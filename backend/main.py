from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, select
from datetime import datetime
import enum
from pydantic import BaseModel

# Database
DATABASE_URL = "sqlite+aiosqlite:///./comfyui.db"

async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Models
class JobType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), default="image")
    status = Column(String(20), default="pending")
    payload = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "payload": self.payload,
            "prompt": self.prompt,
            "image_path": self.image_path,
            "video_path": self.video_path,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

# Schemas
class JobCreate(BaseModel):
    type: str = "image"
    payload: str = ""
    prompt: str = ""

class JobResponse(BaseModel):
    id: int
    type: str
    status: str
    payload: str | None
    prompt: str | None
    image_path: str | None
    video_path: str | None
    progress: float
    error_message: str | None
    created_at: str
    completed_at: str | None

    @classmethod
    def from_job(cls, job: Job):
        return cls(
            id=job.id,
            type=job.type,
            status=job.status,
            payload=job.payload,
            prompt=job.prompt,
            image_path=job.image_path,
            video_path=job.video_path,
            progress=job.progress or 0.0,
            error_message=job.error_message,
            created_at=job.created_at.isoformat() if job.created_at else "",
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )

# App
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="ComfyUI Web API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Routes
ws_connections = []

@app.post("/api/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    async with AsyncSessionLocal() as db:
        job = Job(type=job_data.type, payload=job_data.payload or "", prompt=job_data.prompt, status="pending")
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return JobResponse.from_job(job)

@app.get("/api/jobs")
async def list_jobs(page: int = 1, limit: int = 20):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).order_by(Job.created_at.desc()))
        jobs = result.scalars().all()
        total = len(jobs)
        return {"items": [j.to_dict() for j in jobs[(page-1)*limit:page*limit]], "total": total, "page": page, "pages": (total+limit-1)//limit}

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job: raise HTTPException(status_code=404, detail="Job not found")
        return JobResponse.from_job(job)

@app.patch("/api/jobs/{job_id}")
async def update_job(job_id: int, status: str = None, image_path: str = None, video_path: str = None, error_message: str = None, progress: float = None):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job: raise HTTPException(status_code=404, detail="Job not found")
        
        if status:
            job.status = status
        if image_path is not None:
            job.image_path = image_path
        if video_path is not None:
            job.video_path = video_path
        if error_message is not None:
            job.error_message = error_message
        if progress is not None:
            job.progress = progress
            
        await db.commit()
        await db.refresh(job)
        return JobResponse.from_job(job)

@app.get("/api/stats")
async def get_stats():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        return {"totalImages": sum(1 for j in jobs if j.type == "image" and j.status == "completed"), "totalVideos": sum(1 for j in jobs if j.type == "video" and j.status == "completed"), "pendingJobs": sum(1 for j in jobs if j.status == "pending")}

@app.get("/")
async def root():
    return {"message": "ComfyUI Web API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# WebSocket endpoint
ws_connections = []

@app.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
    except Exception:
        pass
    finally:
        if websocket in ws_connections:
            ws_connections.remove(websocket)

# Serve images
import os
IMAGES_DIR = "E:/ComfyUI_windows_portable/ComfyUI/output"
VIDEOS_DIR = "C:/ComfyUI-Easy-Install/ComfyUI/output/VIDEOS"

@app.get("/api/images/{filename}")
async def serve_image(filename: str):
    # Try multiple directories
    for directory in [IMAGES_DIR, VIDEOS_DIR, "output"]:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/api/videos/{filename}")
async def serve_video(filename: str):
    for directory in [VIDEOS_DIR, IMAGES_DIR, "output"]:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return FileResponse(path, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
