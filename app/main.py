from fastapi import FastAPI


app= FastAPI(
    title="AI-Powered HRMS Virtual Assistant" ,
    description="An AI-powered HRMS virtual assistant that provides personalized support and guidance to employees, helping them navigate HR processes and policies with ease.",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "project":"AI-Powered HRMS Virtual Assistant",
        "status":"Running",
        "message":"Welcome to the AI-Powered HRMS Virtual Assistant API. "
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service":"HRMS-API",
    }