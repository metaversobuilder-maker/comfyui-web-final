""""
Worker for NEW ComfyUI Web API (port 8000)
Processes jobs and connects to ComfyUI - with File Watcher
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
IMAGE_MODELS = {
    "zimage_lora": r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2I_Z Image_Turbo_QwenVL_OK.json",
    "zimage_red": r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2I_Z Image Turbo_QwenVL_Red.json",
    "mainpage": r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2I_Z Image Turbo_QwenVL_main.json",
    "default": r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2I_Z Image_Turbo_QwenVL_OK.json",
}

# Video models
VIDEO_MODELS = {
    "openart": r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2V_wan22-openart.ai.json",
    "wan2.2_smoothmix": r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2V_WAN 2.2 Smooth_v2.0_FAST_CLEAN.json",
    "default": r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2V_WAN 2.2 Smooth_v2.0_FAST_CLEAN.json",
}

# Output directories
OUTPUT_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\output"
VIDEO_OUTPUT_DIR = r"C:\COMFYUINEW\ComfyUI\output\VIDEOS"
WEB_OUTPUT = r"C:\Users\moncl\.openclaw\workspace\comfyui-web\backend\output"

os.makedirs(WEB_OUTPUT, exist_ok=True)

def get_pending_job():
    """Get next pending job from new API"""
    try:
        resp = requests.get(f"{API_URL}/api/jobs?page=1&limit=20")
        data = resp.json()
        
        for job in data.get("items", []):
            if job["status"] == "pending":
                if job["type"] == "video":
                    # Check if any video is processing
                    processing = any(j["type"] == "video" and j["status"] == "processing" for j in data.get("items", []))
                    if processing:
                        print(f"Skipping video job #{job['id']} - video already processing")
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
        
        url = f"{API_URL}/api/jobs/{job_id}"
        print(f"Updating job #{job_id}: {data}")
        resp = requests.patch(url, json=data, timeout=10)
        print(f"Update response: {resp.status_code} - {resp.text}")
        return resp.ok
    except Exception as e:
        print(f"Error updating job #{job_id}: {e}")
        return False

def is_comfyui_busy():
    """Check if ComfyUI is busy"""
    try:
        resp = requests.get(f"{COMFY_URL}/queue", timeout=5)
        data = resp.json()
        return len(data.get("queue_running", [])) > 0
    except:
        return False

def load_workflow(path):
    """Load workflow JSON from file"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def send_to_comfyui(workflow_path, prompt_text, image_filename=None):
    """Send job to ComfyUI"""
    workflow = load_workflow(workflow_path)
    
    # Replace prompt in workflow - find CLIPTextEncode nodes
    for node_id, node_data in workflow.items():
        if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
            if "inputs" in node_data and "text" in node_data["inputs"]:
                workflow[node_id]["inputs"]["text"] = prompt_text
    
    # Replace prompt in Textbox nodes (for video workflows)
    for node_id, node_data in workflow.items():
        if isinstance(node_data, dict) and node_data.get("class_type") == "Textbox":
            if "inputs" in node_data and "text" in node_data["inputs"]:
                workflow[node_id]["inputs"]["text"] = prompt_text
    
    # Replace image in LoadImage nodes (for video workflows)
    if image_filename:
        input_dir = r"C:\COMFYUINEW\ComfyUI\input"
        
        # Check both output directories for the source image
        src = None
        src_main = os.path.join(OUTPUT_DIR, image_filename)
        src_video = os.path.join(VIDEO_OUTPUT_DIR, image_filename)
        
        if os.path.exists(src_main):
            src = src_main
        elif os.path.exists(src_video):
            src = src_video
        
        # Copy to input folder if found
        if src:
            dst = os.path.join(input_dir, image_filename)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f"Copied {image_filename} to input folder")
        
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "LoadImage":
                if "inputs" in node_data and "image" in node_data["inputs"]:
                    workflow[node_id]["inputs"]["image"] = image_filename
    
    print(f"Sending to ComfyUI: {workflow_path}")
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow}, timeout=30)
    if resp.status_code == 200:
        return resp.json().get("prompt_id")
    else:
        print(f"ComfyUI error: {resp.status_code} - {resp.text}")
        return None

def copy_to_output(filename):
    """Copy generated file to web output directory"""
    # Check both output directories
    src = None
    
    # Check main output dir
    src_main = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(src_main):
        src = src_main
    else:
        # Check video output dir
        src_video = os.path.join(VIDEO_OUTPUT_DIR, filename)
        if os.path.exists(src_video):
            src = src_video
    
    if src:
        dst = os.path.join(WEB_OUTPUT, filename)
        shutil.copy2(src, dst)
        print(f"Copied {filename} to web output")
        return filename
    
    print(f"File not found: {src_main} or {VIDEO_OUTPUT_DIR}/{filename}")
    return None

def get_latest_output_file(file_type, since_time):
    """Get latest image or video file created after since_time"""
    # Check both output directories
    dirs_to_check = [OUTPUT_DIR]
    if os.path.exists(VIDEO_OUTPUT_DIR):
        dirs_to_check.append(VIDEO_OUTPUT_DIR)
    
    for output_dir in dirs_to_check:
        if not os.path.exists(output_dir):
            continue
        
        for f in os.listdir(output_dir):
            fpath = os.path.join(output_dir, f)
            if not os.path.isfile(fpath):
                continue
            
            # Check type
            is_image = f.lower().endswith((".png", ".jpg", ".jpeg"))
            is_video = f.lower().endswith((".mp4", ".webm"))
            
            if file_type == "image" and not is_image:
                continue
            if file_type == "video" and not is_video:
                continue
        
        # Check if created after since_time
        mtime = os.path.getmtime(fpath)
        if mtime > since_time:
            return f
    
    return None

def process_image_job(job):
    """Process an image generation job"""
    job_id = job["id"]
    prompt = job.get("prompt", "")
    model = job.get("model", "zimage_lora")
    
    print(f"Processing image job #{job_id}: {prompt[:50]}... (model: {model})")
    
    update_job(job_id, "processing", progress=0.1)
    
    # Get workflow path for the model
    workflow_path = IMAGE_MODELS.get(model, IMAGE_MODELS["zimage_lora"])
    print(f"Using workflow: {workflow_path}")
    
    start_time = time.time()
    
    # Send to ComfyUI
    prompt_id = send_to_comfyui(workflow_path, prompt)
    if not prompt_id:
        print(f"Failed to send job #{job_id} to ComfyUI")
        update_job(job_id, "failed", error="Failed to send to ComfyUI")
        return
    
    print(f"Job #{job_id} sent to ComfyUI, prompt_id: {prompt_id}")
    
    # Poll ComfyUI history
    max_wait = 180
    checked_time = start_time
    
    while time.time() - start_time < max_wait:
        # Check ComfyUI history
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    outputs = data[prompt_id].get("outputs", {})
                    for node_id, node_data in outputs.items():
                        if "images" in node_data:
                            for img in node_data["images"]:
                                filename = img["filename"]
                                copied = copy_to_output(filename)
                                if copied:
                                    update_job(job_id, "completed", image_path=copied, progress=1.0)
                                    print(f"OK Job #{job_id} completed: {copied}")
                                    return
        except Exception as e:
            pass
        
        # Also check for new files in output
        new_file = get_latest_output_file("image", checked_time)
        if new_file:
            print(f"Found new image file: {new_file}")
            copied = copy_to_output(new_file)
            if copied:
                update_job(job_id, "completed", image_path=copied, progress=1.0)
                print(f"OK Job #{job_id} completed via file check: {copied}")
                return
            checked_time = time.time()
        
        time.sleep(3)
    
    # Last resort - get latest image file
    new_file = get_latest_output_file("image", start_time)
    if new_file:
        copied = copy_to_output(new_file)
        if copied:
            update_job(job_id, "completed", image_path=copied, progress=1.0)
            print(f"OK Job #{job_id} completed (last resort): {copied}")
            return
    
    print(f"Timeout waiting for job #{job_id}")
    update_job(job_id, "failed", error="Timeout")

def process_video_job(job):
    """Process a video generation job"""
    job_id = job["id"]
    prompt = job.get("prompt", "")
    model = job.get("model", "openart")
    
    payload = json.loads(job.get("payload", "{}"))
    image_filename = payload.get("image", "")
    
    print(f"Processing video job #{job_id} with model: {model}")
    
    update_job(job_id, "processing", progress=0.1)
    
    start_time = time.time()
    
    workflow_path = VIDEO_MODELS.get(model, VIDEO_MODELS["openart"])
    prompt_id = send_to_comfyui(workflow_path, prompt, image_filename)
    
    if not prompt_id:
        print(f"Failed to send video job #{job_id} to ComfyUI")
        update_job(job_id, "failed", error="Failed to send to ComfyUI")
        return
    
    print(f"Video job #{job_id} sent to ComfyUI")
    
    # Set timeout based on model
    if "smoothmix" in model:
        max_wait = 150  # ~2.5 minutes for smoothmix
    elif "openart" in model:
        max_wait = 500  # ~8 minutes for openart
    else:
        max_wait = 150  # default to smoothmix timeout
    
    print(f"Using timeout: {max_wait} seconds for model: {model}")
    
    print(f"Using timeout: {max_wait} seconds for model: {model}")
    checked_time = start_time
    
    while time.time() - start_time < max_wait:
        try:
            resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    outputs = data[prompt_id].get("outputs", {})
                    for node_id, node_data in outputs.items():
                        if "images" in node_data:
                            for img in node_data["images"]:
                                filename = img["filename"]
                                if filename.endswith((".mp4", ".webm")):
                                    copied = copy_to_output(filename)
                                    if copied:
                                        update_job(job_id, "completed", video_path=copied, progress=1.0)
                                        print(f"OK Video job #{job_id} completed: {copied}")
                                        return
        except:
            pass
        
        # Check for new video files
        new_file = get_latest_output_file("video", checked_time)
        if new_file:
            print(f"Found new video file: {new_file}")
            copied = copy_to_output(new_file)
            if copied:
                update_job(job_id, "completed", video_path=copied, progress=1.0)
                print(f"OK Video job #{job_id} completed: {copied}")
                return
            checked_time = time.time()
        
        time.sleep(5)
    
    # Last resort
    new_file = get_latest_output_file("video", start_time)
    if new_file:
        copied = copy_to_output(new_file)
        if copied:
            update_job(job_id, "completed", video_path=copied, progress=1.0)
            print(f"OK Video job #{job_id} completed (last resort): {copied}")
            return
    
    print(f"Timeout waiting for video job #{job_id}")
    update_job(job_id, "failed", error="Timeout")

def main():
    """Main worker loop"""
    print("Worker started for NEW API (port 8000)")
    print(f"ComfyUI: {COMFY_URL}")
    print(f"API: {API_URL}")
    print(f"Output Dir: {OUTPUT_DIR}")
    
    while True:
        try:
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
