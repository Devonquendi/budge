"""SQLModel tables for user accounts and their Akahu configuration."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
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
