"""Ported from the JavaScript implementation's scripts/test-logic.mjs."""

from budge.charges.ledger import (
    TOKEN_ALPHABET,
    Tally,
    derive_state,
    make_token,
    tally_bill,
)


def events(*types):
    return [{"type": t} for t in types]


# --- state -------------------------------------------------------------------


def test_new_requests_start_open():
    assert derive_state(events("created")) == "open"


def test_debtor_can_claim_paid():
    assert derive_state(events("created", "marked_paid")) == "marked_paid"


def test_creator_confirmation_is_final_over_later_claims():
    log = events("created", "marked_paid", "confirmed", "marked_paid")
    assert derive_state(log) == "confirmed"


def test_creator_can_cancel_a_confirmed_request():
    assert derive_state(events("created", "confirmed", "cancelled")) == "cancelled"


def test_reopening_returns_a_request_to_open():
    log = events("created", "marked_paid", "confirmed", "reopened")
    assert derive_state(log) == "open"


def test_a_claim_after_reopening_still_works():
    log = events("created", "confirmed", "reopened", "marked_paid")
    assert derive_state(log) == "marked_paid"


# --- declining ---------------------------------------------------------------


def test_a_payer_can_decline_an_open_request():
    assert derive_state(events("created", "declined")) == "declined"


def test_declining_overrides_the_payers_own_earlier_claim():
    assert derive_state(events("created", "marked_paid", "declined")) == "declined"


def test_declining_cannot_undo_a_confirmation():
    assert derive_state(events("created", "confirmed", "declined")) == "confirmed"


def test_the_requester_can_reopen_a_declined_request():
    assert derive_state(events("created", "declined", "reopened")) == "open"


# --- tallies -----------------------------------------------------------------


def test_tally_separates_owed_claimed_and_settled():
    assert tally_bill(
        [
            {"amount_cents": 1000, "state": "open"},
            {"amount_cents": 2000, "state": "marked_paid"},
            {"amount_cents": 3000, "state": "confirmed"},
            {"amount_cents": 9999, "state": "cancelled"},
        ]
    ) == Tally(owed=1000, claimed=2000, settled=3000, outstanding=3000)


def test_an_empty_bill_tallies_to_nothing():
    assert tally_bill([]) == Tally(0, 0, 0, 0)


# --- tokens ------------------------------------------------------------------


def test_tokens_are_the_right_shape():
    token = make_token()
    assert len(token) == 12
    assert set(token) <= set(TOKEN_ALPHABET)


def test_the_alphabet_is_unambiguous_and_exactly_32():
    # 32 so the mapping is honest, and without i/l/o so nothing reads as 1 or 0.
    assert len(TOKEN_ALPHABET) == 32
    assert len(set(TOKEN_ALPHABET)) == 32
    assert not set("ilo") & set(TOKEN_ALPHABET)


def test_tokens_do_not_repeat():
    assert len({make_token() for _ in range(2000)}) == 2000
