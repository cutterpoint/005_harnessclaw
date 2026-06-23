/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        base: {
          950: "#0a0a0b",
          900: "#111113",
          850: "#161618",
          800: "#1c1c1f",
          750: "#212125",
          700: "#26262a",
          600: "#34343a",
          500: "#45454d",
        },
        amber: {
          DEFAULT: "#f5a623",
          glow: "#ffb627",
          dim: "#b87b1a",
          dark: "#7a5212",
        },
        cyan: {
          DEFAULT: "#22d3ee",
          dim: "#0e7490",
          dark: "#155e75",
        },
        status: {
          success: "#34d399",
          warning: "#fbbf24",
          error: "#f87171",
          info: "#60a5fa",
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', "monospace"],
        sans: ['"Manrope"', '"Inter"', "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(245, 166, 35, 0.15)",
        "glow-sm": "0 0 12px rgba(245, 166, 35, 0.1)",
        "cyan-glow": "0 0 20px rgba(34, 211, 238, 0.12)",
        card: "0 4px 24px rgba(0, 0, 0, 0.4)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "scan": "scan 4s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
      },
    },
  },
  plugins: [],
};
