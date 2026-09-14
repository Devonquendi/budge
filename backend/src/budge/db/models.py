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
