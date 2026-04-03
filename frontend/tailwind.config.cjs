const path = require("node:path");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    path.join(__dirname, "apps/**/*.{vue,ts,tsx,js,jsx,html}"),
    path.join(__dirname, "packages/**/*.{vue,ts,tsx,js,jsx}")
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0f766e",
          light: "#14b8a6",
          dark: "#115e59"
        }
      }
    }
  },
  plugins: []
};
