from fastapi import FastAPI
from src.db.database import create_tables
from contextlib import asynccontextmanager
import logging
from src.api.v1.user_api import router as user_router
from src.db.database import get_db
from src.models import User
from sqlalchemy.orm import Session
from fastapi import Depends

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting up Personalization Orchestrator...")
    create_tables()
    logging.info("Personalization Orchestrator started successfully.")
    yield


app = FastAPI(title="Personalization Orchestrator", version="0.1.0", lifespan=lifespan)

@app.get("/database_status")
def database_status(db: Session = Depends(get_db)):
    """Check database contents"""
    try:
        return {
            "users": db.query(User).count(),
        }
    except Exception as e:
        logging.error(f"Error checking database status: {e}")
        return {"error": str(e)}
        

@app.get("/")
async def root():
    return {"message": "Personalization Orchestrator"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(user_router, prefix="/api/v1/users")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)




