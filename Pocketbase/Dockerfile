FROM node:latest AS builder

WORKDIR /app

# Clone the repo
RUN git clone https://github.com/Ranjan-Shettigar/linksync-svelte.git .

# Install dependencies
RUN npm install

# Build the SvelteKit app
RUN npm run build

# Start a new, lean container
FROM node:lts-alpine

WORKDIR /app

# Copy built assets from the builder stage
COPY --from=builder /app/build ./
COPY --from=builder /app/package.json ./

# Install only production dependencies
RUN npm install --omit=dev

# Expose port (default SvelteKit node adapter port)
EXPOSE 5173

# Start the app
CMD ["node", "index.js"]