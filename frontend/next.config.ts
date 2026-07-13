import type { NextConfig } from "next";
import path from 'path';

const nextConfig: NextConfig = {
  /* config options here */
  turbopack: {
    // Locks module resolution to the frontend folder only
    root: path.join(__dirname),
  },
};

export default nextConfig;