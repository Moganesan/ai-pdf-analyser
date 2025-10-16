import type { NextConfig } from "next";

const backendUrl = (() => {
  if (process.env.NEXT_PUBLIC_BACKEND_URL) return process.env.NEXT_PUBLIC_BACKEND_URL;
  if (process.env.NEXT_PUBLIC_BACKEND_HOST) {
    const host = process.env.NEXT_PUBLIC_BACKEND_HOST;
    // Render web services expose standard HTTPS on default port
    return `https://${host}`;
  }
  return "http://localhost:8000";
})();

const nextConfig: NextConfig = {
  eslint: { ignoreDuringBuilds: true },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
