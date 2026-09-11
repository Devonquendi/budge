"""Turn Akahu's raw JSON into thrifty's domain models."""

from thrifty.akahu.models import Account


def to_account(data: dict) -> Account:
    """Build an Account from one item of GET /accounts."""
    balance = data["balance"]
    return Account(
        id=data["_id"],
        name=data["name"],
        type=data["type"],
        connection_name=data["connection"]["name"],
        formatted_account=data.get("formatted_account"),
        currency=balance["currency"],
        balance_current=balance["current"],
        balance_available=balance.get("available"),
    )
