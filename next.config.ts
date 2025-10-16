import type { NextConfig } from "next";

const backendUrl = (() => {
  if (process.env.NEXT_PUBLIC_BACKEND_URL) return process.env.NEXT_PUBLIC_BACKEND_URL;
  if (process.env.NEXT_PUBLIC_BACKEND_HOST) {
    const host = process.env.NEXT_PUBLIC_BACKEND_HOST;
    const port = process.env.NEXT_PUBLIC_BACKEND_PORT;
    // Render web services are HTTPS by default
    return `https://${host}${port ? `:${port}` : ''}`;
  }
  return "http://localhost:8000";
})();

const nextConfig: NextConfig = {
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
