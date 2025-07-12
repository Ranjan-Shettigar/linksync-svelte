# LinkSync

LinkSync is a web application that allows users to save, organize, and access their important links from anywhere. It's built with SvelteKit and uses PocketBase for authentication and data storage.

## Features

- **Google OAuth Authentication**: Secure login using Google accounts
- **Link Management**: Add, edit, and delete your saved links
- **Organization**: Tag links and set visibility options (public/private)
- **Responsive Design**: Works well on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js (v18 or later)
- PocketBase (for backend)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/linksync.git
cd linksync
```

2. Install dependencies:

```bash
npm install
```

3. Create a `.env` file in the root directory with your PocketBase URL:

```
VITE_POCKETBASE_URL=http://localhost:8090
```

Or for the hosted version:

```
VITE_POCKETBASE_URL=https://the-loko-pocketbase-s1.hf.space
```

4. Configure PocketBase collections and authentication (see [POCKETBASE_SETUP.md](POCKETBASE_SETUP.md))

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

### Build for Production

```bash
npm run build
```

## Project Structure

- `src/routes`: SvelteKit routes
- `src/lib/components`: Reusable UI components
- `src/lib/services`: Service modules for data operations
- `src/lib/models`: TypeScript interfaces

## PocketBase Setup

For detailed instructions on setting up PocketBase collections and Google OAuth, see [POCKETBASE_SETUP.md](POCKETBASE_SETUP.md).

## License

[MIT](LICENSE)
