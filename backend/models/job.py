from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, Float
from sqlalchemy.sql import func
from datetime import datetime
import enum
import sys
from pathlib import Path

# Add parent to path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from database import Base


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
    
    # Job type: image or video
    type = Column(SQLEnum(JobType), nullable=False, default=JobType.IMAGE)
    
    # Status of the job
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    
    # Payload (JSON as text/string for flexibility)
    payload = Column(Text, nullable=True)
    
    # Input prompt or workflow
    prompt = Column(Text, nullable=True)
    
    # Output paths
    image_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    
    # Progress tracking (0-100)
    progress = Column(Float, default=0.0)
    
    # Error message if failed
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Job(id={self.id}, type={self.type}, status={self.status})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, JobType) else self.type,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "payload": self.payload,
            "prompt": self.prompt,
            "image_path": self.image_path,
            "video_path": self.video_path,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
