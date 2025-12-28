# Runbook — Multi-Agent RAG System for Supplier Quotation Analysis

This document is an **operational runbook**.
It contains **all commands required to run, test, debug, and operate the system**.

No architectural explanations are included here.
For system design and agent architecture, see `README.md`.

---

## 1. Environment Setup (Local)

### 1.1 Create virtual environment
```bash
python -m venv .venv
```

### 1.2 Activate virtual environment

**Windows**
```bash
.venv\Scripts\activate
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

### 1.3 Install dependencies
```bash
pip install -r requirements.txt
```

---

## 2. Running the API Locally (Uvicorn)

### 2.1 Start the API server
```bash
uvicorn app.main:app --reload
```

### 2.2 Open API documentation (Swagger)
```text
http://127.0.0.1:8000/docs
```

---

## 3. Upload Quotations (API Test)

### 3.1 Upload sample quotations
```bash
curl -X POST http://127.0.0.1:8000/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Supplier QuickFix Ltd offers 10mm steel bolts at €0.75 per unit. Delivery in 10 days. Payment terms Net 45.",
      "EuroBuild Components can supply 10mm steel bolts for €0.78 each with delivery in 12 days. Payment terms Net 60.",
      "FastSupply Co offers 10mm steel bolts at €0.95 per unit with express delivery in 5 days. Payment terms Net 15."
    ]
  }'
```

---

## 4. Query Best Supplier (API Test)

### 4.1 Valid product query (expected success)
```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{ "query": "best supplier for 10mm steel bolts" }'
```

### 4.2 Invalid product query (expected rejection)
```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{ "query": "best please" }'
```

### 4.3 Query for non-existing product
```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{ "query": "concrete bricks" }'
```

---

## 5. Running Tests

### 5.1 Run all tests
```bash
pytest -vv
```

### 5.2 Run a specific test file
```bash
pytest tests/test_product_match.py -vv
```

### 5.3 Run query parsing tests
```bash
pytest tests/test_query_parsing.py -vv
```

---

## 6. Chroma Vector Store Management

### 6.1 Stop the API before cleaning Chroma
```bash
CTRL + C
```

### 6.2 Delete persisted Chroma database (local)
```bash
rm -rf .chroma
```

**Windows (PowerShell)**
```powershell
Remove-Item -Recurse -Force .chroma
```

### 6.3 Restart the API after cleanup
```bash
uvicorn app.main:app --reload
```

---

## 7. Docker Execution

### 7.1 Build and start containers
```bash
docker compose up --build
```

### 7.2 Run Docker in detached mode
```bash
docker compose up -d --build
```

### 7.3 View running containers
```bash
docker ps
```

### 7.4 View logs
```bash
docker compose logs -f
```

### 7.5 Stop containers
```bash
docker compose down
```

---

## 8. Docker Cleanup (Optional)

### 8.1 Stop and remove containers
```bash
docker compose down
```

### 8.2 Remove dangling images
```bash
docker image prune -f
```

---

## 9. Validation Checklist

Use this checklist after starting the system:

- API running at `http://127.0.0.1:8000`
- Swagger UI available at `/docs`
- Upload endpoint returns ingested offers
- Query endpoint:
  - Rejects mismatched products
  - Rejects unknown queries
  - Returns ranked offers for valid products
- `pytest -vv` passes with no failures

---

## 10. Shutdown

### 10.1 Stop local server
```bash
CTRL + C
```

### 10.2 Stop Docker services
```bash
docker compose down
```

---

End of runbook.
