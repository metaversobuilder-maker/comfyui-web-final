"""
Worker for NEW ComfyUI Web API (port 8000)
Processes jobs and connects to ComfyUI
"""
import requests
import json
import time
import shutil
import os
from datetime import datetime

API_URL = "http://localhost:8000"
COMFY_URL = "http://localhost:8188"

# Workflows paths
IMAGE_WORKFLOW = r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2I_Z Image_Turbo_QwenVL_OK.json"
VIDEO_WORKFLOW = r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2V_wan22-openart.ai.json"

# Output directories
OUTPUT_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\output"
WEB_OUTPUT = r"C:\Users\moncl\.openclaw\workspace\comfyui-web\backend\output"

os.makedirs(WEB_OUTPUT, exist_ok=True)

def get_pending_job():
    """Get next pending job from new API, skipping if video already processing"""
    try:
        resp = requests.get(f"{API_URL}/api/jobs?page=1&limit=20")
        data = resp.json()
        
        # Check if any video is currently processing
        video_processing = any(
            j["type"] == "video" and j["status"] == "processing" 
            for j in data.get("items", [])
        )
        
        for job in data.get("items", []):
            if job["status"] != "pending":
                continue
            
            # Skip video jobs if another video is already processing
            if job["type"] == "video" and video_processing:
                print(f"Skipping video job #{job['id']} - video already in processing")
                continue
                
            return job
        return None
    except Exception as e:
        print(f"Error getting job: {e}")
        return None

def update_job(job_id, status, image_path=None, video_path=None, error=None, progress=None):
    """Update job in new API"""
    try:
        data = {"status": status}
        if image_path:
            data["image_path"] = image_path
        if video_path:
            data["video_path"] = video_path
        if error:
            data["error_message"] = error
        if progress is not None:
            data["progress"] = progress
            
        requests.patch(f"{API_URL}/api/jobs/{job_id}", json=data)
    except Exception as e:
        print(f"Error updating job: {e}")

def is_comfyui_busy():
    """Check if ComfyUI is busy"""
    try:
        resp = requests.get(f"{COMFY_URL}/queue", timeout=5)
        data = resp.json()
        return len(data.get("queue_running", [])) > 0 or len(data.get("queue_pending", [])) > 0
    except:
        return False

def load_workflow(path):
    """Load workflow JSON from file"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def send_to_comfyui(workflow_path, prompt_text):
    """Send job to ComfyUI"""
    workflow = load_workflow(workflow_path)
    
    # Replace prompt in workflow
    if "4" in workflow and "inputs" in workflow["4"]:
        workflow["4"]["inputs"]["text"] = prompt_text
    
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=30)
    if resp.status_code == 200:
        return resp.json().get("prompt_id")
    else:
        print(f"ComfyUI error: {resp.status_code} - {resp.text}")
        return None

def wait_for_comfyui(prompt_id, timeout=180):
    """Wait for ComfyUI to finish"""
    print(f"Waiting for {prompt_id}...")
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    outputs = data[prompt_id].get("outputs", {})
                    # Find SaveImage node
                    for node_id, node_data in outputs.items():
                        if "images" in node_data:
                            for img in node_data["images"]:
                                return img["filename"]
        except:
            pass
        time.sleep(2)
    
    return None

def copy_to_output(filename):
    """Copy generated file to web output directory"""
    src = os.path.join(OUTPUT_DIR, filename)
    dst = os.path.join(WEB_OUTPUT, filename)
    
    if os.path.exists(src):
        shutil.copy2(src, dst)
        return filename
    return None

def process_image_job(job):
    """Process an image generation job"""
    job_id = job["id"]
    prompt = job.get("prompt", "")
    
    print(f"Processing image job #{job_id}: {prompt[:50]}...")
    
    # Update to processing
    update_job(job_id, "processing", progress=0.1)
    
    # Send to ComfyUI
    prompt_id = send_to_comfyui(IMAGE_WORKFLOW, prompt)
    if not prompt_id:
        update_job(job_id, "failed", error="Failed to send to ComfyUI")
        return
    
    # Wait for completion
    filename = wait_for_comfyui(prompt_id, timeout=180)
    
    if filename:
        # Copy to output
        copied = copy_to_output(filename)
        if copied:
            update_job(job_id, "completed", image_path=copied, progress=1.0)
            print(f"OK Job #{job_id} completed: {copied}")
        else:
            update_job(job_id, "failed", error="File not found")
    else:
        update_job(job_id, "failed", error="Timeout waiting for ComfyUI")

def process_video_job(job):
    """Process a video generation job"""
    job_id = job["id"]
    prompt = job.get("prompt", "")
    
    print(f"Processing video job #{job_id}: {prompt[:50]}...")
    
    update_job(job_id, "processing", progress=0.1)
    
    prompt_id = send_to_comfyui(VIDEO_WORKFLOW, prompt)
    if not prompt_id:
        update_job(job_id, "failed", error="Failed to send to ComfyUI")
        return
    
    filename = wait_for_comfyui(prompt_id, timeout=300)
    
    if filename:
        copied = copy_to_output(filename)
        if copied:
            update_job(job_id, "completed", video_path=copied, progress=1.0)
            print(f"OK Video job #{job_id} completed: {copied}")
        else:
            update_job(job_id, "failed", error="File not found")
    else:
        update_job(job_id, "failed", error="Timeout")

def main():
    """Main worker loop"""
    print("Worker Worker started for NEW API (port 8000)")
    print(f"ComfyUI: {COMFY_URL}")
    print(f"API: {API_URL}")
    
    while True:
        try:
            # Check if ComfyUI is busy
            if is_comfyui_busy():
                print("ComfyUI busy, waiting...")
                time.sleep(5)
                continue
            
            # Get pending job
            job = get_pending_job()
            
            if job:
                print(f"Found job #{job['id']}: {job['type']}")
                
                if job["type"] == "image":
                    process_image_job(job)
                elif job["type"] == "video":
                    process_video_job(job)
            else:
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("Worker stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
