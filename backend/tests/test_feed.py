"""Ported from the JavaScript implementation's scripts/test-money.mjs.

Field names are snake_case here where the JavaScript used camelCase, matching
both Python convention and the database columns.
"""

from budge.charges.feed import (
    cashflow,
    categorise,
    find_internal_transfers,
    match_credit,
    merchant_key,
    possible_business_expenses,
    reconcile,
    rule_matches,
    spending_by_category,
    unlabelled_merchants,
)


def credit(cents, **extra):
    return {
        "id": extra.pop("id", "c1"),
        "amount_cents": cents,
        "date": "2026-09-01",
        **extra,
    }


def request(cents, name="Jess Lin", **extra):
    return {
        "id": extra.pop("id", "r1"),
        "amount_cents": cents,
        "debtor_name": name,
        **extra,
    }


# --- matching ----------------------------------------------------------------


def test_a_lone_amount_match_is_enough():
    reqs = [request(4500), request(9900, "Marcus Reed", id="r2")]
    hit = match_credit(credit(4500), reqs)
    assert hit is not None
    assert hit["id"] == "r1"


def test_no_match_when_nothing_has_that_amount():
    assert match_credit(credit(1234), [request(4500)]) is None


def test_debits_never_match():
    assert match_credit(credit(-4500), [request(4500)]) is None


def test_the_payers_name_breaks_an_amount_tie():
    reqs = [request(4500, "Jess Lin", id="r1"), request(4500, "Marcus Reed", id="r2")]
    hit = match_credit(credit(4500, description="TFR FROM MARCUS REED"), reqs)
    assert hit is not None
    assert hit["id"] == "r2"


def test_an_unbroken_tie_matches_nothing():
    reqs = [request(4500, "Jess Lin", id="r1"), request(4500, "Marcus Reed", id="r2")]
    assert match_credit(credit(4500, description="INTERNET BANKING"), reqs) is None


def test_a_reference_is_never_required():
    # Banks truncate and drop these, so depending on one fails quietly.
    assert match_credit(credit(4500), [request(4500)]) is not None


def test_very_short_first_names_do_not_break_ties():
    reqs = [request(4500, "Jo Smith", id="r1"), request(4500, "Al Brown", id="r2")]
    assert match_credit(credit(4500, description="PAYMENT FROM JO"), reqs) is None


def test_reconcile_never_uses_one_request_twice():
    reqs = [request(4500, id="r1"), request(4500, "Marcus Reed", id="r2")]
    result = reconcile(
        [
            credit(4500, id="c1", description="FROM JESS LIN"),
            credit(4500, id="c2", description="FROM MARCUS REED"),
        ],
        reqs,
    )
    assert {m[1]["id"] for m in result.matches} == {"r1", "r2"}
    assert result.unmatched == []


def test_reconcile_reports_what_it_could_not_place():
    result = reconcile([credit(111, id="c9")], [request(4500)])
    assert result.matches == []
    assert [c["id"] for c in result.unmatched] == ["c9"]


# --- internal transfers ------------------------------------------------------


def test_a_transfer_between_your_own_accounts_is_found():
    txns = [
        {"id": "d", "amount_cents": -20000, "date": "2026-09-01", "connection_id": "a"},
        {"id": "c", "amount_cents": 20000, "date": "2026-09-02", "connection_id": "b"},
    ]
    assert find_internal_transfers(txns) == {"d", "c"}


def test_a_payment_to_someone_else_is_not_a_transfer():
    # Same connection, so it cannot be a move between two of your accounts.
    txns = [
        {"id": "d", "amount_cents": -20000, "date": "2026-09-01", "connection_id": "a"},
        {"id": "c", "amount_cents": 20000, "date": "2026-09-02", "connection_id": "a"},
    ]
    assert find_internal_transfers(txns) == set()


def test_transfers_too_far_apart_are_not_paired():
    txns = [
        {"id": "d", "amount_cents": -20000, "date": "2026-09-01", "connection_id": "a"},
        {"id": "c", "amount_cents": 20000, "date": "2026-09-20", "connection_id": "b"},
    ]
    assert find_internal_transfers(txns) == set()


# --- merchants ---------------------------------------------------------------


def test_the_same_shop_keys_the_same_way():
    assert merchant_key("NEW WORLD DEVONPORT 4205") == merchant_key(
        "NEW WORLD DEVONPORT"
    )


def test_different_shops_key_differently():
    assert merchant_key("Z ENERGY") != merchant_key("SPARK NZ")


def test_a_repeated_merchant_is_not_doubled():
    assert merchant_key("TRANSFERWISE LTD TRANSFERWISE") == "TRANSFERWISE"


def test_junk_keys_to_nothing():
    for junk in ("", "1234 5678", None):
        assert merchant_key(junk) is None


def test_a_rule_matches_its_merchant():
    rule = {"match": merchant_key("NEW WORLD DEVONPORT")}
    assert rule_matches(rule, {"description": "NEW WORLD DEVONPORT 9911"})
    assert not rule_matches(rule, {"description": "COUNTDOWN PONSONBY"})


def test_unlabelled_merchants_are_ranked_by_money_not_count():
    txns = [
        {"amount_cents": -1000, "description": "CORNER DAIRY METRO"},
        {"amount_cents": -1000, "description": "CORNER DAIRY METRO"},
        {"amount_cents": -9000, "description": "TOOLSHED WAREHOUSE"},
    ]
    top = unlabelled_merchants(txns)
    assert top[0].key == merchant_key("TOOLSHED WAREHOUSE")
    assert top[0].cents == 9000
    assert top[1].count == 2


def test_already_labelled_spending_is_left_out():
    txns = [
        {
            "amount_cents": -1000,
            "description": "CORNER DAIRY",
            "user_category": "Groceries",
        }
    ]
    assert unlabelled_merchants(txns) == []


# --- categories --------------------------------------------------------------


def test_money_coming_in_is_income():
    assert categorise({"amount_cents": 200000, "description": "SALARY"}) == "Income"


def test_the_providers_own_category_wins():
    txn = {
        "amount_cents": -1000,
        "description": "COUNTDOWN",
        "provider_category": "Whatever",
    }
    assert categorise(txn) == "Whatever"


def test_real_nz_merchants_categorise():
    for description, expected in [
        ("COUNTDOWN PONSONBY", "Groceries"),
        ("MERCURY ENERGY", "Utilities"),
        ("MOBIL TAKAPUNA", "Transport"),
        ("SPARK NZ MONTHLY", "Utilities"),
        ("NETFLIX.COM", "Subscriptions"),
    ]:
        assert (
            categorise({"amount_cents": -1000, "description": description}) == expected
        )


def test_mobil_the_petrol_station_is_not_a_mobile_plan():
    # The word boundary matters: without it every phone bill files as Transport.
    assert (
        categorise({"amount_cents": -1000, "description": "MOBIL TAKAPUNA"})
        == "Transport"
    )
    assert (
        categorise({"amount_cents": -1000, "description": "SOUTHERLY MOBILE"})
        == "Utilities"
    )


def test_invented_demo_merchants_all_categorise():
    for description in (
        "FRESH VALLEY SUPERMARKET",
        "HARBOURSIDE GROCER",
        "KAHU FUEL TAKAPUNA",
        "METRO CARD TOP UP",
        "SOUTHERLY MOBILE",
        "TUSSOCK ENERGY",
        "FLAT WHITE CO",
        "GRILL HOUSE TAKAPUNA",
        "BARGAIN BARN",
        "TOOLSHED WAREHOUSE",
        "STREAMLINE TV",
        "TUNEBOX MUSIC",
        "DEVONPORT PHARMACY",
        "THE ANCHOR DEVONPORT",
        "CORNER DAIRY METRO",
        "ZIP RIDE",
    ):
        assert (
            categorise({"amount_cents": -1000, "description": description})
            != "Uncategorised"
        ), description


def test_unknown_spending_stays_uncategorised():
    assert (
        categorise({"amount_cents": -1000, "description": "QQQ ZZZ"}) == "Uncategorised"
    )


# --- reports -----------------------------------------------------------------


def test_spending_excludes_income_transfers_and_repayments():
    txns = [
        {"amount_cents": -1000, "description": "COUNTDOWN"},
        {"amount_cents": 200000, "description": "SALARY"},
        {"amount_cents": -5000, "description": "TFR", "internal": True},
        {"amount_cents": -4500, "description": "X", "matched_request_id": "r1"},
    ]
    spending = spending_by_category(txns)
    assert spending.total == 1000
    assert [c.category for c in spending.categories] == ["Groceries"]
    assert spending.categories[0].share == 1.0


def test_cashflow_ignores_your_own_transfers():
    txns = [
        {"amount_cents": 200000},
        {"amount_cents": -5000},
        {"amount_cents": -100000, "internal": True},
    ]
    assert cashflow(txns) == (200000, 5000, 195000)


def test_business_expenses_are_a_suggestion_not_an_answer():
    txns = [
        {"amount_cents": -5000, "description": "BUNNINGS WAREHOUSE"},
        {"amount_cents": -900, "description": "FLAT WHITE CO"},
        {"amount_cents": -2000, "description": "XERO", "internal": True},
    ]
    found = possible_business_expenses(txns)
    assert [t["description"] for t in found] == ["BUNNINGS WAREHOUSE"]
