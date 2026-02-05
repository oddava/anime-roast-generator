import { defineConfig, loadEnv, splitVendorChunkPlugin } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on mode
  const env = loadEnv(mode, process.cwd(), '')
  const apiUrl = env.VITE_API_URL || 'http://localhost:8000'

  return {
    plugins: [
      react({
        // Enable Fast Refresh for faster development
        include: '**/*.{jsx,tsx}',
        // Use automatic JSX runtime (already default in React 18)
        jsxRuntime: 'automatic',
      }),
      splitVendorChunkPlugin(), // Automatic vendor chunk splitting
    ],
    
    // Pre-bundle dependencies to speed up cold starts
    optimizeDeps: {
      // Force pre-bundling of heavy dependencies
      include: [
        'react',
        'react-dom',
        'recharts',
        'lucide-react',
      ],
      // Exclude problematic dependencies if any
      exclude: [],
      // Enable esbuild-based dependency optimization (faster)
      esbuildOptions: {
        target: 'es2020',
      },
    },

    // Build configuration for faster production builds
    build: {
      outDir: 'dist',
      // Enable source maps only in development
      sourcemap: mode === 'development',
      // Use esbuild for minification (faster than terser)
      minify: 'esbuild',
      // Enable CSS code splitting
      cssCodeSplit: true,
      // Rollup options for advanced optimizations
      rollupOptions: {
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            // React ecosystem in one chunk
            'react-vendor': ['react', 'react-dom'],
            // Charts library (heavy) in its own chunk
            'charts': ['recharts'],
            // Icons in their own chunk
            'icons': ['lucide-react'],
          },
          // Optimize chunk file naming for caching
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name)) {
              return 'assets/images/[name]-[hash][extname]'
            }
            if (/\.(css)$/i.test(assetInfo.name)) {
              return 'assets/css/[name]-[hash][extname]'
            }
            return 'assets/[name]-[hash][extname]'
          },
        },
      },
      // Target modern browsers for smaller bundles
      target: 'es2020',
      // Enable build report for analysis (optional)
      reportCompressedSize: false, // Faster builds, disable if not needed
    },

    // Development server configuration
    server: {
      port: 3000,
      host: true,
      // Enable faster HMR
      hmr: {
        overlay: false, // Disable error overlay for faster updates
      },
      // Optimize dependency pre-bundling in dev
      preTransformRequests: true,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
        },
      },
    },

    // Esbuild configuration for faster transforms
    esbuild: {
      // Drop console and debugger in production
      drop: mode === 'production' ? ['console', 'debugger'] : [],
      // Target modern JavaScript
      target: 'es2020',
    },

    // Dependency optimization cache
    cacheDir: '.vite_cache',
  }
})
