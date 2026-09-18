"""The people you split with, and the groups you split with all at once.

Both hold an email rather than a foreign key to users. A request can be sent to
someone who has never signed up, and they should still be in your list while
that is true: the alternative is a picker that can only offer people who already
have an account, which is the opposite of how a flat actually works.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import col, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from budge.auth import CurrentUserId, SessionDep
from budge.db.models import NAME_MAX, TITLE_MAX, Contact, Group, GroupMember

router = APIRouter(prefix="/people", tags=["people"])

NOT_FOUND = 404
MAX_MEMBERS = 30


class Person(BaseModel):
    email: EmailStr
    name: str = Field(default="", max_length=NAME_MAX)


class ContactView(BaseModel):
    id: int
    email: str
    name: str | None
    favourite: bool
    last_asked_at: datetime | None


class GroupView(BaseModel):
    id: int
    name: str
    members: list[Person]


class People(BaseModel):
    """Everything the picker needs, in one call."""

    contacts: list[ContactView]
    groups: list[GroupView]


class NewGroup(BaseModel):
    name: str = Field(max_length=TITLE_MAX)
    members: list[Person] = Field(default_factory=list, max_length=MAX_MEMBERS)


class Favourite(BaseModel):
    favourite: bool


def _view(contact: Contact) -> ContactView:
    return ContactView(
        id=contact.id or 0,
        email=contact.email,
        name=contact.name,
        favourite=contact.favourite,
        last_asked_at=contact.last_asked_at,
    )


async def remember(
    session: AsyncSession, user_id: int, people: list[tuple[str, str | None]]
) -> None:
    """Files everyone you just asked, so the next split is a tap rather than typing.

    Called from the request routes rather than by the browser: a contact list you
    have to curate by hand is a contact list nobody curates.
    """
    now = datetime.now(UTC)
    existing = {
        contact.email: contact
        for contact in await session.exec(
            select(Contact).where(
                Contact.user_id == user_id,
                col(Contact.email).in_([email for email, _ in people]),
            )
        )
    }
    for email, name in people:
        contact = existing.get(email)
        if contact is None:
            contact = Contact(user_id=user_id, email=email, name=name)
        elif name and not contact.name:
            contact.name = name
        contact.last_asked_at = now
        session.add(contact)
    await session.commit()


async def _contacts(session: SessionDep, user_id: int) -> list[ContactView]:
    rows = list(await session.exec(select(Contact).where(Contact.user_id == user_id)))
    # Favourites first, then whoever you asked most recently: the picker should
    # lead with the people you actually split with.
    rows.sort(
        key=lambda c: (
            not c.favourite,
            -(c.last_asked_at or datetime.min.replace(tzinfo=UTC)).timestamp(),
            (c.name or c.email).lower(),
        )
    )
    return [_view(contact) for contact in rows]


async def _groups(session: SessionDep, user_id: int) -> list[GroupView]:
    groups = list(await session.exec(select(Group).where(Group.user_id == user_id)))
    if not groups:
        return []
    members = await session.exec(
        select(GroupMember).where(
            col(GroupMember.group_id).in_([group.id or 0 for group in groups])
        )
    )
    by_group: dict[int, list[Person]] = {group.id or 0: [] for group in groups}
    for member in members:
        by_group[member.group_id].append(
            Person(email=member.email, name=member.name or "")
        )
    return [
        GroupView(
            id=group.id or 0, name=group.name, members=by_group.get(group.id or 0, [])
        )
        for group in groups
    ]


@router.get("")
async def get_people(user_id: CurrentUserId, session: SessionDep) -> People:
    """Contacts and groups together: the picker needs both to draw itself."""
    return People(
        contacts=await _contacts(session, user_id),
        groups=await _groups(session, user_id),
    )


@router.post("/contacts", status_code=201)
async def add_contact(
    body: Person, user_id: CurrentUserId, session: SessionDep
) -> ContactView:
    """Adds someone before you owe them anything. Asking files them anyway."""
    email = str(body.email).lower()
    existing = (
        await session.exec(
            select(Contact).where(Contact.user_id == user_id, Contact.email == email)
        )
    ).first()
    if existing is not None:
        # Already there: name them if they weren't, rather than refuse.
        if body.name.strip() and not existing.name:
            existing.name = body.name.strip()
            session.add(existing)
            await session.commit()
        return _view(existing)

    contact = Contact(user_id=user_id, email=email, name=body.name.strip() or None)
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return _view(contact)


async def _mine(session: SessionDep, user_id: int, contact_id: int) -> Contact:
    contact = await session.get(Contact, contact_id)
    # Someone else's contact is indistinguishable from one that doesn't exist.
    if contact is None or contact.user_id != user_id:
        raise HTTPException(status_code=NOT_FOUND, detail="No such contact")
    return contact


@router.post("/contacts/{contact_id}/favourite")
async def set_favourite(
    contact_id: int, body: Favourite, user_id: CurrentUserId, session: SessionDep
) -> ContactView:
    contact = await _mine(session, user_id, contact_id)
    contact.favourite = body.favourite
    session.add(contact)
    await session.commit()
    return _view(contact)


@router.delete("/contacts/{contact_id}", status_code=204)
async def remove_contact(
    contact_id: int, user_id: CurrentUserId, session: SessionDep
) -> None:
    """Forgets the contact. Requests already sent to them are untouched."""
    await session.delete(await _mine(session, user_id, contact_id))
    await session.commit()


@router.post("/groups", status_code=201)
async def create_group(
    body: NewGroup, user_id: CurrentUserId, session: SessionDep
) -> GroupView:
    group = Group(user_id=user_id, name=body.name.strip() or "Group")
    session.add(group)
    await session.commit()
    await session.refresh(group)
    await _replace_members(session, group.id or 0, body.members)
    return GroupView(
        id=group.id or 0,
        name=group.name,
        members=[Person(email=m.email, name=m.name) for m in body.members],
    )


async def _replace_members(
    session: AsyncSession, group_id: int, members: list[Person]
) -> None:
    await session.exec(delete(GroupMember).where(col(GroupMember.group_id) == group_id))  # type: ignore[call-overload]
    seen: set[str] = set()
    for person in members:
        email = str(person.email).lower()
        # The unique constraint would refuse a repeat; dropping it quietly is
        # kinder than failing a whole group because a name was pasted twice.
        if email in seen:
            continue
        seen.add(email)
        session.add(
            GroupMember(
                group_id=group_id, email=email, name=person.name.strip() or None
            )
        )
    await session.commit()


async def _my_group(session: SessionDep, user_id: int, group_id: int) -> Group:
    group = await session.get(Group, group_id)
    if group is None or group.user_id != user_id:
        raise HTTPException(status_code=NOT_FOUND, detail="No such group")
    return group


@router.put("/groups/{group_id}")
async def update_group(
    group_id: int, body: NewGroup, user_id: CurrentUserId, session: SessionDep
) -> GroupView:
    """Replaces the name and the whole member list, which is how the UI edits it."""
    group = await _my_group(session, user_id, group_id)
    group.name = body.name.strip() or group.name
    session.add(group)
    await session.commit()
    await _replace_members(session, group_id, body.members)
    return GroupView(id=group_id, name=group.name, members=body.members)


@router.delete("/groups/{group_id}", status_code=204)
async def delete_group(
    group_id: int, user_id: CurrentUserId, session: SessionDep
) -> None:
    group = await _my_group(session, user_id, group_id)
    await _replace_members(session, group_id, [])
    await session.delete(group)
    await session.commit()
