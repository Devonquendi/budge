"""Contacts and groups: what makes splitting a tap rather than typing."""

from httpx import AsyncClient

from .conftest import INVITE_CODE

INVITE = {"invite_code": INVITE_CODE}


async def sign_up(client: AsyncClient, email: str = "ara@example.com") -> None:
    response = await client.post(
        "/api/auth/signup", json={"email": email, "password": "hunter2hunter2"} | INVITE
    )
    assert response.status_code == 201, response.text


async def split(client: AsyncClient, *emails: str) -> None:
    response = await client.post(
        "/api/requests",
        json={
            "title": "Power, August",
            "amount": "60",
            "payees": [{"email": email} for email in emails],
        },
    )
    assert response.status_code == 201, response.text


async def test_asking_someone_files_them(client: AsyncClient) -> None:
    """The whole point: nobody curates a contact list by hand."""
    await sign_up(client)
    await split(client, "neve@example.com", "tipene@example.com")

    people = (await client.get("/api/people")).json()
    assert {c["email"] for c in people["contacts"]} == {
        "neve@example.com",
        "tipene@example.com",
    }
    assert all(c["last_asked_at"] for c in people["contacts"])


async def test_asking_the_same_person_twice_files_them_once(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    await split(client, "neve@example.com")
    await split(client, "neve@example.com")

    contacts = (await client.get("/api/people")).json()["contacts"]
    assert len(contacts) == 1


async def test_favourites_lead_the_list(client: AsyncClient) -> None:
    await sign_up(client)
    await split(client, "neve@example.com", "tipene@example.com", "dev@example.com")

    contacts = (await client.get("/api/people")).json()["contacts"]
    last = next(c for c in contacts if c["email"] == "dev@example.com")
    await client.post(
        f"/api/people/contacts/{last['id']}/favourite", json={"favourite": True}
    )

    after = (await client.get("/api/people")).json()["contacts"]
    assert after[0]["email"] == "dev@example.com"
    assert after[0]["favourite"] is True


async def test_someone_can_be_added_before_they_owe_anything(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    created = await client.post(
        "/api/people/contacts", json={"email": "Marguerite@example.com", "name": "Marg"}
    )

    assert created.status_code == 201, created.text
    # Lowercased, so it matches what a request stores.
    assert created.json()["email"] == "marguerite@example.com"
    assert created.json()["last_asked_at"] is None


async def test_adding_the_same_contact_twice_names_them(client: AsyncClient) -> None:
    await sign_up(client)
    await client.post("/api/people/contacts", json={"email": "neve@example.com"})
    second = await client.post(
        "/api/people/contacts", json={"email": "neve@example.com", "name": "Neve"}
    )

    assert second.json()["name"] == "Neve"
    assert len((await client.get("/api/people")).json()["contacts"]) == 1


async def test_a_contact_can_be_forgotten(client: AsyncClient) -> None:
    await sign_up(client)
    await split(client, "neve@example.com")
    contact = (await client.get("/api/people")).json()["contacts"][0]

    assert (
        await client.delete(f"/api/people/contacts/{contact['id']}")
    ).status_code == 204
    assert (await client.get("/api/people")).json()["contacts"] == []


async def test_nobody_touches_someone_elses_contacts(client: AsyncClient) -> None:
    await sign_up(client)
    await split(client, "neve@example.com")
    contact = (await client.get("/api/people")).json()["contacts"][0]
    await client.post("/api/auth/logout")
    await sign_up(client, "someone.else@example.com")

    assert (
        await client.delete(f"/api/people/contacts/{contact['id']}")
    ).status_code == 404
    assert (
        await client.post(
            f"/api/people/contacts/{contact['id']}/favourite", json={"favourite": True}
        )
    ).status_code == 404


async def test_a_group_is_a_list_of_people_you_ask_together(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    created = await client.post(
        "/api/people/groups",
        json={
            "name": "The flat",
            "members": [
                {"email": "neve@example.com", "name": "Neve"},
                {"email": "tipene@example.com"},
            ],
        },
    )

    assert created.status_code == 201, created.text
    groups = (await client.get("/api/people")).json()["groups"]
    assert len(groups) == 1
    assert groups[0]["name"] == "The flat"
    assert {m["email"] for m in groups[0]["members"]} == {
        "neve@example.com",
        "tipene@example.com",
    }


async def test_editing_a_group_replaces_its_members(client: AsyncClient) -> None:
    await sign_up(client)
    group = (
        await client.post(
            "/api/people/groups",
            json={"name": "The flat", "members": [{"email": "neve@example.com"}]},
        )
    ).json()

    await client.put(
        f"/api/people/groups/{group['id']}",
        json={"name": "The flat", "members": [{"email": "dev@example.com"}]},
    )

    members = (await client.get("/api/people")).json()["groups"][0]["members"]
    assert [m["email"] for m in members] == ["dev@example.com"]


async def test_a_name_pasted_twice_does_not_break_a_group(
    client: AsyncClient,
) -> None:
    await sign_up(client)
    created = await client.post(
        "/api/people/groups",
        json={
            "name": "The flat",
            "members": [
                {"email": "neve@example.com"},
                {"email": "NEVE@example.com"},
            ],
        },
    )

    assert created.status_code == 201, created.text
    assert len((await client.get("/api/people")).json()["groups"][0]["members"]) == 1


async def test_a_group_can_be_deleted(client: AsyncClient) -> None:
    await sign_up(client)
    group = (
        await client.post(
            "/api/people/groups",
            json={"name": "The flat", "members": [{"email": "neve@example.com"}]},
        )
    ).json()

    assert (await client.delete(f"/api/people/groups/{group['id']}")).status_code == 204
    assert (await client.get("/api/people")).json()["groups"] == []


async def test_nobody_edits_someone_elses_group(client: AsyncClient) -> None:
    await sign_up(client)
    group = (
        await client.post(
            "/api/people/groups", json={"name": "The flat", "members": []}
        )
    ).json()
    await client.post("/api/auth/logout")
    await sign_up(client, "someone.else@example.com")

    assert (await client.delete(f"/api/people/groups/{group['id']}")).status_code == 404
