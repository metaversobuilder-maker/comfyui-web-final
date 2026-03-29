"use client";

import { useState, useEffect } from "react";
import { getStats, getJobs } from "@/lib/api";

export default function Home() {
  const [stats, setStats] = useState({ totalImages: 0, totalVideos: 0, pendingJobs: 0 });
  const [recentJobs, setRecentJobs] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsData, jobsData] = await Promise.all([getStats(), getJobs()]);
      setStats(statsData);
      setRecentJobs(jobsData.items.slice(0, 6));
    } catch (e) {
      console.error("Error:", e);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="max-w-6xl mx-auto p-6 space-y-8">
        
        {/* Header */}
        <div className="text-center py-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-4">
            🎨 ComfyUI Web
          </h1>
          <p className="text-xl text-gray-400">Tu panel de herramientas de IA</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-6">
          <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50 text-center">
            <div className="text-4xl mb-2">🖼️</div>
            <div className="text-3xl font-bold">{stats.totalImages}</div>
            <div className="text-gray-400">Imágenes</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50 text-center">
            <div className="text-4xl mb-2">🎬</div>
            <div className="text-3xl font-bold">{stats.totalVideos}</div>
            <div className="text-gray-400">Videos</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50 text-center">
            <div className="text-4xl mb-2">⏳</div>
            <div className="text-3xl font-bold">{stats.pendingJobs}</div>
            <div className="text-gray-400">Pendientes</div>
          </div>
        </div>

        {/* Tools Grid */}
        <div>
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <span>🛠️</span> Herramientas
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Prompts Tool */}
            <a href="/prompts" className="group bg-gray-800/50 backdrop-blur rounded-2xl p-6 border border-gray-700/50 hover:border-blue-500 transition-all hover:scale-105">
              <div className="text-5xl mb-4">🎯</div>
              <h3 className="text-xl font-bold mb-2 group-hover:text-blue-400">Prompts</h3>
              <p className="text-gray-400">Genera imágenes y videos con modelos de IA</p>
            </a>

            {/* Coming Soon */}
            <div className="bg-gray-800/30 backdrop-blur rounded-2xl p-6 border border-gray-700/30 opacity-50">
              <div className="text-5xl mb-4">🔄</div>
              <h3 className="text-xl font-bold mb-2">Workflows</h3>
              <p className="text-gray-500">Próximamente...</p>
            </div>

            {/* Coming Soon */}
            <div className="bg-gray-800/30 backdrop-blur rounded-2xl p-6 border border-gray-700/30 opacity-50">
              <div className="text-5xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">Estadísticas</h3>
              <p className="text-gray-500">Próximamente...</p>
            </div>

          </div>
        </div>

        {/* Recent Activity */}
        {recentJobs.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <span>📋</span> Actividad Reciente
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {recentJobs.map(job => (
                <a key={job.id} href={`/prompts`} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700 hover:border-blue-500 transition-all">
                  <div className="text-2xl mb-2">{job.type === "image" ? "🖼️" : "🎬"}</div>
                  <div className="text-sm text-gray-400 truncate">{job.prompt?.substring(0, 30)}...</div>
                  <div className={`text-xs mt-2 ${job.status === "completed" ? "text-green-400" : job.status === "failed" ? "text-red-400" : "text-yellow-400"}`}>
                    {job.status === "completed" ? "✅" : job.status === "failed" ? "❌" : "⏳"} {job.status}
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-gray-500 py-8">
          <p>ComfyUI Web v1.0 • Powered by OpenClaw</p>
        </div>

      </div>
    </div>
  );
}