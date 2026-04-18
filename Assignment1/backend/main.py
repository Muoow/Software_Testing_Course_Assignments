from fastapi import FastAPI
from upload_api import router as upload_router
from test_generator import router as test_case_router

app = FastAPI()

app.include_router(upload_router)
app.include_router(test_case_router)
