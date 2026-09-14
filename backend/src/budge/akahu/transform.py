"""Turn Akahu's raw JSON into budge's domain models."""

from budge.akahu.models import Account, Category, Merchant, Transaction

# The NZFCC grouping worth showing a human. Akahu sends several mappings under
# `groups`; the others are for apps that have their own taxonomy.
PERSONAL_FINANCE = "personal_finance"


def to_account(data: dict) -> Account:
    """Build an Account from one item of GET /accounts."""
    balance = data["balance"]
    connection = data["connection"]
    return Account(
        id=data["_id"],
        name=data["name"],
        type=data["type"],
        connection_id=connection["_id"],
        connection_name=connection["name"],
        connection_logo=connection.get("logo"),
        formatted_account=data.get("formatted_account"),
        currency=balance["currency"],
        balance_current=balance["current"],
        balance_available=balance.get("available"),
    )


def to_category(
    data: dict | None, source: str, confidence: float | None = None
) -> Category | None:
    """Akahu and Genie describe a category identically, so one reader does both."""
    if not data:
        return None
    group = (data.get("groups") or {}).get(PERSONAL_FINANCE) or {}
    return Category(
        id=data.get("_id"),
        name=data["name"],
        group=group.get("name"),
        source=source,
        confidence=confidence,
    )


def to_merchant(data: dict | None) -> Merchant | None:
    if not data:
        return None
    return Merchant(
        id=data.get("_id"),
        name=data["name"],
        logo=data.get("logo"),
        website=data.get("website"),
    )


def to_transaction(data: dict, account_name: str, currency: str) -> Transaction:
    """Build a Transaction from one item of GET /transactions.

    Enrichment is optional: which apps get `merchant` and `category` inline is
    up to Akahu, and a transaction that arrives bare is the normal case Genie
    exists to fill in.
    """
    meta = data.get("meta") or {}
    merchant = to_merchant(data.get("merchant"))
    # Some connections send a merchant name in `meta` without a merchant
    # record. It's still a better label than the raw description.
    if merchant is None and meta.get("merchant_name"):
        merchant = Merchant(name=meta["merchant_name"])
    # Akahu hangs the merchant's logo off `meta` rather than the merchant
    # record, so it has to be carried across by hand.
    if merchant is not None and merchant.logo is None:
        merchant.logo = meta.get("logo")

    return Transaction(
        id=data["_id"],
        account_id=data["_account"],
        account_name=account_name,
        currency=currency,
        connection_id=data["_connection"],
        date=data["date"],
        description=data["description"],
        amount=data["amount"],
        type=data.get("type", "UNKNOWN"),
        merchant=merchant,
        category=to_category(data.get("category"), source="akahu"),
    )
