from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import ProjectConfig, CalculationResponse
from .financial_logic import FinancialCalculator

app = FastAPI(title="Real Estate Financial Tracker API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo purposes
projects_db = {}

@app.get("/")
def read_root():
    return {"message": "Financial Tracker API is running"}

@app.post("/calculate", response_model=CalculationResponse)
def calculate_project(config: ProjectConfig):
    try:
        calculator = FinancialCalculator(config)
        flow = calculator.calculate()
        kpis = calculator.get_kpis(flow)
        return CalculationResponse(flow=flow, kpis=kpis)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/projects")
def save_project(config: ProjectConfig):
    projects_db[config.name] = config
    return {"message": "Project saved successfully", "name": config.name}

@app.get("/projects")
def list_projects():
    return list(projects_db.values())
