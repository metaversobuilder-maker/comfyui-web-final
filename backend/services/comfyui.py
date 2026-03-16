"""
ComfyUI API Integration Service
Handles communication with ComfyUI (port 8188) for image/video generation
"""
import aiohttp
import asyncio
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

COMFYUI_HOST = os.getenv("COMFYUI_HOST", "http://localhost:8188")

class ComfyUIService:
    def __init__(self, host: str = COMFYUI_HOST):
        self.host = host
        self.client: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self.client is None or self.client.closed:
            self.client = aiohttp.ClientSession()
        return self.client
    
    async def close(self):
        if self.client and not self.client.closed:
            await self.client.close()
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get ComfyUI system stats (VRAM, models, etc.)"""
        async with await self.get_session() as session:
            async with session.get(f"{self.host}/system_stats") as resp:
                return await resp.json()
    
    async def get_models(self) -> Dict[str, Any]:
        """Get available models"""
        async with await self.get_session() as session:
            async with session.get(f"{self.host}/object_info") as resp:
                return await resp.json()
    
    async def queue_size(self) -> int:
        """Get current queue size"""
        async with await self.get_session() as session:
            async with session.get(f"{self.host}/queue") as resp:
                data = await resp.json()
                return len(data.get("queue_running", [])) + len(data.get("queue_pending", []))
    
    async def interrupt(self) -> bool:
        """Interrupt current execution"""
        async with await self.get_session() as session:
            async with session.post(f"{self.host}/interrupt") as resp:
                return resp.status == 200
    
    async def upload_image(self, image_path: str) -> Optional[str]:
        """Upload image to ComfyUI for video generation"""
        if not os.path.exists(image_path):
            return None
        
        filename = os.path.basename(image_path)
        async with await self.get_session() as session:
            with open(image_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("image", f, filename=filename)
                form.add_field("overwrite", "true")
                async with session.post(f"{self.host}/upload/image", data=form) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("name")
        return None
    
    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history"""
        async with await self.get_session() as session:
            async with session.get(f"{self.host}/history/{prompt_id}") as resp:
                return await resp.json()
    
    async def get_outputs(self, prompt_id: str) -> Dict[str, Any]:
        """Get outputs for a prompt"""
        history = await self.get_history(prompt_id)
        return history.get(prompt_id, {}).get("outputs", {})
    
    async def queue_prompt(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Queue a prompt for execution, returns prompt_id"""
        async with await self.get_session() as session:
            async with session.post(f"{self.host}/prompt", json={"prompt": workflow}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("prompt_id")
        return None
    
    # ============ WORKFLOW BUILDERS ============
    
    def build_image_workflow(
        self,
        prompt: str,
        model: str = "sd15",
        steps: int = 20,
        cfg: float = 7.0,
        sampler: str = "euler",
        width: int = 512,
        height: int = 512,
        seed: int = 42
    ) -> Dict[str, Any]:
        """Build SD 1.5 image generation workflow"""
        return {
            "1": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": "normal",
                    "model": [" comfyui_tools_h付费模型 none", [model]],
                    "positive": [prompt, []],
                    "negative": "",
                    "latent_image": [" empty_latent_image", []]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "empty_latent_image": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "save": {
                "inputs": {
                    "filename_prefix": f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "images": ["1", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            }
        }
    
    def build_video_workflow(
        self,
        prompt: str,
        image_path: str,
        model: str = "wan_14",
        frames: int = 24,
        seed: int = 42
    ) -> Dict[str, Any]:
        """Build Wan 2.2 video generation workflow"""
        # Simplified workflow - actual depends on installed nodes
        return {
            "load_image": {
                "inputs": {
                    "image": image_path
                },
                "class_type": "LoadImage",
                "_meta": {"title": "Load Image"}
            },
            "wan_video": {
                "inputs": {
                    "seed": seed,
                    "steps": 30,
                    "cfg": 7.0,
                    "prompt": prompt,
                    "image": ["load_image", 0],
                    "model": model,
                    "frames": frames
                },
                "class_type": "WanVideo",
                "_meta": {"title": "Wan Video Generation"}
            },
            "save_video": {
                "inputs": {
                    "filename_prefix": f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "video": ["wan_video", 0]
                },
                "class_type": "SaveVideo",
                "_meta": {"title": "Save Video"}
            }
        }


# Global service instance
comfyui_service = ComfyUIService()
