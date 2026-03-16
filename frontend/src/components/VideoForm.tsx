"use client";

import { useState } from "react";
import { Job, generateVideo } from "@/lib/api";

interface VideoFormProps {
  images: Job[];
  onSubmit: (prompt: string, imageId: string) => Promise<void>;
  disabled?: boolean;
}

export default function VideoForm({ images, onSubmit, disabled }: VideoFormProps) {
  const [prompt, setPrompt] = useState("");
  const [selectedImage, setSelectedImage] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const imageJobs = images.filter((j) => j.type === "image" && j.status === "completed");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !selectedImage || loading || disabled) return;

    setLoading(true);
    try {
      await onSubmit(prompt, selectedImage);
      setPrompt("");
      setSelectedImage("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Seleccionar imagen
        </label>
        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-gray-800 rounded-lg">
          {imageJobs.length === 0 ? (
            <p className="text-gray-500 text-sm">No hay imágenes disponibles</p>
          ) : (
            imageJobs.map((img) => (
              <button
                key={img.id}
                type="button"
                onClick={() => setSelectedImage(String(img.id))}
                disabled={disabled}
                className={`relative w-16 h-16 rounded-lg overflow-hidden border-2 transition-all ${
                  selectedImage === String(img.id)
                    ? "border-blue-500 ring-2 ring-blue-500/50"
                    : "border-gray-700 hover:border-gray-500"
                } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                {img.image_path ? (
                  <img
                    src={`http://localhost:8000/api/images/${img.image_path}`}
                    alt={img.prompt || ""}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-700">
                    🖼️
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Prompt para video
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe el movimiento que quieres generar..."
          disabled={disabled || !selectedImage}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 resize-none"
          rows={2}
        />
      </div>

      <button
        type="submit"
        disabled={!prompt.trim() || !selectedImage || loading || disabled}
        className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="animate-spin">⏳</span>
            Generando...
          </>
        ) : (
          <>
            🎬 Generar Video
          </>
        )}
      </button>
    </form>
  );
}
