const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Job {
  id: number;
  type: "image" | "video";
  status: "pending" | "processing" | "completed" | "failed";
  payload?: string;
  prompt?: string;
  image_path?: string;
  video_path?: string;
  progress?: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface Stats {
  totalImages: number;
  totalVideos: number;
  pendingJobs: number;
}

export async function generateImage(prompt: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      type: "image",
      prompt: prompt,
      payload: JSON.stringify({ prompt })
    }),
  });
  if (!res.ok) throw new Error("Failed to generate image");
  return res.json();
}

export async function generateVideo(
  prompt: string,
  imageFilename: string
): Promise<Job> {
  const res = await fetch(`${API_BASE}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      type: "video",
      prompt: prompt,
      payload: JSON.stringify({ prompt, image: imageFilename })
    }),
  });
  if (!res.ok) throw new Error("Failed to generate video");
  return res.json();
}

export async function getJobs(page: number = 1): Promise<{ items: Job[]; total: number; page: number; pages: number }> {
  const res = await fetch(`${API_BASE}/api/jobs?page=${page}&limit=20`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch jobs");
  return res.json();
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/api/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function getJob(jobId: number): Promise<Job> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch job");
  return res.json();
}

export function connectWebSocket(
  onMessage: (data: any) => void,
  onError?: (error: Event) => void
): WebSocket {
  const ws = new WebSocket(`${API_BASE.replace("http", "ws")}/ws/jobs`);
  
  ws.onopen = () => {
    console.log("WebSocket connected");
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("Failed to parse WebSocket message", e);
    }
  };
  
  ws.onerror = (error) => {
    console.error("WebSocket error", error);
    onError?.(error);
  };
  
  return ws;
}
