
from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.employees import router as employee_router
from app.api.users import router as user_router
from app.api.leaves import router as leave_router
from app.api.documents import router as document_router

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
# Register user management router
app.include_router(
    user_router,
    prefix="/api/v1",
)
# Register Leave Management router
app.include_router(
    leave_router,
    prefix="/api/v1",
)
# Register HR Document Management router
app.include_router(
    document_router,
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
