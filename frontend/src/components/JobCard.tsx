"use client";

import { Job } from "@/lib/api";

interface JobCardProps {
  job: Job;
  onClick: (job: Job) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function JobCard({ job, onClick }: JobCardProps) {
  const statusColors = {
    pending: "bg-yellow-500",
    processing: "bg-blue-500 animate-pulse",
    completed: "bg-green-500",
    failed: "bg-red-500",
  };

  const statusLabels = {
    pending: "Pendiente",
    processing: "Procesando",
    completed: "Completado",
    failed: "Error",
  };

  const typeIcon = job.type === "image" ? "🖼️" : "🎬";
  
  // Get image URL - check multiple possible fields
  const imageUrl = job.image_path 
    ? `${API_BASE}/api/images/${job.image_path}`
    : job.video_path
      ? `${API_BASE}/api/videos/${job.video_path}`
      : null;

  return (
    <button
      onClick={() => onClick(job)}
      className="relative flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden bg-gray-700 border-2 border-gray-600 hover:border-blue-500 hover:scale-105 transition-all group"
    >
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={job.prompt || "Job"}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-700">
          <span className="text-2xl">{typeIcon}</span>
        </div>
      )}
      
      {/* Status indicator */}
      <div
        className={`absolute bottom-1 right-1 w-3 h-3 rounded-full ${statusColors[job.status]} border-2 border-gray-900`}
        title={statusLabels[job.status]}
      />
      
      {/* Type badge */}
      <div className="absolute top-1 left-1 bg-black/50 px-1.5 py-0.5 rounded text-xs">
        {typeIcon}
      </div>
    </button>
  );
}
