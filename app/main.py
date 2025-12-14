from fastapi import FastAPI


from app.api.upload_api import router as upload_router
from app.api.query_api import router as query_router

app = FastAPI(title="Supplier Quotation Multi-Agent API")

app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(query_router, prefix="/api", tags=["query"])

