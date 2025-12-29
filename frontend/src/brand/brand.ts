// Friends of PIFA Brand System
export const brandTokens = {
  name: "Friends of PIFA",
  
  colors: {
    // Primary brand colors (UEFA-inspired blues)
    primary: {
      50: "#eff6ff",
      100: "#dbeafe", 
      200: "#bfdbfe",
      300: "#93c5fd",
      400: "#60a5fa",
      500: "#3b82f6", // Main brand blue
      600: "#2563eb",
      700: "#1d4ed8",
      800: "#1e40af",
      900: "#1e3a8a",
      950: "#172554"
    },
    
    // Secondary colors (Football green)
    secondary: {
      50: "#f0fdf4",
      100: "#dcfce7",
      200: "#bbf7d0", 
      300: "#86efac",
      400: "#4ade80",
      500: "#22c55e", // Football green
      600: "#16a34a",
      700: "#15803d",
      800: "#166534",
      900: "#14532d",
      950: "#052e16"
    },
    
    // Accent colors (Gold/Yellow for highlights)
    accent: {
      50: "#fefce8",
      100: "#fef9c3",
      200: "#fef08a",
      300: "#fde047",
      400: "#facc15",
      500: "#eab308", // Gold
      600: "#ca8a04",
      700: "#a16207",
      800: "#854d0e",
      900: "#713f12",
      950: "#422006"
    },
    
    // Neutral grays
    neutral: {
      50: "#f8fafc",
      100: "#f1f5f9",
      200: "#e2e8f0",
      300: "#cbd5e1", 
      400: "#94a3b8",
      500: "#64748b",
      600: "#475569",
      700: "#334155",
      800: "#1e293b",
      900: "#0f172a",
      950: "#020617"
    },
    
    // Status colors
    success: "#22c55e",
    warning: "#eab308", 
    error: "#ef4444",
    info: "#3b82f6"
  },
  
  radii: {
    none: "0px",
    sm: "0.25rem",    // 4px
    base: "0.375rem", // 6px
    md: "0.5rem",     // 8px
    lg: "0.75rem",    // 12px
    xl: "1rem",       // 16px
    "2xl": "1.5rem",  // 24px
    full: "9999px"
  },
  
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      mono: ['SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'monospace']
    }
  }
};

export type BrandTokens = typeof brandTokens;