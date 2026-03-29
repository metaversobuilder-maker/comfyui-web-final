"use client";

import { Job } from "@/lib/api";

interface ImageModalProps {
  job: Job | null;
  onClose: () => void;
}

export default function ImageModal({ job, onClose }: ImageModalProps) {
  if (!job) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={onClose}
    >
      <div
        className="relative max-w-4xl w-full max-h-[90vh] bg-gray-900 rounded-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              {job.type === "image" ? "🖼️ Imagen" : "🎬 Video"}
              {job.model && <span className="text-sm px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded">📦 {job.model}</span>}
            </h2>
            <p className="text-sm text-gray-300 mt-1 font-mono bg-gray-800 px-2 py-1 rounded">{job.prompt}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-auto max-h-[calc(90vh-120px)]">
          {job.image_path && job.type === "image" && (
            <img
              src={`http://localhost:8000/api/images/${job.image_path}`}
              alt={job.prompt || ""}
              className="w-full h-auto rounded-lg"
            />
          )}
          
          {job.video_path && job.type === "video" && (
            <video
              src={`http://localhost:8000/api/videos/${job.video_path}`}
              controls
              className="w-full h-auto rounded-lg"
            >
              Tu navegador no soporta videos.
            </video>
          )}

          {!job.image_path && !job.video_path && job.status === "processing" && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500" />
              <p className="mt-4 text-gray-400">Procesando...</p>
            </div>
          )}

          {!job.image_path && !job.video_path && job.status === "pending" && (
            <div className="flex flex-col items-center justify-center py-20">
              <p className="text-4xl">⏳</p>
              <p className="mt-4 text-gray-400">En cola de espera...</p>
            </div>
          )}

          {job.status === "failed" && (
            <div className="flex flex-col items-center justify-center py-20">
              <p className="text-4xl">❌</p>
              <p className="mt-4 text-red-400">Error: {job.error_message || "Error desconocido"}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-700">
          <span className={`px-3 py-1 rounded-full text-sm ${
            job.status === "completed" ? "bg-green-500/20 text-green-400" :
            job.status === "failed" ? "bg-red-500/20 text-red-400" :
            job.status === "processing" ? "bg-blue-500/20 text-blue-400" :
            "bg-yellow-500/20 text-yellow-400"
          }`}>
            {job.status === "completed" && "✅ Completado"}
            {job.status === "failed" && "❌ Fallido"}
            {job.status === "processing" && "🔄 Procesando"}
            {job.status === "pending" && "⏳ Pendiente"}
          </span>
          <span className="text-sm text-gray-500">
            {job.created_at ? new Date(job.created_at).toLocaleString("es-ES") : ""}
          </span>
        </div>
      </div>
    </div>
  );
}
