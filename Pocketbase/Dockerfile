FROM node:latest AS builder

WORKDIR /app

# Clone the repo
RUN git clone https://github.com/Ranjan-Shettigar/linksync-svelte.git .

# Install dependencies
RUN npm install

# Build the SvelteKit app
RUN npm run build

# Expose port (default SvelteKit port)
EXPOSE 5173

# Start the app
CMD ["npm", "run", "preview", "--", "--port", "5173"]