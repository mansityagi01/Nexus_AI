import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'
  const isProd = mode === 'production'

  return {
    plugins: [svelte()],
    build: {
      outDir: '../backend/web/static',
      emptyOutDir: true,
      minify: isProd ? 'esbuild' : false,
      sourcemap: isDev,
      rollupOptions: {
        output: {
          entryFileNames: isProd ? 'assets/[name].[hash].js' : 'bundle.js',
          chunkFileNames: isProd ? 'assets/[name].[hash].js' : 'bundle.js',
          assetFileNames: isProd ? 'assets/[name].[hash].[ext]' : 'bundle.[ext]',
          manualChunks: isProd ? {
            vendor: ['socket.io-client']
          } : undefined
        }
      },
      target: 'es2015',
      cssCodeSplit: isProd,
      assetsInlineLimit: isProd ? 4096 : 0
    },
    server: {
      port: 3000,
      proxy: {
        '/socket.io': {
          target: 'http://localhost:5000',
          ws: true
        }
      }
    },
    define: {
      __DEV__: isDev,
      __PROD__: isProd
    }
  }
})