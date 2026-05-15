import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    # Arrange
    expected_redirect_path = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == expected_redirect_path


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert expected_activity in data


def test_get_activities_response_has_expected_fields():
    # Arrange
    expected_fields = {"description", "schedule",
                       "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    for activity in response.json().values():
        assert expected_fields.issubset(activity.keys())


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_new_student_succeeds():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"}


def test_signup_adds_student_to_participants():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_duplicate_student_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # already a participant in seed data

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_unknown_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/participants
# ---------------------------------------------------------------------------

def test_unregister_existing_participant_succeeds():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # existing participant in seed data

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"}


def test_unregister_removes_student_from_participants():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    client.delete(
        f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_nonexistent_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "ghost@mergington.edu"  # not a participant

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]


def test_unregister_unknown_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]
