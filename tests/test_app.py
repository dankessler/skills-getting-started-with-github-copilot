"""
Tests for the FastAPI application.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state between tests."""
    from app import activities
    initial_state = {
        "Basketball": {
            "description": "Team sport focusing on basketball skills and competitive play",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Individual and doubles tennis training",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["alex@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater production, acting, and performance arts",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and visual art creation",
            "schedule": "Mondays, Wednesdays, Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 18,
            "participants": ["grace@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["marcus@mergington.edu", "nina@mergington.edu"]
        },
        "Science Club": {
            "description": "Hands-on experiments and scientific exploration",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["ryan@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    activities.clear()
    activities.update(initial_state)
    yield
    activities.clear()
    activities.update(initial_state)


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirect(self, client):
        """Test that root redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that get activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert data["Basketball"]["description"] == "Team sport focusing on basketball skills and competitive play"

    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that activities include participant information."""
        response = client.get("/activities")
        data = response.json()
        assert "participants" in data["Basketball"]
        assert "james@mergington.edu" in data["Basketball"]["participants"]

    def test_get_activities_includes_schedule(self, client, reset_activities):
        """Test that activities include schedule information."""
        response = client.get("/activities")
        data = response.json()
        assert "schedule" in data["Basketball"]
        assert "max_participants" in data["Basketball"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant."""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up newstudent@mergington.edu for Basketball" in response.json()["message"]

    def test_signup_updates_participants_list(self, client, reset_activities):
        """Test that signup updates the participants list."""
        client.post("/activities/Tennis%20Club/signup?email=newplayer@mergington.edu")
        response = client.get("/activities")
        participants = response.json()["Tennis Club"]["participants"]
        assert "newplayer@mergington.edu" in participants

    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up the same participant twice fails."""
        # First signup succeeds
        response1 = client.post(
            "/activities/Basketball/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200

        # Second signup for same activity and email fails
        response2 = client.post(
            "/activities/Basketball/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a non-existent activity fails."""
        response = client.post(
            "/activities/NonexistentClub/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signing up with special characters in email."""
        response = client.post(
            "/activities/Art%20Studio/signup?email=test%2Bstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "test+student@mergington.edu" in response.json()["message"]


class TestRemoveParticipant:
    """Tests for the DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_remove_existing_participant(self, client, reset_activities):
        """Test removing an existing participant."""
        response = client.delete(
            "/activities/Basketball/participants/james@mergington.edu"
        )
        assert response.status_code == 200
        assert "Removed james@mergington.edu from Basketball" in response.json()["message"]

    def test_remove_updates_participants_list(self, client, reset_activities):
        """Test that removal updates the participants list."""
        client.delete("/activities/Drama%20Club/participants/isabella@mergington.edu")
        response = client.get("/activities")
        participants = response.json()["Drama Club"]["participants"]
        assert "isabella@mergington.edu" not in participants
        assert "lucas@mergington.edu" in participants  # Other participant remains

    def test_remove_nonexistent_activity_fails(self, client, reset_activities):
        """Test that removing from non-existent activity fails."""
        response = client.delete(
            "/activities/NonexistentClub/participants/someone@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing non-existent participant fails."""
        response = client.delete(
            "/activities/Basketball/participants/notamember@mergington.edu"
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_and_signup_same_participant(self, client, reset_activities):
        """Test removing then re-signing up the same participant."""
        # Remove participant
        response1 = client.delete(
            "/activities/Basketball/participants/james@mergington.edu"
        )
        assert response1.status_code == 200

        # Sign up again
        response2 = client.post(
            "/activities/Basketball/signup?email=james@mergington.edu"
        )
        assert response2.status_code == 200

        # Verify participant is back
        response3 = client.get("/activities")
        participants = response3.json()["Basketball"]["participants"]
        assert "james@mergington.edu" in participants


class TestActivityConstraints:
    """Tests for activity constraints and business logic."""

    def test_activity_description_preserved(self, client, reset_activities):
        """Test that activity descriptions are preserved."""
        response = client.get("/activities")
        assert response.json()["Programming Class"]["description"] == "Learn programming fundamentals and build software projects"

    def test_max_participants_information(self, client, reset_activities):
        """Test that max participants information is available."""
        response = client.get("/activities")
        data = response.json()
        assert data["Basketball"]["max_participants"] == 15
        assert data["Gym Class"]["max_participants"] == 30
