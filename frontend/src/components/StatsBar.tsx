"use client";

import { Stats } from "@/lib/api";

interface StatsBarProps {
  stats: Stats;
}

export default function StatsBar({ stats }: StatsBarProps) {
  return (
    <div className="flex gap-4 p-4 bg-gray-800 rounded-lg">
      <div className="flex items-center gap-2">
        <span className="text-2xl">🖼️</span>
        <div>
          <p className="text-2xl font-bold text-white">{stats.totalImages}</p>
          <p className="text-sm text-gray-400">Imágenes</p>
        </div>
      </div>
      
      <div className="w-px bg-gray-700" />
      
      <div className="flex items-center gap-2">
        <span className="text-2xl">🎬</span>
        <div>
          <p className="text-2xl font-bold text-white">{stats.totalVideos}</p>
          <p className="text-sm text-gray-400">Videos</p>
        </div>
      </div>
      
      <div className="w-px bg-gray-700" />
      
      <div className="flex items-center gap-2">
        <span className="text-2xl">⏳</span>
        <div>
          <p className="text-2xl font-bold text-yellow-500">{stats.pendingJobs}</p>
          <p className="text-sm text-gray-400">Pendientes</p>
        </div>
      </div>
    </div>
  );
}
