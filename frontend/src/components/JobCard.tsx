"use client";

import { Job, deleteJob } from "@/lib/api";
import { useState } from "react";

interface JobCardProps {
  job: Job;
  onClick: (job: Job) => void;
  onDelete?: (jobId: number) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function JobCard({ job, onClick, onDelete }: JobCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("¿Eliminar este job de la cola?")) return;
    
    setIsDeleting(true);
    try {
      await deleteJob(job.id);
      onDelete?.(job.id);
    } catch (err) {
      console.error("Failed to delete job:", err);
      alert("Error al eliminar job");
    } finally {
      setIsDeleting(false);
    }
  };

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
    <div
      onClick={() => onClick(job)}
      className="relative flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden bg-gray-700 border-2 border-gray-600 hover:border-blue-500 hover:scale-105 transition-all group cursor-pointer"
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
      
      {/* Delete button - appears on hover */}
      <div 
        className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleDelete}
      >
        <button 
          disabled={isDeleting}
          className="w-6 h-6 bg-red-600 hover:bg-red-500 rounded-full flex items-center justify-center text-xs"
          title="Eliminar"
        >
          {isDeleting ? "⏳" : "✕"}
        </button>
      </div>
    </div>
  );
}
