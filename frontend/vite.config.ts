import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
      manifest: {
        name: 'Yoga Sutras of Patanjali',
        short_name: 'Yoga Sutras',
        description: 'A Sanskrit reading platform for the Yoga Sutras of Patanjali with sandhi splitting, dictionary lookup, and offline support.',
        theme_color: '#7c3aed',
        background_color: '#faf5ff',
        display: 'standalone',
        orientation: 'portrait-primary',
        scope: '/',
        start_url: '/',
        categories: ['education', 'books', 'reference'],
        lang: 'en',
        icons: [
          {
            src: 'pwa-64x64.png',
            sizes: '64x64',
            type: 'image/png'
          },
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: 'maskable-icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ]
      },
      workbox: {
        // Pre-cache app shell
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],

        // Runtime caching for API calls
        runtimeCaching: [
          {
            // Cache Google Fonts stylesheets
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-stylesheets',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              }
            }
          },
          {
            // Cache Google Fonts webfont files
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-webfonts',
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Cache text/section data - these don't change often
            urlPattern: /\/api\/texts(?:\/[^/]+)?(?:\/section\/[^/]+)?$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'sutras-data',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 7 // 1 week
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Cache individual block data
            urlPattern: /\/api\/texts\/[^/]+\/block\/\d+$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'sutras-blocks',
              expiration: {
                maxEntries: 250, // All 196 sutras + buffer
                maxAgeSeconds: 60 * 60 * 24 * 7 // 1 week
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Cache dictionary lookups - these are frequently accessed
            urlPattern: /\/api\/dictionary\/.+$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'dictionary-data',
              expiration: {
                maxEntries: 5000, // Many unique words
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Cache sandhi splits - compound words
            urlPattern: /\/api\/split\/.+$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'sandhi-splits',
              expiration: {
                maxEntries: 2000,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Cache search results with NetworkFirst for freshness
            urlPattern: /\/api\/search\?.+$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'search-results',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 // 1 hour
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      },
      devOptions: {
        enabled: true // Enable PWA in dev mode for testing
      }
    })
  ],
})
