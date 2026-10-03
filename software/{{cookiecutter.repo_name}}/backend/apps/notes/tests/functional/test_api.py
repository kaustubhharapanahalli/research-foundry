"""The notes API, end to end: permissions, rules, conflicts and paging."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.notes.models import Note

pytestmark = pytest.mark.django_db
NOTES = "/api/notes/"


def test_anonymous_requests_are_refused() -> None:
    assert APIClient().get(NOTES).status_code == 403


def test_a_created_note_is_listed_with_paging(api: APIClient) -> None:
    created = api.post(NOTES, {"title": "Ideas", "body": "Many."})
    assert created.status_code == 201
    listing = api.get(NOTES).json()
    assert listing["count"] == 1
    assert listing["results"][0]["title"] == "Ideas"
    assert listing["results"][0]["created_at"]


def test_another_users_notes_stay_out_of_reach(
    api: APIClient, other_user: User
) -> None:
    theirs = Note.objects.create(owner=other_user, title="Theirs")
    assert api.get(NOTES).json()["count"] == 0
    assert api.get(f"{NOTES}{theirs.pk}/").status_code == 404
    assert api.delete(f"{NOTES}{theirs.pk}/").status_code == 404


@pytest.mark.parametrize("title", ["", "   "])
def test_a_blank_title_is_a_bad_request(api: APIClient, title: str) -> None:
    # DRF trims whitespace first, so both are blank before the model's own
    # rule is reached; the model tests cover that rule directly.
    response = api.post(NOTES, {"title": title})
    assert response.status_code == 400
    assert "may not be blank" in str(response.json())


def test_a_duplicate_title_is_a_bad_request(api: APIClient) -> None:
    api.post(NOTES, {"title": "Ideas"})
    response = api.post(NOTES, {"title": "IDEAS"})
    assert response.status_code == 400
    assert "already have a note" in str(response.json())


def test_a_write_that_slips_past_validation_is_a_conflict(
    api: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # As if a concurrent request saved the same title between this one's
    # check and its insert: Postgres refuses, and the API answers 409.
    api.post(NOTES, {"title": "Ideas"})
    monkeypatch.setattr(Note, "validate_constraints", lambda self: None)
    response = api.post(NOTES, {"title": "ideas"})
    assert response.status_code == 409
    assert Note.objects.count() == 1


def test_the_owner_can_delete_a_note(api: APIClient) -> None:
    note_id = api.post(NOTES, {"title": "Ideas"}).json()["id"]
    assert api.delete(f"{NOTES}{note_id}/").status_code == 204
    assert not Note.objects.exists()


def test_the_schema_is_served_to_signed_in_users(api: APIClient) -> None:
    response = api.get("/api/schema/")
    assert response.status_code == 200
    assert b"/api/notes/" in response.content
