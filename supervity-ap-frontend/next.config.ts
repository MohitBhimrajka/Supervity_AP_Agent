import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Ignore canvas when bundling for the browser
    if (!isServer) {
      config.resolve = config.resolve || {};
      config.resolve.fallback = config.resolve.fallback || {};
      config.resolve.fallback.canvas = false;
      config.resolve.fallback.encoding = false;
    }
    
    return config;
  },
};

export default nextConfig;
