# PocketBase Configuration for LinkSync

To fully set up the LinkSync application, you need to create and configure the necessary PocketBase collections. Follow the steps below:

## Setting Up PocketBase

1. Make sure you have PocketBase running (if using a remote instance, ensure the URL is correctly set in your `.env` file)
2. Log in to the PocketBase Admin UI (typically at `https://your-pocketbase-url/_/`)

## Creating the Links Collection

1. In the PocketBase Admin UI, go to the "Collections" section
2. Click "Create collection"
3. Enter the following details:
   - Name: `links`
   - Type: "Base collection"
   - Click "Create"

4. Add the following fields:

| Field Name    | Type           | Required | Settings                           |
|---------------|----------------|----------|-----------------------------------|
| url           | URL            | Yes      | Min length: 1                     |
| name          | Text           | Yes      | Min length: 1                     |
| description   | Text           | No       | -                                 |
| tags          | JSON Array     | No       | Default: `[]`                     |
| visibility    | Select         | Yes      | Options: `private`, `public`      |
|               |                |          | Default: `private`                |
| favicon       | Text           | No       | -                                 |
| user          | Relation       | Yes      | Collection: `users`               |
|               |                |          | Cascade Delete: Yes               |

1. Set up collection rules:
   - In the "API Rules" tab, create rules to ensure users can only:
     - Read their own links (except for public links)
     - Create links for themselves
     - Update and delete only their own links

## Google OAuth Configuration

1. In the PocketBase Admin UI, go to "Settings" > "Auth providers"
2. Enable Google provider
3. Fill in your Google OAuth credentials:
   - Client ID
   - Client Secret
4. Set up authorized redirect URL:
   - For local development: `http://localhost:5173/auth/callback`
   - For production: `https://your-domain.com/auth/callback`

## Testing the Setup

1. Make sure your environment variables are set correctly:

```env
VITE_POCKETBASE_URL=https://your-pocketbase-url
```

2. Run the LinkSync application:

```bash
npm run dev
```

3. Try the following:
   - Sign in with Google
   - Add a new link
   - Edit an existing link
   - Delete a link
   - Verify that links are saved to the PocketBase collection

## Security Considerations

- Ensure proper authentication is enforced for all API requests
- Set up CORS policies in PocketBase to only allow requests from your application domains
- Regularly update dependencies and PocketBase to the latest versions
- Consider adding rate limiting to prevent abuse
