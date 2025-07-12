import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 5173,
		strictPort: true, // Fail if port is already in use
		hmr: {
			protocol: 'ws',
			host: 'localhost',
			port: 5173
		}
	}
});
