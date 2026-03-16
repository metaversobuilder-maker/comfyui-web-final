from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import sys
from pathlib import Path

# Add parent to path
backend_dir = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(backend_dir))

from api.schemas.job import JobCreate, JobResponse, JobList, StatsResponse
from models.job import Job
from database import AsyncSessionLocal

router = APIRouter(prefix="/api", tags=["jobs"])

# WebSocket connections
ws_connections: List[WebSocket] = []


@router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    """Crear un nuevo job (imagen o video)"""
    async with AsyncSessionLocal() as db:
        job = Job(
            type=job_data.type.value if hasattr(job_data.type, 'value') else job_data.type,
            payload=job_data.payload or "",
            prompt=job_data.prompt,
            status="pending"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        # Notify all WS clients
        for ws in ws_connections:
            try:
                await ws.send_json({"type": "job_created", "job": job.to_dict()})
            except:
                pass
        
        return job


@router.get("/jobs", response_model=JobList)
async def list_jobs(page: int = 1, limit: int = 20):
    """Listar jobs con paginación"""
    async with AsyncSessionLocal() as db:
        query = select(Job).order_by(Job.created_at.desc())
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        total = len(jobs)
        jobs_page = jobs[(page - 1) * limit:page * limit]
        
        return {
            "items": [j.to_dict() for j in jobs_page],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    """Obtener un job específico"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).filter(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Obtener estadísticas"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        
        total_images = sum(1 for j in jobs if j.type == "image" and j.status == "completed")
        total_videos = sum(1 for j in jobs if j.type == "video" and j.status == "completed")
        pending = sum(1 for j in jobs if j.status == "pending")
        
        return {
            "totalImages": total_images,
            "totalVideos": total_videos,
            "pendingJobs": pending
        }


@router.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """WebSocket para updates en tiempo real"""
    await websocket.accept()
    ws_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_connections.remove(websocket)
