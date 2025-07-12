// Fetch metadata for a URL
export async function fetchUrlMetadata(url: string) {
    try {
        const response = await fetch('/api/fetch-metadata', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch metadata');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching URL metadata:', error);
        throw error;
    }
}
