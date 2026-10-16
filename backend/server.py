import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the official Google GenAI client (picks up GEMINI_API_KEY from environment)
client = genai.Client()

class LogInput(BaseModel):
    logs: str

# Define the exact structural schema we want back from Gemini
class IncidentReport(BaseModel):
    severity: str = Field(description="Severity rating, e.g., 'P1 - CRITICAL' or 'P2 - HIGH'")
    summary: str = Field(description="A brief 1-sentence summary of the incident analysis")
    root_cause: str = Field(description="The technical root cause of the error log")
    evidence: list[str] = Field(description="List of specific strings or lines extracted from logs as proof")
    mitigation: str = Field(description="Numbered step-by-step remediation plan")

@app.post("/analyze", response_model=IncidentReport)
def analyze_logs(payload: LogInput):
    if not payload.logs.strip():
        raise HTTPException(status_code=400, data={"error": "Log input cannot be empty"})

    prompt = f"""
    You are an expert Principal Site Reliability Engineer (SRE). 
    Analyze the following production error logs, diagnose the issue, determine its severity, 
    extract key evidence lines, and provide clear remediation steps.
    
    Logs:
    {payload.logs}
    """

    try:
        # Call Gemini 2.5/3.5 Flash using structured schema outputs
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IncidentReport,
                temperature=0.2,
            ),
        )
        
        # Parse the structured JSON string back into a Python dictionary/model response
        import json
        result_data = json.loads(response.text)
        return result_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
