import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ComfyUI Web",
  description: "Generación de imágenes y videos con ComfyUI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen bg-gray-900 text-white">
        {children}
      </body>
    </html>
  );
}
