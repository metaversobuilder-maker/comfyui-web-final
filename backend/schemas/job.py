from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobBase(BaseModel):
    type: JobType = JobType.IMAGE
    payload: Optional[str] = None
    prompt: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    status: JobStatus = JobStatus.PENDING
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobList(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    pages: int


class StatsResponse(BaseModel):
    totalImages: int
    totalVideos: int
    pendingJobs: int
