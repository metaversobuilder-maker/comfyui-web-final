"use client";

import { useState, useEffect, useCallback } from "react";
import { Job, Stats, generateImage, generateVideo, getJobs, getStats } from "@/lib/api";
import JobCard from "@/components/JobCard";
import ImageModal from "@/components/ImageModal";

export default function PromptsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats>({ totalImages: 0, totalVideos: 0, pendingJobs: 0 });
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  
  // Image generation
  const [imagePrompt, setImagePrompt] = useState("");
  const [imageModel, setImageModel] = useState("zimage_lora");
  const [loadingImage, setLoadingImage] = useState(false);
  
  // Video generation  
  const [showVideoForm, setShowVideoForm] = useState(false);
  const [videoPrompt, setVideoPrompt] = useState("");
  const [videoModel, setVideoModel] = useState("wan2.2_smoothmix");
  const [selectedImage, setSelectedImage] = useState("");
  const [loadingVideo, setLoadingVideo] = useState(false);
  
  // Filters & pagination
  const [filter, setFilter] = useState<"all" | "image" | "video">("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [jobsResponse, statsData] = await Promise.all([getJobs(page), getStats()]);
      const jobsArray = Array.isArray(jobsResponse) ? jobsResponse : (jobsResponse.items || []);
      setJobs(jobsArray);
      setStats(statsData);
      // Estimate total pages
      setTotalPages(Math.ceil(jobsArray.length / 20) || 1);
    } catch (e) {
      console.error("Error fetching data:", e);
    }
  }, [page]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleGenerateImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imagePrompt.trim() || loadingImage) return;
    setLoadingImage(true);
    setError("");
    try {
      await generateImage(imagePrompt, imageModel);
      setImagePrompt("");
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Error al generar imagen");
    } finally {
      setLoadingImage(false);
    }
  };

  const handleGenerateVideo = async () => {
    if (!videoPrompt.trim() || !selectedImage || loadingVideo) return;
    setLoadingVideo(true);
    setError("");
    try {
      await generateVideo(videoPrompt, selectedImage, videoModel);
      setShowVideoForm(false);
      setVideoPrompt("");
      setSelectedImage("");
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Error al generar video");
    } finally {
      setLoadingVideo(false);
    }
  };

  const filteredJobs = jobs.filter(job => {
    if (filter === "all") return true;
    return job.type === filter;
  });

  const imageJobs = jobs.filter(j => j.type === "image" && j.status === "completed");

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <a href="/" className="text-2xl text-gray-400 hover:text-white">← Volver</a>
            <h1 className="text-4xl font-bold mt-2 flex items-center gap-3 bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              <span>🎯</span> Prompts para ComfyUI
            </h1>
            <p className="text-gray-400 mt-1">Generación de imágenes y videos con IA</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchData()}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-lg font-medium transition-all"
            >
              🔄 Refresh
            </button>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
            >
              <option value="all">Todos</option>
              <option value="image">Imágenes</option>
              <option value="video">Videos</option>
            </select>
            {stats.pendingJobs > 0 && (
              <span className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full text-sm font-medium animate-pulse">
                🔄 {stats.pendingJobs} en cola
              </span>
            )}
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-3 gap-4 bg-gray-800/30 rounded-xl p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{stats.totalImages}</div>
            <div className="text-sm text-gray-400">Imágenes</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{stats.totalVideos}</div>
            <div className="text-sm text-gray-400">Videos</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{stats.pendingJobs}</div>
            <div className="text-sm text-gray-400">Pendientes</div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-400">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Generator Forms */}
          <div className="lg:col-span-2 space-y-6">
            {/* Image Generator */}
            <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                🖼️ Generar Imagen
              </h2>
              <form onSubmit={handleGenerateImage} className="space-y-4">
                <textarea
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  placeholder="Describe la imagen que quieres generar..."
                  className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={3}
                />
                <select
                  value={imageModel}
                  onChange={(e) => setImageModel(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="zimage_lora">Zimage Lora</option>
                  <option value="zimage_red">Zimage Red</option>
                  <option value="mainpage">MainPage</option>
                </select>
                <button
                  type="submit"
                  disabled={loadingImage || !imagePrompt.trim()}
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-medium transition-all"
                >
                  {loadingImage ? "⏳ Generando..." : "🎨 Generar Imagen"}
                </button>
              </form>
            </div>

            {/* Video Generator */}
            <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                🎬 Generar Video
              </h2>
              
              {!showVideoForm ? (
                <button
                  onClick={() => setShowVideoForm(true)}
                  className="w-full py-3 bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-500 hover:to-teal-500 rounded-xl font-medium transition-all"
                >
                  🎬 Generar Video
                </button>
              ) : (
                <div className="space-y-4">
                  {/* Image Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Seleccionar imagen base
                    </label>
                    <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-2 bg-gray-800 rounded-lg">
                      {imageJobs.length === 0 ? (
                        <p className="text-gray-500 text-sm">No hay imágenes disponibles</p>
                      ) : (
                        imageJobs.map((img) => (
                          <button
                            key={img.id}
                            type="button"
                            onClick={() => setSelectedImage(img.image_path || "")}
                            className={`relative w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                              selectedImage === img.image_path
                                ? "border-blue-500 ring-2 ring-blue-500/50"
                                : "border-gray-700 hover:border-gray-500"
                            }`}
                          >
                            {img.image_path && (
                              <img
                                src={`http://localhost:8000/api/images/${img.image_path}`}
                                alt=""
                                className="w-full h-full object-cover"
                              />
                            )}
                          </button>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Video Model */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Modelo de Video</label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setVideoModel("wan2.2_smoothmix")}
                        className={`flex-1 py-2 px-3 rounded-lg border-2 transition-all ${
                          videoModel === "wan2.2_smoothmix"
                            ? "border-purple-500 bg-purple-500/20 text-white"
                            : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-500"
                        }`}
                      >
                        ✨ Wan 2.2 SmoothMix
                      </button>
                      <button
                        type="button"
                        onClick={() => setVideoModel("openart")}
                        className={`flex-1 py-2 px-3 rounded-lg border-2 transition-all ${
                          videoModel === "openart"
                            ? "border-purple-500 bg-purple-500/20 text-white"
                            : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-500"
                        }`}
                      >
                        🎨 OpenArt
                      </button>
                    </div>
                  </div>

                  {/* Video Prompt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Prompt para video
                    </label>
                    <textarea
                      value={videoPrompt}
                      onChange={(e) => setVideoPrompt(e.target.value)}
                      placeholder="Describe el movimiento que quieres generar..."
                      className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 resize-none"
                      rows={2}
                    />
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleGenerateVideo}
                      disabled={loadingVideo || !videoPrompt.trim() || !selectedImage}
                      className="flex-1 py-3 bg-gradient-to-r from-green-600 to-teal-600 disabled:opacity-50 rounded-xl font-medium"
                    >
                      {loadingVideo ? "⏳ Generando..." : "🎬 Generar Video"}
                    </button>
                    <button
                      onClick={() => { setShowVideoForm(false); setVideoPrompt(""); setSelectedImage(""); }}
                      className="px-4 py-3 bg-gray-700 rounded-xl hover:bg-gray-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Recent Jobs */}
          <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">📋 Últimos Trabajos</h2>
            </div>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {filteredJobs.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No hay trabajos aún</p>
              ) : (
                filteredJobs.map((job) => (
                  <JobCard 
                    key={job.id} 
                    job={job} 
                    onClick={() => setSelectedJob(job)}
                    onDelete={(id) => setJobs(jobs.filter(j => j.id !== id))}
                  />
                ))
              )}
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 bg-gray-700 rounded-lg disabled:opacity-50"
                >
                  ←
                </button>
                <span className="text-gray-400">{page} / {totalPages}</span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 bg-gray-700 rounded-lg disabled:opacity-50"
                >
                  →
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Modal */}
        {selectedJob && (
          <ImageModal job={selectedJob} onClose={() => setSelectedJob(null)} />
        )}
      </div>
    </div>
  );
}