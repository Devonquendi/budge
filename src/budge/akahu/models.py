"""Domain models for Akahu data."""

from pydantic import BaseModel


class Account(BaseModel):
    id: str
    name: str
    type: str
    connection_name: str
    formatted_account: str | None = None
    currency: str
    balance_current: float
    balance_available: float | None = None
