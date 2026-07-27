import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // CloudOps AI palette: mission-control dark, not the generic
        // cream/terracotta AI-tool default. Named after their ops role.
        void: "#0B0E14",       // page background
        panel: "#12151C",      // card / panel surface
        panelBorder: "#232733",
        signal: "#4FD1C5",     // healthy / active cyan
        warn: "#F5A623",       // medium severity amber
        critical: "#EF4444",   // critical severity red
        ink: "#E6E8EB",        // primary text
        faint: "#8B93A1",      // muted text
      },
      fontFamily: {
        mono: ["'IBM Plex Mono'", "monospace"],
        sans: ["'Inter'", "sans-serif"],
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        pulseSignal: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
      animation: {
        scan: "scan 2.2s linear infinite",
        pulseSignal: "pulseSignal 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
