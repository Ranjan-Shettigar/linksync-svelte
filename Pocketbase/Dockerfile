FROM node:20-alpine

# Install ca-certificates, unzip, curl, jq, rclone, and git
RUN apk add --no-cache ca-certificates unzip curl jq rclone git

# Download and install PocketBase (latest version)
RUN LATEST_VERSION=$(curl -s https://api.github.com/repos/pocketbase/pocketbase/releases/latest | jq -r '.tag_name') \
    && wget -O /tmp/pocketbase.zip "https://github.com/pocketbase/pocketbase/releases/download/${LATEST_VERSION}/pocketbase_${LATEST_VERSION#v}_linux_amd64.zip" \
    && unzip /tmp/pocketbase.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/pocketbase \
    && rm /tmp/pocketbase.zip

# Clone SvelteKit repo
RUN git clone https://github.com/Ranjan-Shettigar/linksync-svelte.git /linksync-svelte

# Install SvelteKit dependencies
RUN cd /linksync-svelte && npm install

# Build SvelteKit for production
RUN cd /linksync-svelte && npm run build

# Copy startup script to /pb_data
COPY startup.sh /pb_data/startup.sh
RUN chmod +x /pb_data/startup.sh

# Create data directory with proper permissions
RUN mkdir -p /pb_data && chmod 755 /pb_data

# Create home directory for non-root user
RUN mkdir -p /home/pocketbase

# Create non-root user with home directory
RUN adduser -D -s /bin/sh -h /home/pocketbase pocketbase

# Change ownership of directories
RUN chown -R pocketbase:pocketbase /pb_data /home/pocketbase

# Switch to non-root user
USER pocketbase

# Expose port
EXPOSE 5173 

# Set working directory
WORKDIR /pb_data

# Start with backup script
CMD sh startup.sh