import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    // Every interface, not just loopback, so a phone on the same network can
    // load the dev server. Safe-area insets, dvh and touch behaviour don't
    // show up in a resized desktop window.
    host: true,

    // In production vercel.json rewrites /api to the backend service. Locally
    // the two servers are separate origins, so proxy to keep them one origin,
    // otherwise the session cookie won't be sent.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
