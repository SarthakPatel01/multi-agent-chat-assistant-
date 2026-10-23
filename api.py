
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from jwt.exceptions import InvalidTokenError

from database import Base, engine, get_db
from models import User, ResearchReport
from schemas import (
    UserRegister, UserResponse, TokenResponse,
    ResearchRequest, ReportResponse
)
from auth import (
    hash_password, verify_password,
    create_access_token, decode_access_token
)
from pipeline import run_research_pipeline

from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AI Research Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://multi-agent-chat-assistant-rilv.onrender.com"
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",  # Only for local file testing; use a proper origin in production.
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@app.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: UserRegister,
    db: Annotated[Session, Depends(get_db)]
):
    email = str(data.email).lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    email = form.username.lower()

    user = db.scalar(select(User).where(User.email == email))

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer"
    }


@app.get("/me", response_model=UserResponse)
def me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@app.post("/research", response_model=ReportResponse, status_code=201)
def create_research(
    data: ResearchRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        result = run_research_pipeline(data.topic)
        report = result["report"]

        # Handle a pipeline that returns a string report.
        if not isinstance(report, str):
            report = str(report)

        saved_report = ResearchReport(
            topic=data.topic.strip(),
            report=report,
            user_id=current_user.id
        )

        db.add(saved_report)
        db.commit()
        db.refresh(saved_report)
        return saved_report

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Research generation or saving failed"
        )


@app.get("/reports", response_model=list[ReportResponse])
def list_reports(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    return db.scalars(
        select(ResearchReport)
        .where(ResearchReport.user_id == current_user.id)
        .order_by(ResearchReport.created_at.desc())
    ).all()


@app.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    report = db.scalar(
        select(ResearchReport).where(
            ResearchReport.id == report_id,
            ResearchReport.user_id == current_user.id
        )
    )

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


@app.delete("/reports/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    report = db.scalar(
        select(ResearchReport).where(
            ResearchReport.id == report_id,
            ResearchReport.user_id == current_user.id
        )
    )

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
