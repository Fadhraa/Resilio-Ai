/** @type {import('next').NextConfig} */
const nextConfig = {
  // Menonaktifkan floating dev indicator / watermark "N" di pojok layar
  devIndicators: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
