import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

# Import app
from backend.main import app
from backend import history_logger
from backend import feedback_logger

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown_logs():
    """Fixture to clear logs before and after each test."""
    history_logger.clear_history()
    feedback_logger.clear_feedback()
    yield
    history_logger.clear_history()
    feedback_logger.clear_feedback()

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("backend.event_analyzer.analyze_event_description")
def test_analyze_event(mock_analyze):
    mock_analyze.return_value = ["Technology", "Business & Entrepreneurship"]
    
    response = client.post(
        "/analyze-event",
        json={"event_description": "A tech startup summit", "mock": False}
    )
    assert response.status_code == 200
    assert "themes" in response.json()
    assert response.json()["themes"] == ["Technology", "Business & Entrepreneurship"]
    mock_analyze.assert_called_once_with("A tech startup summit", mock=False)

@patch("backend.event_analyzer.analyze_event_description")
@patch("backend.topic_generator.generate_conversation_starters")
def test_generate_conversation(mock_generate, mock_analyze):
    mock_analyze.return_value = ["Technology"]
    mock_generate.return_value = ["Starter A", "Starter B", "Starter C"]
    
    response = client.post(
        "/generate-conversation",
        json={
            "event_description": "Tech conference",
            "user_interests": "Python, AI",
            "mock": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "generation_id" in data
    assert data["themes"] == ["Technology"]
    assert data["conversation_starters"] == ["Starter A", "Starter B", "Starter C"]
    
    # Verify history logger logged it
    history = history_logger.get_history()
    assert len(history) == 1
    assert history[0]["generation_id"] == data["generation_id"]
    assert history[0]["conversation_starters"] == ["Starter A", "Starter B", "Starter C"]

@patch("backend.fact_checker.search_wikipedia")
@patch("backend.fact_checker.verify_claim")
def test_fact_check(mock_verify, mock_search):
    # Setup mocks
    mock_search.return_value = (
        "Python (programming language)",
        "Python is a high-level programming language created by Guido van Rossum.",
        "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )
    mock_verify.return_value = {
        "verdict": "Supported",
        "confidence": 0.95,
        "details": "Wikipedia content supports this claim."
    }
    
    response = client.post(
        "/fact-check",
        json={"claim": "Python was created by Guido", "mock": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "Supported"
    assert data["confidence"] == 0.95
    assert data["wikipedia_title"] == "Python (programming language)"
    assert data["wikipedia_url"] == "https://en.wikipedia.org/wiki/Python_(programming_language)"
    
    mock_search.assert_called_once_with("Python was created by Guido")
    mock_verify.assert_called_once_with(
        "Python was created by Guido",
        "Python is a high-level programming language created by Guido van Rossum.",
        mock=False
    )

def test_fact_check_no_results():
    with patch("backend.fact_checker.search_wikipedia", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = ("", "", "")
        
        response = client.post(
            "/fact-check",
            json={"claim": "xyzabc123 NonExistentTopic", "mock": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] == "Neutral"
        assert data["wikipedia_title"] == "None Found"

def test_feedback_logging():
    # 1. Create a generation entry in history
    gen_id = "test-gen-id-123"
    history_logger.log_generation(
        generation_id=gen_id,
        event_description="Test event",
        user_interests="Testing",
        themes=["Social"],
        starters=["Hi", "Hello", "Hey"]
    )
    
    # 2. Submit feedback
    response = client.post(
        "/feedback",
        json={"generation_id": gen_id, "rating": "like"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 3. Check stats
    stats_resp = client.get("/feedback/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["likes"] == 1
    assert stats["total"] == 1
    assert stats["like_ratio"] == 1.0
    
    # 4. Update feedback to dislike
    response2 = client.post(
        "/feedback",
        json={"generation_id": gen_id, "rating": "dislike"}
    )
    assert response2.status_code == 200
    
    stats_resp2 = client.get("/feedback/stats")
    stats2 = stats_resp2.json()
    assert stats2["dislikes"] == 1
    assert stats2["likes"] == 0
    assert stats2["like_ratio"] == 0.0

def test_clear_endpoints():
    history_logger.log_generation("id1", "desc", "int", ["Theme"], ["Starter"])
    feedback_logger.log_feedback("id1", "like")
    
    assert len(history_logger.get_history()) == 1
    assert len(feedback_logger.get_feedback()) == 1
    
    # Clear history
    resp1 = client.post("/history/clear")
    assert resp1.status_code == 200
    assert len(history_logger.get_history()) == 0
    
    # Clear feedback
    resp2 = client.post("/feedback/clear")
    assert resp2.status_code == 200
    assert len(feedback_logger.get_feedback()) == 0

