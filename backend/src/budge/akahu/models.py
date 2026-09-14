"""Domain models for Akahu data."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Account(BaseModel):
    id: str
    name: str
    type: str
    connection_name: str
    # Akahu hosts a logo per provider, which is what puts a bank's mark beside
    # its accounts instead of our own initials.
    connection_logo: str | None = None
    formatted_account: str | None = None
    currency: str
    # Money is Decimal end to end: floats don't add up to totals that reconcile.
    # Pydantic serialises these as JSON strings, so the browser gets the exact
    # digits Akahu sent and decides for itself how to add them up.
    balance_current: Decimal
    balance_available: Decimal | None = None
    # What the user renamed this account to, which is ours rather than Akahu's.
    nickname: str | None = None

    @property
    def display_name(self) -> str:
        return self.nickname or self.name


class Category(BaseModel):
    """What a transaction was spent on, however we worked that out."""

    name: str
    # Akahu's NZFCC id, absent when Genie matched on name alone.
    id: str | None = None
    # The broad "personal finance" grouping NZFCC rolls up into: "Lifestyle",
    # "Household", and so on. Coarse enough to chart, unlike the ~200 NZFCCs.
    group: str | None = None
    # "akahu" when it arrived on the transaction, "genie" when we asked Genie.
    # The page shows the split, which is the only way to tell whether Genie is
    # earning its keep.
    source: str
    confidence: float | None = None


class Merchant(BaseModel):
    name: str
    id: str | None = None
    logo: str | None = None
    website: str | None = None


class Transaction(BaseModel):
    id: str
    account_id: str
    # Resolved from the account, because Akahu hangs currency off the account
    # rather than repeating it on every transaction.
    account_name: str
    currency: str
    connection_id: str
    date: datetime
    description: str
    # Akahu's sign convention: negative is money out, positive is money in.
    amount: Decimal
    type: str
    merchant: Merchant | None = None
    category: Category | None = None
