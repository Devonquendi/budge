"""Reconciliation and categorisation over a bank feed.

Pure functions over transaction mappings, so both are testable without a bank, a
network or a database. Transactions are dicts here rather than models on purpose:
this layer should not care where the rows came from.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from typing import Any, NamedTuple

Txn = Mapping[str, Any]


# --------------------------------------------------------------- reconciling


def match_credit(credit: Txn, open_requests: Sequence[Txn]) -> Txn | None:
    """Match an incoming credit to exactly one open request, or nothing.

    Amount is the strong signal. The reference deliberately is NOT required —
    paying banks truncate it to twelve characters, drop it, or put it in a
    different field, so a matcher that depends on it fails quietly and often.
    Where the amount is ambiguous the payer's name breaks the tie; where it is
    still ambiguous this returns None and a human decides.

    Guessing wrong here means telling somebody they have paid when they have not,
    which is the worst thing this application could do.
    """
    if credit["amount_cents"] <= 0:
        return None

    same_amount = [
        r for r in open_requests if r["amount_cents"] == credit["amount_cents"]
    ]
    if not same_amount:
        return None
    if len(same_amount) == 1:
        return same_amount[0]

    # Deliberately excludes the counterparty account number: a digit string can
    # only ever produce a false match against a person's name.
    haystack = " ".join(
        str(credit.get(field) or "")
        for field in ("description", "particulars", "reference", "counterparty")
    ).lower()

    def named(request: Txn) -> bool:
        first = str(request["debtor_name"]).strip().split()[0].lower()
        return len(first) >= 3 and first in haystack

    by_name = [r for r in same_amount if named(r)]
    return by_name[0] if len(by_name) == 1 else None


class Reconciliation(NamedTuple):
    matches: list[tuple[Txn, Txn]]  # (credit, request)
    unmatched: list[Txn]


def reconcile(credits: Sequence[Txn], open_requests: Sequence[Txn]) -> Reconciliation:
    """Match every credit to a distinct request, leaving ambiguous ones alone."""
    remaining = list(open_requests)
    matches: list[tuple[Txn, Txn]] = []
    matched_credits: list[int] = []

    for index, credit in enumerate(credits):
        hit = match_credit(credit, remaining)
        if hit is None:
            continue
        matches.append((credit, hit))
        matched_credits.append(index)
        remaining.remove(hit)

    claimed = set(matched_credits)
    return Reconciliation(
        matches=matches,
        unmatched=[c for i, c in enumerate(credits) if i not in claimed],
    )


def _day_number(value: object) -> int:
    """Whole days since the epoch, from a date or an ISO-ish string."""
    if isinstance(value, datetime):
        return value.date().toordinal()
    if isinstance(value, date):
        return value.toordinal()
    return date.fromisoformat(str(value)[:10]).toordinal()


def find_internal_transfers(
    transactions: Sequence[Txn], window_days: int = 3
) -> set[Any]:
    """Ids of transactions that are you moving your own money about.

    With a joint and a personal account connected these can dominate a report —
    the same mistake as counting a flatmate's repayment as income, just bigger. A
    transfer shows up twice: a debit on one account and a matching credit on
    another, within a day or two.

    The pair must sit on DIFFERENT connections, so a genuine payment to somebody
    else can never be mistaken for one.
    """
    credits = [t for t in transactions if t["amount_cents"] > 0]
    claimed: set[Any] = set()
    internal: set[Any] = set()

    for debit in (t for t in transactions if t["amount_cents"] < 0):
        for credit in credits:
            if (
                credit["id"] not in claimed
                and credit["amount_cents"] == -debit["amount_cents"]
                and credit.get("connection_id") != debit.get("connection_id")
                and abs(_day_number(credit["date"]) - _day_number(debit["date"]))
                <= window_days
            ):
                claimed.add(credit["id"])
                internal.add(debit["id"])
                internal.add(credit["id"])
                break

    return internal


# ----------------------------------------------------------------- merchants

STOPWORDS = frozenset({"THE", "LTD", "LIMITED", "NZ", "PTY", "INC", "CO", "AND"})
_NOT_LETTERS = re.compile(r"[^A-Z ]+")


def merchant_key(description: object) -> str | None:
    """A stable key for "the same shop".

    Bank descriptions carry branch codes, card suffixes and reference numbers
    that differ every time — "NEW WORLD DEVONPORT 4205" and "NEW WORLD DEVONPORT"
    are one merchant, and a rule matching the exact string would be useless.

    Strips digits and punctuation, then keeps the first two meaningful words:
    enough to tell New World from New Zealand Post, short enough to survive the
    junk banks append.
    """
    text = _NOT_LETTERS.sub(" ", str(description or "").upper())
    words = [w for w in text.split() if len(w) > 1 and w not in STOPWORDS]

    # Some descriptions repeat the merchant ("TRANSFERWISE ... TRANSFERWISE"),
    # which would otherwise key as "TRANSFERWISE TRANSFERWISE".
    deduped: list[str] = []
    for word in words:
        if not deduped or word != deduped[-1]:
            deduped.append(word)

    unique = list(dict.fromkeys(deduped))
    return " ".join(unique[:2]) or None


def rule_matches(rule: Mapping[str, Any], txn: Txn) -> bool:
    """Does this transaction belong to the merchant a rule is about?"""
    return merchant_key(txn.get("description")) == rule["match"]


class UnlabelledMerchant(NamedTuple):
    key: str
    count: int
    cents: int
    sample: str


def unlabelled_merchants(
    transactions: Iterable[Txn], limit: int = 12
) -> list[UnlabelledMerchant]:
    """Biggest unlabelled merchants first — where labelling buys the most."""
    groups: dict[str, dict[str, Any]] = {}
    for txn in transactions:
        if txn["amount_cents"] >= 0 or txn.get("internal") or txn.get("user_category"):
            continue
        key = merchant_key(txn.get("description"))
        if not key:
            continue
        group = groups.setdefault(
            key,
            {"key": key, "count": 0, "cents": 0, "sample": txn.get("description", "")},
        )
        group["count"] += 1
        group["cents"] += abs(txn["amount_cents"])

    ordered = sorted(groups.values(), key=lambda g: g["cents"], reverse=True)
    return [UnlabelledMerchant(**g) for g in ordered[:limit]]


# ---------------------------------------------------------------- categories
# Ordered: the first rule that hits wins, so the specific ones come first.
#
# Real retailers belong here — this reads a user's own bank feed, and a
# transaction that says COUNTDOWN is groceries whatever we think about it. The
# generic words on each line catch everything the named list misses.

RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"countdown|new world|pak.?n.?save|four square|woolworths|grocer|supermarket|dairy",
            re.IGNORECASE,
        ),
        "Groceries",
    ),
    (
        re.compile(
            r"z energy|bp connect|\bmobil\b|gull|waitomo|fuel|petrol|service station",
            re.IGNORECASE,
        ),
        "Transport",
    ),
    (
        re.compile(
            r"at hop|uber|zoomy|ola |air new zealand|ride|taxi|metro card|bus |rail",
            re.IGNORECASE,
        ),
        "Transport",
    ),
    (
        re.compile(
            r"spark|one nz|vodafone|2degrees|contact energy|mercury|genesis|electric kiwi|energy|power|mobile|broadband",
            re.IGNORECASE,
        ),
        "Utilities",
    ),
    (
        re.compile(
            r"netflix|spotify|disney|neon|prime video|patreon|\btv\b|streaming|music",
            re.IGNORECASE,
        ),
        "Subscriptions",
    ),
    (
        re.compile(
            r"bunnings|mitre 10|kmart|briscoes|the warehouse|hardware|toolshed|warehouse|bargain",
            re.IGNORECASE,
        ),
        "Home & shopping",
    ),
    (
        re.compile(
            r"chemist|unichem|life pharmacy|doctor|medical|dental|pharmacy",
            re.IGNORECASE,
        ),
        "Health",
    ),
    (
        re.compile(
            r"cafe|espresso|coffee|restaurant|bar |eatery|pizza|sushi|flat white|grill|brewery|\bpub\b|the anchor",
            re.IGNORECASE,
        ),
        "Eating out",
    ),
    (re.compile(r"\brent\b|tenancy|property manage", re.IGNORECASE), "Rent"),
    (re.compile(r"ird|inland revenue", re.IGNORECASE), "Tax"),
]

UNCATEGORISED = "Uncategorised"
INCOME = "Income"


def categorise(txn: Txn) -> str:
    """Best guess at what a transaction was for."""
    # Trust the provider's own enrichment over our patterns when it is there.
    if txn.get("provider_category"):
        return str(txn["provider_category"])
    if txn["amount_cents"] > 0:
        return INCOME

    text = " ".join(
        str(txn.get(f) or "") for f in ("description", "particulars", "reference")
    )
    for pattern, category in RULES:
        if pattern.search(text):
            return category
    return UNCATEGORISED


# ------------------------------------------------------------------ reports


class CategoryTotal(NamedTuple):
    category: str
    cents: int
    share: float


class Spending(NamedTuple):
    total: int
    categories: list[CategoryTotal]


def spending_by_category(transactions: Iterable[Txn]) -> Spending:
    """Spending by category, excluding income and money already accounted for.

    Anything matched to a request is left out — a flatmate paying you back is not
    income, and counting it as such is the classic way these reports lie.
    """
    totals: dict[str, int] = {}
    total = 0
    for txn in transactions:
        if (
            txn["amount_cents"] >= 0
            or txn.get("matched_request_id")
            or txn.get("internal")
        ):
            continue
        category = txn.get("category") or categorise(txn)
        spent = abs(txn["amount_cents"])
        totals[category] = totals.get(category, 0) + spent
        total += spent

    categories = [
        CategoryTotal(category=c, cents=cents, share=(cents / total if total else 0.0))
        for c, cents in totals.items()
    ]
    categories.sort(key=lambda c: c.cents, reverse=True)
    return Spending(total=total, categories=categories)


class Cashflow(NamedTuple):
    inbound: int
    outbound: int
    net: int


def cashflow(transactions: Iterable[Txn]) -> Cashflow:
    """Money in, money out, and what it nets to."""
    inbound = outbound = 0
    for txn in transactions:
        if txn.get("internal"):
            continue  # shuffling your own money about is not cashflow
        if txn["amount_cents"] >= 0:
            inbound += txn["amount_cents"]
        else:
            outbound += abs(txn["amount_cents"])
    return Cashflow(inbound=inbound, outbound=outbound, net=inbound - outbound)


# Deductible-looking spend, for somebody doing their own books. Explicitly a
# suggestion and not advice — these are patterns, not tax law, and the interface
# has to say so wherever this is shown.
BUSINESSY = re.compile(
    r"bunnings|mitre 10|officemax|warehouse stationery|xero|adobe|figma"
    r"|github|aws|google cloud|canva|zoom",
    re.IGNORECASE,
)


def possible_business_expenses(transactions: Iterable[Txn]) -> list[Txn]:
    """Spending that looks like it might be deductible. A prompt, not an answer."""
    return [
        t
        for t in transactions
        if t["amount_cents"] < 0
        and not t.get("internal")
        and BUSINESSY.search(
            " ".join(str(t.get(f) or "") for f in ("description", "particulars"))
        )
    ]
