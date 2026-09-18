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
