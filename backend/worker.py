"""
Worker Service - Processes jobs from queue and generates images/videos
Uses the existing database models
"""
import asyncio
import os
import json
import aiohttp
from datetime import datetime
from sqlalchemy import select
from database import AsyncSessionLocal
from models.job import Job, JobStatus, JobType

# ComfyUI configuration
COMFYUI_HOST = os.getenv("COMFYUI_HOST", "http://localhost:8188")
OUTPUT_DIR = "E:/ComfyUI_windows_portable/ComfyUI/output"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("output", exist_ok=True)


async def get_comfyui_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession()


async def queue_prompt(workflow: dict) -> str | None:
    """Queue a prompt to ComfyUI"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{COMFYUI_HOST}/prompt", json={"prompt": workflow}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("prompt_id")
        except Exception as e:
            print(f"Error queueing prompt: {e}")
    return None


async def get_history(prompt_id: str) -> dict:
    """Get history for a prompt"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{COMFYUI_HOST}/history/{prompt_id}") as resp:
                return await resp.json()
        except:
            return {}


def build_image_workflow(prompt: str, seed: int = 42) -> dict:
    """Build a simple SD workflow"""
    return {
        "1": {
            "inputs": {
                "seed": seed,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "model": [" comfyui_tools_h付费模型 none", ["sd1.5", "model"]],
                "positive": [prompt, []],
                "negative": "",
                "latent_image": ["3", 0]
            },
            "class_type": "KSampler"
        },
        "3": {
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "4": {
            "inputs": {
                "filename_prefix": f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "images": ["1", 0]
            },
            "class_type": "SaveImage"
        }
    }


async def process_job(job: Job):
    """Process a single job"""
    print(f"Processing job #{job.id}: {job.type} - {job.prompt[:50] if job.prompt else 'No prompt'}...")
    
    try:
        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.progress = 10.0
        async with AsyncSessionLocal() as db:
            await db.commit()
        
        if job.type == JobType.IMAGE:
            await generate_image(job)
        elif job.type == JobType.VIDEO:
            await generate_video(job)
            
    except Exception as e:
        print(f"Job #{job.id} failed: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        async with AsyncSessionLocal() as db:
            await db.commit()


async def generate_image(job: Job):
    """Generate image using ComfyUI"""
    prompt = job.prompt or "a beautiful landscape"
    
    # Build workflow
    workflow = build_image_workflow(prompt, seed=job.id)
    
    # Queue prompt
    prompt_id = await queue_prompt(workflow)
    if not prompt_id:
        raise Exception("Failed to queue prompt")
    
    print(f"   Prompt queued: {prompt_id}")
    
    # Wait for completion
    max_wait = 300  # 5 minutes
    elapsed = 0
    
    while elapsed < max_wait:
        await asyncio.sleep(3)
        elapsed += 3
        
        try:
            history = await get_history(prompt_id)
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_id, node_data in outputs.items():
                    if "images" in node_data:
                        for img in node_data["images"]:
                            filename = img.get("filename")
                            if filename:
                                # Find and copy the image
                                src = os.path.join(OUTPUT_DIR, filename)
                                if os.path.exists(src):
                                    dest = os.path.join("output", filename)
                                    import shutil
                                    shutil.copy2(src, dest)
                                    
                                    job.image_path = filename
                                    job.status = JobStatus.COMPLETED
                                    job.progress = 100.0
                                    job.completed_at = datetime.utcnow()
                                    async with AsyncSessionLocal() as db:
                                        await db.commit()
                                    print(f"✅ Job #{job.id} completed: {filename}")
                                    return
        except Exception as e:
            print(f"   Checking status... {e}")
    
    raise Exception("Timeout waiting for generation")


async def generate_video(job: Job):
    """Generate video using ComfyUI/Wan"""
    # For now, mark as failed - needs proper Wan2.2 integration
    job.status = JobStatus.FAILED
    job.error_message = "Video generation not yet implemented"
    async with AsyncSessionLocal() as db:
        await db.commit()


async def run_worker():
    """Main worker loop"""
    print("Worker starting...")
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Get oldest pending job
                result = await db.execute(
                    select(Job)
                    .where(Job.status == JobStatus.PENDING)
                    .order_by(Job.created_at.asc())
                    .limit(1)
                )
                job = result.scalar_one_or_none()
                
                if job:
                    await process_job(job)
                else:
                    await asyncio.sleep(2)  # Wait for new jobs
                    
        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
