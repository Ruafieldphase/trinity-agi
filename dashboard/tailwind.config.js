/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                'trinity-bg': '#0a0a0f',
                'trinity-panel': '#1a1a2e',
                'trinity-accent': '#4a9eff',
                'trinity-success': '#00ff88',
                'trinity-warning': '#ffaa00',
                'trinity-error': '#ff4466',
                'trinity-urgent': '#ff6b6b',
                'trinity-calm': '#6bc5ff',
            },
        },
    },
    plugins: [],
}
