from fastapi import FastAPI, HTTPException, Request
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

# Database - PostgreSQL
DATABASE_URL = "postgresql+asyncpg://postgres:comfyui123@localhost:5432/comfyui"

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
    model = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "payload": self.payload,
            "prompt": self.prompt,
            "model": self.model,
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
    model: str | None = None

class JobResponse(BaseModel):
    id: int
    type: str
    status: str
    payload: str | None
    model: str | None
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
            model=job.model,
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
        job = Job(
            type=job_data.type, 
            payload=job_data.payload or "", 
            prompt=job_data.prompt, 
            model=job_data.model,
            status="pending"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return JobResponse.from_job(job)

@app.get("/api/status")
async def get_status():
    """Get system status - API, Worker, ComfyUI"""
    status = {
        "api": "ok",
        "worker": "unknown",
        "comfyui": "unknown",
        "postgres": "unknown"
    }
    
    # Check PostgreSQL
    try:
        import asyncpg
        conn = await asyncpg.connect('postgresql://postgres:comfyui123@localhost:5432/comfyui')
        await conn.close()
        status["postgres"] = "ok"
    except:
        status["postgres"] = "error"
    
    # Check ComfyUI
    try:
        resp = requests.get(f"{COMFY_URL}/queue", timeout=5)
        status["comfyui"] = "ok"
    except:
        status["comfyui"] = "error"
    
    # Check worker (if it processed jobs recently)
    try:
        resp = requests.get(f"{API_URL}/api/jobs?page=1&limit=1")
        if resp.ok:
            data = resp.json()
            if data.get("items"):
                latest = data["items"][0]
                # If latest job is pending/processing, worker might be stuck
                if latest["status"] in ["pending", "processing"]:
                    status["worker"] = "busy"
                else:
                    status["worker"] = "ok"
            else:
                status["worker"] = "idle"
    except:
        status["worker"] = "error"
    
    return status

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

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        await db.delete(job)
        await db.commit()
        return {"message": "Job deleted", "id": job_id}

@app.patch("/api/jobs/{job_id}")
async def update_job(job_id: int, request: Request):
    """Update job - accepts JSON body"""
    try:
        data = await request.json()
    except Exception:
        data = {}
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if "status" in data and data["status"]:
            job.status = data["status"]
        if "image_path" in data:
            job.image_path = data["image_path"]
        if "video_path" in data:
            job.video_path = data["video_path"]
        if "error_message" in data:
            job.error_message = data["error_message"]
        if "progress" in data:
            job.progress = data["progress"]
            
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
