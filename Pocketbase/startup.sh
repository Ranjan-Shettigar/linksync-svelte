#!/bin/sh

set -e

# Set rclone config directory
export RCLONE_CONFIG_DIR="$HOME/.config/rclone"

# Prepare rclone config
mkdir -p "$RCLONE_CONFIG_DIR"
if [ -n "$RCLONE_CONF_TEXT" ]; then
  echo "Using provided RCLONE_CONF_TEXT for rclone.conf"
  echo "$RCLONE_CONF_TEXT" > "$RCLONE_CONFIG_DIR/rclone.conf"
else
  echo "RCLONE_CONF_TEXT is not set. Exiting."
  exit 1
fi

# Restore PocketBase data from Dropbox if available
if rclone ls dropbox:pocketbase-linksync-data >/dev/null 2>&1; then
  echo "Restoring PocketBase data from Dropbox..."
  rclone sync --checksum dropbox:pocketbase-linksync-data /pb_data
else
  echo "No backup found on Dropbox. Skipping restore."
fi

# Schedule backup every 5 minutes in background
while true; do
  sleep 300
  echo "Backing up PocketBase data to Dropbox..."
  rclone sync --checksum /pb_data dropbox:pocketbase-linksync-data
done &

# Start PocketBase in background
pocketbase serve --http=0.0.0.0:8090 &

# Start SvelteKit (run in /linksync-svelte)
cd /linksync-svelte
npm run preview -- --host 0.0.0.0 &

# Wait for background processes
wait
