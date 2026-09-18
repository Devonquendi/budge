"""An invented bank feed for the invented people.

Every account, merchant and bank here is made up. Nothing in this module talks
to Akahu, and it is the only way a demo persona ever has transactions: previews
cannot reach a real bank at all (see environment.akahu_enabled), and a persona
has no Akahu tokens to reach one with.

The feed is generated rather than listed so it stays current: it is always the
last few months up to today, so the dashboard's "this month" is never empty.
Seeded off the persona's email, so the same person has the same history every
time rather than a new past on every page load.
"""

import hashlib
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from budge.akahu.models import Account, Category, Merchant, Transaction

DAYS = 120
CURRENCY = "NZD"

# Two invented banks, so an account list has more than one mark in it.
BANKS = [
    ("conn_demo_kowhai", "Kowhai Bank", "Everyday", "0.00"),
    ("conn_demo_harbourline", "Harbourline Savings", "Savings", "0.00"),
]


class Spend:
    """One recurring line in someone's month."""

    def __init__(
        self,
        merchant: str,
        category: str,
        group: str,
        low: int,
        high: int,
        every: int,
    ) -> None:
        self.merchant = merchant
        self.category = category
        self.group = group
        self.low = low
        self.high = high
        # Roughly every N days. Jittered, because nobody buys milk on a timer.
        self.every = every


# Invented merchants, all of them. Categories are Akahu's NZFCC names, which is
# what the browser colours and groups on.
PATTERN = [
    Spend("Fern & Fig Grocers", "Groceries", "Household", 4200, 11800, 6),
    Spend("Pipipi Coffee", "Cafes & restaurants", "Lifestyle", 450, 1900, 3),
    Spend("Kauri Fuel", "Fuel", "Transport", 5500, 9800, 11),
    Spend("Reka Thai Kitchen", "Takeaway", "Lifestyle", 1800, 4600, 14),
    Spend("Moa Mobile", "Phone & internet", "Utilities", 2500, 2500, 30),
    Spend("Tussock Power", "Power", "Utilities", 11200, 21400, 30),
    Spend("Longspan Internet", "Phone & internet", "Utilities", 8999, 8999, 30),
    Spend("Riverbend Pharmacy", "Health", "Health", 1200, 4800, 26),
    Spend("Halswell Hardware", "Household", "Household", 1500, 8900, 21),
    Spend("Southerly Outdoors", "Clothing", "Lifestyle", 3900, 14500, 34),
]

RENT_CENTS = 26_000
SALARY_LOW = 142_000
SALARY_HIGH = 168_000


def _seeded(email: str) -> random.Random:
    """Same person, same history. A plain hash of the email is enough."""
    digest = hashlib.sha256(email.lower().encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _slug(email: str) -> str:
    return email.split("@")[0].lower()


def accounts_for(email: str) -> list[Account]:
    """Two accounts at two different invented banks."""
    rng = _seeded(email)
    slug = _slug(email)
    everyday = Decimal(rng.randrange(18_000, 420_000)) / 100
    savings = Decimal(rng.randrange(150_000, 1_800_000)) / 100
    balances = [everyday, savings]

    return [
        Account(
            id=f"acc_demo_{slug}_{name.lower()}",
            name=f"{name} account",
            type="CHECKING" if name == "Everyday" else "SAVINGS",
            connection_name=bank,
            connection_logo=None,
            formatted_account=f"12-{3400 + index:04d}-{rng.randrange(1_000_000, 9_999_999)}-00",
            currency=CURRENCY,
            balance_current=balance,
            balance_available=balance,
        )
        for index, ((_, bank, name, _), balance) in enumerate(
            zip(BANKS, balances, strict=True)
        )
    ]


def _transaction(
    index: int,
    account: Account,
    connection_id: str,
    when: datetime,
    description: str,
    cents: int,
    category: str | None = None,
    group: str | None = None,
    merchant: str | None = None,
    kind: str = "DEBIT",
) -> Transaction:
    return Transaction(
        id=f"txn_demo_{account.id}_{index}",
        account_id=account.id,
        account_name=account.display_name,
        currency=account.currency,
        connection_id=connection_id,
        date=when,
        description=description,
        # Akahu's sign convention: negative is money out.
        amount=Decimal(cents) / 100,
        type=kind,
        merchant=Merchant(name=merchant) if merchant else None,
        category=(
            Category(name=category, group=group, source="akahu", confidence=1.0)
            if category
            else None
        ),
    )


def transactions_for(
    email: str, accounts: list[Account], start: datetime, end: datetime
) -> list[Transaction]:
    """A plausible few months, newest first, clipped to the window asked for."""
    rng = _seeded(email)
    everyday, savings = accounts[0], accounts[1]
    everyday_connection = BANKS[0][0]
    savings_connection = BANKS[1][0]
    today = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    out: list[Transaction] = []

    def add(
        account: Account,
        connection: str,
        when: datetime,
        description: str,
        cents: int,
        category: str | None = None,
        group: str | None = None,
        merchant: str | None = None,
        kind: str = "DEBIT",
    ) -> None:
        out.append(
            _transaction(
                len(out) + 1,
                account,
                connection,
                when,
                description,
                cents,
                category,
                group,
                merchant,
                kind,
            )
        )

    for spend in PATTERN:
        day = rng.randrange(spend.every)
        while day < DAYS:
            when = today - timedelta(days=day, hours=rng.randrange(10))
            add(
                everyday,
                everyday_connection,
                when,
                spend.merchant.upper(),
                -rng.randrange(spend.low, spend.high + 1),
                spend.category,
                spend.group,
                spend.merchant,
            )
            # Jitter, so two people's feeds don't line up day for day.
            day += max(1, spend.every + rng.randrange(-2, 3))

    # Fortnightly pay, weekly rent, and a standing transfer to savings: the
    # three things that shape a month more than any of the spending above.
    for day in range(rng.randrange(14), DAYS, 14):
        when = today - timedelta(days=day)
        add(
            everyday,
            everyday_connection,
            when,
            "SALARY",
            rng.randrange(SALARY_LOW, SALARY_HIGH),
            "Salary & wages",
            "Income",
            kind="CREDIT",
        )

    for day in range(rng.randrange(7), DAYS, 7):
        when = today - timedelta(days=day, hours=2)
        add(
            everyday,
            everyday_connection,
            when,
            "RENT PAYMENT",
            -RENT_CENTS,
            "Rent",
            "Housing",
        )

    # The same money leaving one account and landing in the other on the same
    # day: what charges.feed.find_internal_transfers exists to spot. The
    # dashboard counts the outgoing leg as spending today, which is the gap
    # that function closes, and leaving it visible here is the point.
    for day in range(rng.randrange(28), DAYS, 28):
        when = today - timedelta(days=day, hours=1)
        amount = rng.randrange(15_000, 60_000)
        add(
            everyday,
            everyday_connection,
            when,
            "TRANSFER TO SAVINGS",
            -amount,
            "Transfers",
            "Transfer",
            kind="TRANSFER",
        )
        add(
            savings,
            savings_connection,
            when,
            "TRANSFER FROM EVERYDAY",
            amount,
            "Transfers",
            "Transfer",
            kind="TRANSFER",
        )

    keep = [t for t in out if start <= t.date <= end]
    keep.sort(key=lambda transaction: transaction.date, reverse=True)
    return keep


class FixtureClient:
    """Stands in for AkahuClient, with the same two methods and no network.

    Deliberately not a subclass: sharing a base with the real client is how a
    demo session ends up one missing override away from a real HTTP call.
    """

    def __init__(self, email: str) -> None:
        self._email = email

    async def get_accounts(self) -> list[Account]:
        return accounts_for(self._email)

    async def get_transactions(
        self, accounts: list[Account], start: datetime, end: datetime
    ) -> list[Transaction]:
        wanted = {account.id for account in accounts}
        every = transactions_for(self._email, accounts_for(self._email), start, end)
        return [
            transaction for transaction in every if transaction.account_id in wanted
        ]
