from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from upload_api import router as upload_router
from test_generator import router as test_case_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(upload_router)
app.include_router(test_case_router)
