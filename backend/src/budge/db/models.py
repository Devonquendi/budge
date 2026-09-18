"""SQLModel tables for user accounts and their Akahu configuration."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint

# Long enough for "Joint everyday account", short enough to stay on one line
# wherever an account is listed.
NICKNAME_MAX = 40

# A display name, not a legal one: long enough for anything someone answers
# "what should we call you" with.
NAME_MAX = 60


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    # What the user asked to be called. Null until they say.
    name: str | None = Field(default=None, max_length=NAME_MAX)
    # Where money should actually go, normalised to bank-branch-account-suffix.
    # Null until they say, and a request without one can only be claimed paid
    # rather than paid.
    payout_account: str | None = Field(default=None)
    # The name on that account, which Confirmation of Payee checks against.
    payout_name: str | None = Field(default=None, max_length=NAME_MAX)
    # When it was last seen among their connected accounts. Null means it was
    # never checked; a stale one means it may have been disconnected since.
    payout_verified_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AkahuCredential(SQLModel, table=True):
    __tablename__ = "akahu_credentials"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    app_token_encrypted: str
    user_token_encrypted: str


class AkahuAccountSetting(SQLModel, table=True):
    __tablename__ = "akahu_account_settings"
    __table_args__ = (UniqueConstraint("user_id", "akahu_account_id"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    akahu_account_id: str
    included_in_dashboard: bool = Field(default=True)
    # What the user calls this account. Null means Akahu's own name stands.
    nickname: str | None = Field(default=None, max_length=NICKNAME_MAX)


# What the bill is for, as the payer will read it on the request.
TITLE_MAX = 80

# Free text on an event: "paid it this morning", "I paid you in cash".
NOTE_MAX = 200


class Bill(SQLModel, table=True):
    """One thing that was paid for, and is being split."""

    __tablename__ = "bills"

    id: int | None = Field(default=None, primary_key=True)
    creator_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=TITLE_MAX)
    total_cents: int
    # The transaction this was split from, when it came from the feed rather
    # than a typed-in amount. Akahu's id, not ours.
    source_transaction_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChargeRequest(SQLModel, table=True):
    """One person's share of a bill, and the link that addresses it."""

    __tablename__ = "charge_requests"

    id: int | None = Field(default=None, primary_key=True)
    bill_id: int = Field(foreign_key="bills.id", index=True)
    # The whole address of a request: anyone holding it can open the page and
    # pay, which is the point. Unguessable rather than secret.
    token: str = Field(unique=True, index=True)
    payee_email: str = Field(index=True)
    payee_name: str | None = Field(default=None, max_length=NAME_MAX)
    amount_cents: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RequestEvent(SQLModel, table=True):
    """Append-only: every state a request has ever been in is still here.

    Nothing updates a row in this table and nothing stores the current state.
    `charges.ledger.derive_state` folds these into it on read, so a balance can
    always be re-explained from what happened rather than trusted from a column.
    """

    __tablename__ = "request_events"

    id: int | None = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="charge_requests.id", index=True)
    type: str
    # "creator" or "payee". Who acted decides whose claim this is, and the
    # creator's word wins: see CREATOR_ACTIONS.
    actor: str
    note: str | None = Field(default=None, max_length=NOTE_MAX)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Contact(SQLModel, table=True):
    """Someone you have asked for money, or expect to.

    Held by email rather than by a foreign key to users: the whole point of a
    request is that it can be sent to somebody who has not signed up, and they
    should still be in your list while that is true.
    """

    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("user_id", "email"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    email: str
    name: str | None = Field(default=None, max_length=NAME_MAX)
    # Favourites lead the picker. Everything else is ordered by recency.
    favourite: bool = Field(default=False)
    # Bumped every time they are asked for something, so the picker can put the
    # people you actually split with first without you curating anything.
    last_asked_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Group(SQLModel, table=True):
    """A flat, a trip, a household: people who get asked together."""

    __tablename__ = "groups"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=TITLE_MAX)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GroupMember(SQLModel, table=True):
    """One person in a group, by email for the same reason contacts are."""

    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "email"),)

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id", index=True)
    email: str
    name: str | None = Field(default=None, max_length=NAME_MAX)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MatchSuggestion(SQLModel, table=True):
    """A credit that looks like it settles an open request.

    Never applied on its own. Telling somebody they have been paid when they
    have not is the worst thing this application could do, so a match is a
    question put to the person owed, and their answer is what moves the request.
    """

    __tablename__ = "match_suggestions"
    __table_args__ = (UniqueConstraint("request_id", "transaction_id"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    request_id: int = Field(foreign_key="charge_requests.id", index=True)
    # Akahu's id for the credit. Not a foreign key: transactions are read from
    # the bank on demand and never stored.
    transaction_id: str
    amount_cents: int
    description: str
    occurred_at: datetime
    # "pending", "accepted" or "dismissed". A dismissed one is remembered so the
    # same credit is not offered again every time the feed is read.
    state: str = Field(default="pending")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
