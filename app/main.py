
from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.employees import router as employee_router



app = FastAPI(
    title="AI-Powered HRMS Virtual Assistant",
    description=(
        "An AI-powered HRMS virtual assistant that provides "
        "personalized support and guidance to employees, "
        "helping them navigate HR processes and policies with ease."
    ),
    version="1.0.0",
)

# Register authentication router
app.include_router(auth_router)
# Register employee management router
app.include_router(
    employee_router,
    prefix="/api/v1",
)


@app.get("/")
def home():
    return {
        "project": "AI-Powered HRMS Virtual Assistant",
        "status": "Running",
        "message": "Welcome to the AI-Powered HRMS Virtual Assistant API.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "HRMS-API",
    }
