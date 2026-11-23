"""Test Case 2: Multi-Session Memory Persona Adaptation.

Specification:
1. Send query 1: 'Hello! I work in Python and prefer brief, code-only responses.' using user_id='usr_99'.
2. Call the memory retrieval endpoint: `/api/users/usr_99/memories`. Verify that the response lists the extracted Python preference fact.
3. Open a new chat session. Send query 2: 'Write a quick merge sort routine.' Verify the agent bypasses long explanations and returns only the python code block, adapting to the user's stored profile.
"""

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_multi_session_memory_persona_adaptation():
    """Execute Test Case 2 verification workflow across multiple sessions."""
    user_id = "usr_99"

    # Step 1: Send query 1 in session 1
    query_1_payload = {
        "query": "Hello! I work in Python and prefer brief, code-only responses.",
        "user_id": user_id,
        "session_id": "sess_profile_setup",
    }
    res1 = client.post("/api/chat", json=query_1_payload)
    assert res1.status_code == 200

    # Step 2: Call memory retrieval endpoint: `/api/users/usr_99/memories`
    # Verify that the response lists the extracted Python preference fact
    mem_res = client.get(f"/api/users/{user_id}/memories")
    assert mem_res.status_code == 200
    mem_data = mem_res.json()

    assert mem_data["user_id"] == user_id
    stored_memories = mem_data["memories"]
    assert len(stored_memories) > 0, "Expected stored memories for user usr_99"

    # Check for extracted Python preference fact
    has_python_fact = any("python" in m.lower() for m in stored_memories)
    assert has_python_fact, f"Extracted memories must list Python preference fact: {stored_memories}"

    # Step 3: Open a new chat session. Send query 2: 'Write a quick merge sort routine.'
    # Verify the agent bypasses long explanations and returns only the python code block
    query_2_payload = {
        "query": "Write a quick merge sort routine.",
        "user_id": user_id,
        "session_id": "sess_new_task_002",
    }
    res2 = client.post("/api/chat", json=query_2_payload)
    assert res2.status_code == 200
    res2_data = res2.json()
    answer = res2_data["response"].strip()

    # Assert code block presence
    assert "```python" in answer, f"Expected python code block in response: {answer}"
    assert "def merge_sort" in answer, f"Expected merge_sort routine in code block: {answer}"

    # Verify agent bypasses long explanations (starts with or is primarily the code block)
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    assert lines[0] == "```python", (
        f"Agent should bypass conversational preamble and return code block directly: {lines[0]}"
    )
