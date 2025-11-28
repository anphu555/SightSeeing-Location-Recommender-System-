// exSighting/vite.config.js
import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        login: resolve(__dirname, 'login.html'),
        register: resolve(__dirname, 'register.html'),
        result: resolve(__dirname, 'result.html'),
        // Thêm các file html khác vào đây nếu còn
      },
    },
  },
})