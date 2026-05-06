import pytest
from fastapi.testclient import TestClient
from main import app

# Initialize test client
client = TestClient(app)

def test_get_patient_success():
    """Test UC24: Learn about latest health status (GET FHIR Patient)"""
    response = client.get("/api/v1/emr/Patient/123")
    
    # Verbose assertion: if this fails, it prints the exact server error
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Details: {response.text}"
    
    data = response.json()
    
    # Contract Verification
    assert data.get("resourceType") == "Patient", f"Invalid resource type: {data.get('resourceType')}"
    assert data.get("id") == "123"
    
    # FIX: The FHIR 'name' field is a list. We must safely index it with first!
    patient_name_list = data.get("name", [])
    assert len(patient_name_list) > 0, "Patient name list is empty!"
    assert patient_name_list.get("family") == "Smith", f"Expected Smith, got {patient_name_list.get('family')}"

def test_get_patient_not_found():
    """Test boundary condition for EMR queries"""
    response = client.get("/api/v1/emr/Patient/999")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}. Details: {response.text}"

def test_process_assessment_intent():
    """Test UC06: Record assessment using voice assistant"""
    payload = {
        "sessionID": "sess-001",
        "userID": "nurse-01",
        "rawText": "Patient Jane Smith, vitals stable. Blood pressure 122 over 78. Will notify physician."
    }
    response = client.post("/api/v1/assistant/process", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Details: {response.text}"
    
    data = response.json()
    assert data["intentLabel"] == "RECORD_ASSESSMENT"
    assert data["actionTaken"] == "Posted Clinical Note to EMR"
    assert "documentID" in data["data"]

def test_process_lab_query_intent():
    """Test UC11: Query lab database"""
    payload = {
        "sessionID": "sess-002",
        "userID": "nurse-01",
        "rawText": "Nurse Mate, what are the latest lab results?"
    }
    response = client.post("/api/v1/assistant/process", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Details: {response.text}"
    
    data = response.json()
    assert data["intentLabel"] == "QUERY_LAB_RESULTS"
    assert data["actionTaken"] == "Queried EMR for Labs"

def test_task_creation():
    """Test UC40: Manager assign task to Nurse"""
    payload = {
        "title": "Administer IV Fluids",
        "assignedTo": "nurse-02",
        "priority": 1
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Details: {response.text}"
    
    data = response.json()
    assert data["status"] == "PENDING"
    assert "taskID" in data
    assert data["assignedTo"] == "nurse-02"

def test_process_general_intent():
    """Test fallback intent routing for non-clinical chatter"""
    payload = {
        "sessionID": "sess-003",
        "userID": "nurse-01",
        "rawText": "Hello Nurse Mate, just checking the microphone."
    }
    response = client.post("/api/v1/assistant/process", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Details: {response.text}"
    
    data = response.json()
    assert data["intentLabel"] == "GENERAL_COMMUNICATION"
    assert data["actionTaken"] == "None"

def test_task_creation_validation_error():
    """Test strict contract validation (missing required fields triggers 422)"""
    payload = {
        "title": "Administer IV Fluids"
        # Missing 'assignedTo' and 'priority' to intentionally trigger Pydantic validation
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 422, "Expected 422 Unprocessable Entity for missing fields"
    assert "detail" in response.json(), "FastAPI should return validation details"