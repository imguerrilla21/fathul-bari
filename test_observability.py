import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_tests():
    print("--- Stage 45 Observability Verification ---")
    
    # 1. Health and Ready check
    r = httpx.get(f"{BASE_URL}/health")
    print(f"GET /health: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    
    r = httpx.get(f"{BASE_URL}/ready")
    print(f"GET /ready: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    
    # 2. Simulate API Request Telemetry
    trace_id = f"TRACE-{int(time.time())}"
    r = httpx.post(f"{BASE_URL}/telemetry/request", json={
        "trace_id": trace_id,
        "endpoint": "/api/v1/workspace/projects",
        "request_type": "POST",
        "status": "200 OK",
        "start_time": time.time() - 0.2
    })
    print(f"POST /telemetry/request: {r.status_code}")
    
    # 3. Simulate AI Generation Telemetry
    r = httpx.post(f"{BASE_URL}/telemetry/ai_generation", json={
        "trace_id": trace_id,
        "model_name": "gpt-4-turbo",
        "model_version": "v1",
        "prompt_version": "research-v3",
        "retrieval_version": "rag-v8",
        "input_tokens": 432,
        "output_tokens": 128,
        "finish_reason": "stop",
        "start_time": time.time() - 1.5
    })
    print(f"POST /telemetry/ai_generation: {r.status_code}")
    
    # 4. Trigger Incident
    r = httpx.post(f"{BASE_URL}/telemetry/incident", json={
        "incident_code": "LLM-002",
        "severity": "WARNING",
        "component": "AI Generation",
        "description": "Fallback to backup model",
        "trace_id": trace_id
    })
    print(f"POST /telemetry/incident: {r.status_code}")
    
    # 5. Trigger Evaluation Suite
    r = httpx.post(f"{BASE_URL}/evaluation/run")
    print(f"POST /evaluation/run: {r.status_code}")
    
    # 6. Check Quality Gate
    r = httpx.get(f"{BASE_URL}/quality/gate")
    print(f"GET /quality/gate: {r.status_code}")
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    run_tests()
