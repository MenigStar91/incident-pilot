from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class LogInput(BaseModel):
    logs: str

@app.post("/analyze")
def analyze_logs(payload: LogInput):
    logs = payload.logs.strip()
    if "ConnectionRefusedError" in logs or "504" in logs:
        severity = "P1 - CRITICAL"
        root_cause = "Database/Upstream Service Timeout"
        evidence = [line for line in logs.split("\n") if "Connection" in line or "504" in line]
        mitigation = "1. Scale up connection pool.\n2. Restart affected microservices."
    else:
        severity = "P2 - HIGH"
        root_cause = "Unhandled Exception / Application Error"
        evidence = logs.split("\n")[:2]
        mitigation = "1. Deploy hotfix with validation.\n2. Review stack trace."

    return {
        "severity": severity,
        "summary": "AI Incident Investigator analyzed the production log anomaly.",
        "root_cause": root_cause,
        "evidence": evidence if evidence else [logs[:100]],
        "mitigation": mitigation
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
