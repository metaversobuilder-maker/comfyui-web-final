"use client";

import { useEffect, useState, useCallback } from "react";
import { Job, Stats, generateImage, generateVideo, getJobs, getStats, connectWebSocket } from "@/lib/api";
import JobCard from "@/components/JobCard";
import StatsBar from "@/components/StatsBar";
import ImageModal from "@/components/ImageModal";
import VideoForm from "@/components/VideoForm";

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats>({ totalImages: 0, totalVideos: 0, pendingJobs: 0 });
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [imagePrompt, setImagePrompt] = useState("");
  const [loadingImage, setLoadingImage] = useState(false);
  const [loadingVideo, setLoadingVideo] = useState(false);
  const [wsError, setWsError] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [filter, setFilter] = useState<"all" | "image" | "video">("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchData = useCallback(async () => {
    try {
      const [jobsResponse, statsData] = await Promise.all([getJobs(page), getStats()]);
      const jobsArray = Array.isArray(jobsResponse) ? jobsResponse : (jobsResponse.items || []);
      setJobs(jobsArray);
      setStats(statsData);
      setWsError(false);
      // @ts-ignore
      if (jobsResponse.pages) setTotalPages(jobsResponse.pages);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    }
  }, [page]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    let ws: WebSocket | null = null;

    const initWs = () => {
      ws = connectWebSocket(
        (data: Job) => {
          setJobs((prev) => {
            const idx = prev.findIndex((j) => j.id === data.id);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = data;
              return updated;
            }
            return [data, ...prev];
          });
          fetchData();
        },
        () => {
          setWsError(true);
        }
      );
    };

    initWs();

    return () => {
      ws?.close();
    };
  }, [fetchData]);

  const handleGenerateImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imagePrompt.trim() || loadingImage) return;

    setLoadingImage(true);
    try {
      await generateImage(imagePrompt);
      setImagePrompt("");
      await fetchData();
    } catch (err) {
      console.error("Failed to generate image:", err);
      alert("Error al generar imagen");
    } finally {
      setLoadingImage(false);
    }
  };

  const handleGenerateVideo = async (prompt: string, imageId: string) => {
    setLoadingVideo(true);
    try {
      await generateVideo(prompt, imageId);
      await fetchData();
    } catch (err) {
      console.error("Failed to generate video:", err);
      alert("Error al generar video");
    } finally {
      setLoadingVideo(false);
    }
  };

  const filteredJobs = jobs.filter(job => {
    if (filter === "all") return true;
    return job.type === filter;
  });

  const pendingJobs = jobs.filter(j => j.status === "pending" || j.status === "processing");

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <h1 className="text-4xl font-bold flex items-center gap-3">
            <span className="text-5xl">🎨</span>
            ComfyUI Web
          </h1>
          <div className="flex items-center gap-3">
            {wsError && (
              <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-sm flex items-center gap-2">
                ⚠️ WebSocket
              </span>
            )}
            {pendingJobs.length > 0 && (
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                🔄 {pendingJobs.length} en cola
              </span>
            )}
          </div>
        </div>

        {/* Stats */}
        <StatsBar stats={stats} />

        {/* Forms */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Generate Image */}
          <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              🖼️ Generar Imagen
            </h2>
            <form onSubmit={handleGenerateImage} className="space-y-4">
              <textarea
                value={imagePrompt}
                onChange={(e) => setImagePrompt(e.target.value)}
                placeholder="Describe la imagen que quieres generar..."
                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
              />
              <button
                type="submit"
                disabled={!imagePrompt.trim() || loadingImage}
                className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 disabled:from-gray-600 disabled:to-gray-700 text-white font-medium rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg"
              >
                {loadingImage ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Generando...
                  </>
                ) : (
                  <>
                    ✨ Generar Imagen
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Generate Video */}
          <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              🎬 Generar Video
            </h2>
            <VideoForm
              images={jobs}
              onSubmit={handleGenerateVideo}
              disabled={loadingVideo}
            />
          </div>
        </div>

        {/* Jobs Section */}
        <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50">
          {/* Controls */}
          <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              📋 Historial
              <span className="text-sm font-normal text-gray-400">
                ({filteredJobs.length} jobs)
              </span>
            </h2>
            
            <div className="flex items-center gap-3">
              {/* Filter */}
              <div className="flex bg-gray-900/50 rounded-lg p-1">
                {(["all", "image", "video"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-3 py-1 rounded-md text-sm transition-colors ${
                      filter === f 
                        ? "bg-blue-600 text-white" 
                        : "text-gray-400 hover:text-white"
                    }`}
                  >
                    {f === "all" ? "Todos" : f === "image" ? "🖼️" : "🎬"}
                  </button>
                ))}
              </div>

              {/* View Toggle */}
              <div className="flex bg-gray-900/50 rounded-lg p-1">
                <button
                  onClick={() => setViewMode("grid")}
                  className={`px-3 py-1 rounded-md transition-colors ${viewMode === "grid" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"}`}
                >
                  ▦
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={`px-3 py-1 rounded-md transition-colors ${viewMode === "list" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"}`}
                >
                  ☰
                </button>
              </div>
            </div>
          </div>
          
          {filteredJobs.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <p className="text-6xl mb-4">📭</p>
              <p className="text-xl">No hay jobs</p>
              <p className="text-sm mt-2">Genera una imagen o video para comenzar</p>
            </div>
          ) : viewMode === "grid" ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
              {filteredJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onClick={setSelectedJob}
                />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredJobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job)}
                  className="w-full flex items-center gap-4 p-3 bg-gray-900/50 hover:bg-gray-700/50 rounded-xl transition-colors text-left"
                >
                  <div className="w-12 h-12 rounded-lg bg-gray-700 flex items-center justify-center text-xl flex-shrink-0 overflow-hidden">
                    {job.image_path ? (
                      <img 
                        src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/images/${job.image_path}`}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      job.type === "image" ? "🖼️" : "🎬"
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{job.prompt || "Sin prompt"}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(job.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    job.status === "completed" ? "bg-green-500/20 text-green-400" :
                    job.status === "processing" ? "bg-blue-500/20 text-blue-400" :
                    job.status === "pending" ? "bg-yellow-500/20 text-yellow-400" :
                    "bg-red-500/20 text-red-400"
                  }`}>
                    {job.status}
                  </span>
                </button>
              ))}
            </div>
          )}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6 pt-4 border-t border-gray-700">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm"
              >
                ◀
              </button>
              <span className="px-3 py-1 text-sm text-gray-400">
                Página {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm"
              >
                ▶
              </button>
            </div>
          )}
        </div>
      </div>

      <ImageModal job={selectedJob} onClose={() => setSelectedJob(null)} />
    </div>
  );
}
