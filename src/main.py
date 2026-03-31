from fastapi import FastAPI
from src.db.database import create_tables

app = FastAPI(title="Personalization Orchestrator", version="0.1.0")


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/")
async def root():
    return {"message": "Personalization Orchestrator"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

#to do make db schema