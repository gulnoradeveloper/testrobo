import animate from "tailwindcss-animate";
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: { center: true, padding: "1rem", screens: { "2xl": "1240px" } },
    extend: {
      colors: {
        primary: { DEFAULT: "#123A63", foreground: "#FFFFFF" },
        accent: { DEFAULT: "#1877C9", foreground: "#FFFFFF", soft: "#E8F1FB" },
        background: "#F6F9FC",
        card: "#FFFFFF",
        ink: "#172B4D",
        muted: { DEFAULT: "#66788A", bg: "#EEF3F8" },
        border: "#E1E8F0",
        success: { DEFAULT: "#168A61", soft: "#E6F4EE" },
        warning: { DEFAULT: "#D99726", soft: "#FBF3E4" },
        danger: { DEFAULT: "#DC3545", soft: "#FCECEE" },
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "-apple-system", '"Segoe UI"', "Roboto", "Arial", "sans-serif"],
      },
      borderRadius: { lg: "12px", md: "8px", sm: "6px" },
      boxShadow: { card: "0 1px 2px rgba(18,58,99,0.04), 0 4px 16px rgba(18,58,99,0.06)" },
      keyframes: { "fade-in": { from: { opacity: "0", transform: "translateY(4px)" }, to: { opacity: "1", transform: "none" } } },
      animation: { "fade-in": "fade-in .25s ease-out" },
    },
  },
  plugins: [animate],
};
