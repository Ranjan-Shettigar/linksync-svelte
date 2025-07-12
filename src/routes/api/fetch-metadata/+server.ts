import metascraper from 'metascraper';
import metascraperTitle from 'metascraper-title';
import metascraperDescription from 'metascraper-description';
import metascraperImage from 'metascraper-image';
import metascraperLogo from 'metascraper-logo';
import metascraperUrl from 'metascraper-url';

// Initialize metascraper with the rules we want
const scraper = metascraper([
    metascraperTitle(),
    metascraperDescription(),
    metascraperImage(),
    metascraperLogo(),
    metascraperUrl()
]);

export async function POST({ request }) {
    try {
        const { url } = await request.json();
        
        if (!url) {
            return new Response(
                JSON.stringify({ error: 'URL is required' }),
                { status: 400, headers: { 'Content-Type': 'application/json' } }
            );
        }
        
        // Fetch the HTML content
        const response = await fetch(url);
        const html = await response.text();
        
        // Extract metadata using metascraper
        const metadata = await scraper({ html, url });
        
        // Try to get favicon from the domain if no logo was found
        if (!metadata.logo) {
            try {
                const urlObj = new URL(url);
                const domain = urlObj.hostname;
                // Try common favicon locations
                metadata.logo = `https://${domain}/favicon.ico`;
                
                // Verify the favicon exists with a HEAD request
                const faviconCheck = await fetch(metadata.logo, { method: 'HEAD' })
                    .then(res => res.ok)
                    .catch(() => false);
                
                if (!faviconCheck) {
                    // Try Google's favicon service as fallback
                    metadata.logo = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
                }
            } catch (e) {
                console.error('Error getting favicon:', e);
                // If all else fails, provide a default icon or empty string
                metadata.logo = '';
            }
        }
        
        return new Response(
            JSON.stringify(metadata),
            { headers: { 'Content-Type': 'application/json' } }
        );
    } catch (error) {
        console.error('Error fetching metadata:', error);
        
        return new Response(
            JSON.stringify({ error: 'Failed to fetch metadata' }),
            { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
    }
}
