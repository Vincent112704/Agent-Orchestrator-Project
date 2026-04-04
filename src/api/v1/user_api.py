from fastapi import APIRouter, HTTPException, Depends
from src.db.database import get_db
from hashlib import sha256
from src.models import User as users
from sqlalchemy import and_
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()
@router.get("/")
async def test ():
    return JSONResponse(content={"message": "Hello"})

@router.post("/login")
async def login(email: str, password: str, db = Depends(get_db)):
    try:
        # Hash the password
        hashed_password = sha256(password.encode()).hexdigest()
        user = db.query(users).filter(and_(users.email == email, users.password_hash == hashed_password)).first()
        if user:
            return JSONResponse(content={"message": "Login successful", "user_id": user.user_id})
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register")
async def register(email: str, password: str, db = Depends(get_db)):
    try:
        user = db.query(users).filter(users.email == email).first()
        logging.info(f"Registering user: {user.email if user else 'None'}")
        breakpoint()
        if user:
            breakpoint()
            return JSONResponse(content={"message": "Email already registered"}, status_code=400)
        hashed_password = sha256(password.encode()).hexdigest()
        new_user = users(email=email, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return JSONResponse(content={"message": "User registered successfully", "user_id": new_user.user_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
async def get_user(user_id: str, db = Depends(get_db)):
    try:
        user = db.query(users).filter(users.user_id == user_id).first()
        if user:
            return JSONResponse(content={"user_id": user.user_id, "email": user.email})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
