"""
Worker para ComfyUI - Procesa jobs de la nueva API
"""
import requests
import json
import time
import shutil
import os
from datetime import datetime

API_URL = "http://localhost:8000"
COMFY_URL = "http://localhost:8188"

# Rutas
IMAGE_WORKFLOW = r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2I_Z Image_Turbo_QwenVL_OK.json"
VIDEO_WORKFLOW = r"C:\ComfyUI-Easy-Install\WORKS\RAG_I2V_wan22-openart.ai.json"
OUTPUT_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\output"
COMFYUI_INPUT = r"C:\COMFYUINEW\ComfyUI\input"
VIDEO_DIR = r"C:\COMFYUINEW\ComfyUI\output\VIDEOS"

def get_pending_job():
    """Obtener el siguiente job pendiente"""
    resp = requests.get(f"{API_URL}/api/jobs?page=1&limit=1")
    data = resp.json()
    
    for job in data.get("items", []):
        if job["status"] == "pending":
            return job
    return None

def update_job(job_id, status, data=None):
    """Actualizar job en la API"""
    job_data = {"status": status}
    if data:
        if "image_path" in data:
            job_data["image_path"] = data["image_path"]
        if "video_path" in data:
            job_data["video_path"] = data["video_path"]
        if "error_message" in data:
            job_data["error_message"] = data["error_message"]
        if "progress" in data:
            job_data["progress"] = data["progress"]
    
    requests.patch(f"{API_URL}/api/jobs/{job_id}", json=job_data)

def wait_for_comfyui_job(prompt_id, timeout=120):
    """Esperar a que ComfyUI termine el job usando history API"""
    print(f"Esperando job {prompt_id}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Verificar si el prompt está en la cola
            resp = requests.get(f"{COMFY_URL}/queue", timeout=5)
            queue_data = resp.json()
            
            running = queue_data.get("queue_running", [])
            pending = queue_data.get("queue_pending", [])
            
            # Si no está en la cola, verificar el historial
            if prompt_id not in running and prompt_id not in pending:
                # Verificar en history si ya terminó
                hist_resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=5)
                if hist_resp.status_code == 200:
                    hist = hist_resp.json()
                    if prompt_id in hist:
                        print(f"Job {prompt_id} completado en historial!")
                        return True
                
                # Si no está en cola ni en history, esperar un poco más
                time.sleep(1)
                continue
            
            print(f"Job en cola: running={len(running)}, pending={len(pending)}")
            time.sleep(2)
            
        except Exception as e:
            print(f"Error verificando job: {e}")
            time.sleep(2)
    
    print(f"Timeout esperando job {prompt_id}")
    return False

def get_latest_file(ext, min_time=None):
    """Buscar archivo más reciente"""
    all_files = []
    for directory in [VIDEO_DIR, OUTPUT_DIR]:
        if not os.path.exists(directory):
            continue
        files = [f for f in os.listdir(directory) if f.endswith(ext)]
        if files:
            for f in files:
                fpath = os.path.join(directory, f)
                all_files.append((fpath, os.path.getmtime(fpath), f, directory))
    
    if not all_files:
        return None, None
    
    all_files.sort(key=lambda x: x[1], reverse=True)
    latest = all_files[0]
    
    if min_time and latest[1] < min_time:
        for fpath, mtime, fname, fdir in all_files:
            if mtime > min_time:
                return fname, fdir
        return None, None
    
    return latest[2], latest[3]

def run_image_workflow(prompt_text):
    """Ejecutar workflow de imagen"""
    print(f"Cargando workflow: {IMAGE_WORKFLOW}")
    with open(IMAGE_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = json.load(f)
    
    # Buscar nodo 216 con String - como el worker original
    if "216" in workflow:
        if "inputs" in workflow["216"] and "String" in workflow["216"]["inputs"]:
            print(f"Actualizando nodo 216 String: {prompt_text[:30]}...")
            workflow["216"]["inputs"]["String"] = prompt_text
        elif "widgets_values" in workflow["216"]:
            workflow["216"]["widgets_values"][0] = prompt_text
            print(f"Actualizando nodo 216 widgets_values")
    
    print(f"Enviando workflow a ComfyUI")
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    print(f"Respuesta: {resp.status_code}")
    return resp.json()

def run_video_workflow(prompt_text, image_filename):
    """Ejecutar workflow de video"""
    src = os.path.join(OUTPUT_DIR, image_filename)
    dst = os.path.join(COMFYUI_INPUT, image_filename)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Imagen copiada: {src} -> {dst}")
    
    with open(VIDEO_WORKFLOW, "r", encoding="utf-8") as f:
        workflow = json.load(f)
    
    # Buscar nodos
    for node_id, node in workflow.items():
        inputs = node.get("inputs", {})
        if "image" in inputs:
            inputs["image"] = image_filename
        if "text" in inputs and isinstance(inputs.get("text"), str):
            inputs["text"] = prompt_text
    
    resp = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    return resp.json()

def process_job(job):
    """Procesar un job"""
    job_id = job["id"]
    job_type = job["type"]
    
    print(f"\n=== Procesando job {job_id}: {job_type} ===")
    update_job(job_id, "processing", {"progress": 0})
    
    try:
        payload = json.loads(job.get("payload", "{}"))
        prompt = payload.get("prompt", job.get("prompt", ""))
        
        if not prompt:
            prompt = "a beautiful woman"
        
        image_filename = payload.get("image", "")
        start_time = time.time()
        
        if job_type == "video":
            update_job(job_id, "processing", {"progress": 20})
            result = run_video_workflow(prompt, image_filename)
        else:
            update_job(job_id, "processing", {"progress": 20})
            result = run_image_workflow(prompt)
        
        if "prompt_id" in result:
            prompt_id = result["prompt_id"]
            print(f"Job enviado, prompt_id: {prompt_id}")
            
            # Usar wait_for_comfyui_job en lugar de wait_for_comfyui
            success = wait_for_comfyui_job(prompt_id, timeout=120)
            
            if not success:
                print("Timeout o error esperando ComfyUI")
            
            update_job(job_id, "processing", {"progress": 80})
            
            ext = ".mp4" if job_type == "video" else ".png"
            print(f"Buscando archivo {ext}...")
            filename, directory = get_latest_file(ext, min_time=start_time)
            
            if filename:
                if job_type == "video":
                    update_job(job_id, "completed", {"video_path": filename, "progress": 100})
                else:
                    update_job(job_id, "completed", {"image_path": filename, "progress": 100})
                print(f"[OK] Job {job_id} completado: {filename}")
            else:
                update_job(job_id, "failed", {"error_message": "No se encontro archivo"})
                print(f"[FAIL] Job {job_id} fallo: no se encontro archivo")
        else:
            update_job(job_id, "failed", {"error_message": str(result)})
            print(f"[FAIL] Job {job_id} fallo: {result}")
            
    except Exception as e:
        update_job(job_id, "failed", {"error_message": str(e)})
        print(f"[ERROR] Job {job_id} error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Worker iniciado. Esperando jobs...")
    print(f"ComfyUI: {COMFY_URL}")
    print(f"API: {API_URL}")
    while True:
        try:
            job = get_pending_job()
            if job:
                process_job(job)
            else:
                time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
