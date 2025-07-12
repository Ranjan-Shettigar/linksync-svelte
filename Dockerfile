FROM node:latest AS builder

WORKDIR /app

# Clone the repo
RUN git clone https://github.com/Ranjan-Shettigar/linksync-svelte.git .

# Install dependencies
RUN npm install

# Build the SvelteKit app
RUN npm run build

# Set permissions for required directories
RUN chmod 777 /app /app/node_modules && \
    find /app -type d -exec chmod 777 {} \;

# Set ownership to node user
RUN chown -R node:node /app

# Set preview host from environment (default empty)
ENV PREVIEW_HOST=""

# Use node user
USER node

# Expose port (default SvelteKit port)
EXPOSE 4173

# Start the app
CMD ["npm", "run", "preview"]