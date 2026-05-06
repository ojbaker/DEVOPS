# %% [markdown]
# # Nurse Mate Smart Assistant API
# 
# This notebook contains the complete FastAPI implementation for the Nurse Mate backend, including the SMART on FHIR R4 endpoints and the NLP intent routing logic.
# 
# **Note:** To run this API server directly inside this notebook environment, make sure to execute the bottom cell which utilizes `nest_asyncio` and `uvicorn`.

# %%
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

# Initialize FastAPI Application
app = FastAPI(
    title="Nurse Mate Smart Assistant API", 
    version="1.0.1", 
    description="Intelligent Communication Tool & Clinical Co-Pilot for Nurses"
)

# ==========================================
# 1. API CONTRACTS (Data Models)
# ==========================================

class FHIRPatient(BaseModel):
    """Contract for EMR R4 Patient Resource"""
    resourceType: str = "Patient"
    id: str
    name: List[Dict[str, Any]]
    gender: str
    birthDate: str

class FHIRDocumentReference(BaseModel):
    """Contract for EMR R4 Clinical Note / Document Reference"""
    resourceType: str = "DocumentReference"
    status: str = Field("current", description="Required in R4: Status of this document reference")
    subject: Dict[str, Any] = Field(..., description="Reference to the Patient")
    type: Dict[str, Any] = Field(..., description="Document type (e.g., LOINC code)")
    content: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None

class TranscriptInput(BaseModel):
    """Contract for incoming Speech-to-Text processed payload"""
    sessionID: str
    userID: str
    rawText: str

class AssistantResponse(BaseModel):
    """Contract for the Smart Assistant's NLP resolution"""
    intentLabel: str
    confidence: float
    actionTaken: str
    data: Dict[str, Any]

class TaskCreate(BaseModel):
    """Contract for assigning a new task"""
    title: str
    assignedTo: str
    priority: int

class Task(TaskCreate):
    """Contract for a managed task within the system"""
    taskID: str
    status: str
    dueTime: datetime

# ==========================================
# 2. IN-MEMORY MOCKS & DATABASES
# ==========================================
MOCK_PATIENTS = {
    "123": FHIRPatient(
        id="123", 
        name=[{"family": "Smith", "given": ["Jane"]}], 
        gender="female", 
        birthDate="1975-06-15"
    )
}
TASKS_DB = []

# ==========================================
# 3. DOMAIN SERVICES (Business Logic)
# ==========================================

class NLPEngine:
    @staticmethod
    def classify_intent(text: str) -> str:
        text = text.lower()
        if "vitals" in text or "blood pressure" in text or "assessment" in text:
            return "RECORD_ASSESSMENT" 
        elif "lab" in text:
            return "QUERY_LAB_RESULTS" 
        elif "task" in text or "delegate" in text:
            return "CREATE_TASK"       
        return "GENERAL_COMMUNICATION"

class EMRInterface:
    @staticmethod
    def get_patient(patient_id: str) -> FHIRPatient:
        if patient_id in MOCK_PATIENTS:
            return MOCK_PATIENTS[patient_id]
        raise HTTPException(status_code=404, detail="Patient not found in EMR Sandbox")

    @staticmethod
    def post_note(note: FHIRDocumentReference) -> dict:
        return {"status": "success", "documentID": str(uuid.uuid4())}

# ==========================================
# 4. RESTFUL ENDPOINTS
# ==========================================

@app.post("/api/v1/assistant/process", response_model=AssistantResponse)
def process_input(transcript: TranscriptInput):
    intent = NLPEngine.classify_intent(transcript.rawText)
    
    action_taken = "None"
    data_payload = {}

    if intent == "RECORD_ASSESSMENT":
        doc = FHIRDocumentReference(
            status="current",
            subject={"reference": "Patient/123"},
            type={"coding": [{"system": "http://loinc.org", "code": "11488-4", "display": "Consult note"}]},
            content=[{"attachment": {"data": "base64encoded_clinical_text==", "contentType": "text/plain"}}]
        )
        res = EMRInterface.post_note(doc)
        action_taken = "Posted Clinical Note to EMR"
        data_payload = res
        
    elif intent == "QUERY_LAB_RESULTS":
        action_taken = "Queried EMR for Labs"
        data_payload = {"labs": [{"test": "CBC", "result": "Within Normal Limits", "referenceRange": "4.0-10.0"}]}

    return AssistantResponse(
        intentLabel=intent, 
        confidence=0.97, 
        actionTaken=action_taken, 
        data=data_payload
    )

@app.get("/api/v1/emr/Patient/{patient_id}", response_model=FHIRPatient)
def get_patient(patient_id: str):
    return EMRInterface.get_patient(patient_id)

@app.post("/api/v1/tasks", response_model=Task)
def create_task(task: TaskCreate):
    # Compatibility mapping for both Pydantic V1 and V2
    task_data = task.model_dump() if hasattr(task, 'model_dump') else task.dict()
    
    new_task = Task(
        **task_data, 
        taskID=str(uuid.uuid4()), 
        status="PENDING", 
        dueTime=datetime.now(timezone.utc)
    )
    TASKS_DB.append(new_task)
    return new_task


# %% [markdown]
# ### Run Server in Notebook
# FastAPI normally blocks the thread. To run it inside a Jupyter Notebook interactively, we apply `nest_asyncio` and start the server using `uvicorn`.

# %%
# !pip install nest_asyncio uvicorn
import nest_asyncio
import uvicorn

nest_asyncio.apply()

# Start the API server on port 8000
uvicorn.run(app, host="0.0.0.0", port=8000)


