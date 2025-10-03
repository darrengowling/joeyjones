/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
  	extend: {
  		fontFamily: {
  			sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
  			mono: ['SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'monospace']
  		},
  		borderRadius: {
  			sm: 'var(--radius-sm)',
  			DEFAULT: 'var(--radius-base)',
  			md: 'var(--radius-md)',
  			lg: 'var(--radius-lg)',
  			xl: 'var(--radius-xl)'
  		},
  		colors: {
  			/* Brand Colors */
  			brand: {
  				primary: {
  					50: 'var(--brand-primary-50)',
  					100: 'var(--brand-primary-100)',
  					200: 'var(--brand-primary-200)',
  					300: 'var(--brand-primary-300)',
  					400: 'var(--brand-primary-400)',
  					500: 'var(--brand-primary-500)',
  					600: 'var(--brand-primary-600)',
  					700: 'var(--brand-primary-700)',
  					800: 'var(--brand-primary-800)',
  					900: 'var(--brand-primary-900)',
  					950: 'var(--brand-primary-950)',
  					DEFAULT: 'var(--brand-primary-600)'
  				},
  				secondary: {
  					50: 'var(--brand-secondary-50)',
  					100: 'var(--brand-secondary-100)',
  					200: 'var(--brand-secondary-200)',
  					300: 'var(--brand-secondary-300)',
  					400: 'var(--brand-secondary-400)',
  					500: 'var(--brand-secondary-500)',
  					600: 'var(--brand-secondary-600)',
  					700: 'var(--brand-secondary-700)',
  					800: 'var(--brand-secondary-800)',
  					900: 'var(--brand-secondary-900)',
  					950: 'var(--brand-secondary-950)',
  					DEFAULT: 'var(--brand-secondary-500)'
  				},
  				accent: {
  					50: 'var(--brand-accent-50)',
  					100: 'var(--brand-accent-100)',
  					200: 'var(--brand-accent-200)',
  					300: 'var(--brand-accent-300)',
  					400: 'var(--brand-accent-400)',
  					500: 'var(--brand-accent-500)',
  					600: 'var(--brand-accent-600)',
  					700: 'var(--brand-accent-700)',
  					800: 'var(--brand-accent-800)',
  					900: 'var(--brand-accent-900)',
  					950: 'var(--brand-accent-950)',
  					DEFAULT: 'var(--brand-accent-500)'
  				},
  				neutral: {
  					50: 'var(--brand-neutral-50)',
  					100: 'var(--brand-neutral-100)',
  					200: 'var(--brand-neutral-200)',
  					300: 'var(--brand-neutral-300)',
  					400: 'var(--brand-neutral-400)',
  					500: 'var(--brand-neutral-500)',
  					600: 'var(--brand-neutral-600)',
  					700: 'var(--brand-neutral-700)',
  					800: 'var(--brand-neutral-800)',
  					900: 'var(--brand-neutral-900)',
  					950: 'var(--brand-neutral-950)',
  					DEFAULT: 'var(--brand-neutral-600)'
  				},
  				success: 'var(--brand-success)',
  				warning: 'var(--brand-warning)', 
  				error: 'var(--brand-error)',
  				info: 'var(--brand-info)'
  			},
  			
  			/* Semantic Colors */
  			background: 'var(--background)',
  			foreground: 'var(--foreground)',
  			card: {
  				DEFAULT: 'var(--card)',
  				foreground: 'var(--card-foreground)'
  			},
  			surface: {
  				DEFAULT: 'var(--surface)',
  				foreground: 'var(--surface-foreground)'
  			},
  			primary: {
  				DEFAULT: 'var(--primary)',
  				foreground: 'var(--primary-foreground)'
  			},
  			secondary: {
  				DEFAULT: 'var(--secondary)',
  				foreground: 'var(--secondary-foreground)'
  			},
  			accent: {
  				DEFAULT: 'var(--accent)',
  				foreground: 'var(--accent-foreground)'
  			},
  			muted: {
  				DEFAULT: 'var(--muted)',
  				foreground: 'var(--muted-foreground)'
  			},
  			border: 'var(--border)',
  			input: 'var(--input)',
  			ring: 'var(--ring)'
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};