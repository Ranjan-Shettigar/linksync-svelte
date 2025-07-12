import pb from './pocketbase';
import type { Link, LinkFormData } from '$lib/models/link';
import { fetchUrlMetadata } from './metadata-service';

// Get all links for the current user
export async function getUserLinks(): Promise<Link[]> {
    try {
        if (!pb.authStore.isValid) {
            throw new Error('User not authenticated');
        }
        
        const userId = pb.authStore.model?.id;
        if (!userId) {
            throw new Error('User ID not found');
        }
        
        const records = await pb.collection('links').getList(1, 100, {
            filter: `user = "${userId}"`,
            sort: '-created'
        });
        
        return records.items as unknown as Link[];
    } catch (error) {
        console.error('Error fetching user links:', error);
        throw error;
    }
}

// Create a new link
export async function createLink(linkData: LinkFormData): Promise<Link> {
    try {
        if (!pb.authStore.isValid) {
            throw new Error('User not authenticated');
        }
        
        const userId = pb.authStore.model?.id;
        if (!userId) {
            throw new Error('User ID not found');
        }
        
        // Process tags from comma-separated string to array
        const tags = linkData.tags
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag !== '');
        
        // Try to fetch favicon/logo from the URL
        let favicon = '';
        try {
            const metadata = await fetchUrlMetadata(linkData.url);
            favicon = metadata.logo || '';
        } catch (err) {
            console.warn('Failed to fetch favicon:', err);
            // Continue without favicon if there's an error
        }
        
        const data = {
            url: linkData.url,
            name: linkData.name,
            description: linkData.description,
            tags: tags,
            visibility: linkData.visibility,
            user: userId,
            favicon: favicon
        };
        
        const record = await pb.collection('links').create(data);
        return record as unknown as Link;
    } catch (error) {
        console.error('Error creating link:', error);
        throw error;
    }
}

// Update an existing link
export async function updateLink(id: string, linkData: LinkFormData): Promise<Link> {
    try {
        if (!pb.authStore.isValid) {
            throw new Error('User not authenticated');
        }
        
        // Process tags from comma-separated string to array
        const tags = linkData.tags
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag !== '');
        
        // Try to fetch favicon/logo from the URL if it's changed
        let favicon = '';
        try {
            const metadata = await fetchUrlMetadata(linkData.url);
            favicon = metadata.logo || '';
        } catch (err) {
            console.warn('Failed to fetch favicon during update:', err);
            // Continue with empty favicon if there's an error
        }
        
        const data = {
            url: linkData.url,
            name: linkData.name,
            description: linkData.description,
            tags: tags,
            visibility: linkData.visibility,
            favicon: favicon
        };
        
        const record = await pb.collection('links').update(id, data);
        return record as unknown as Link;
    } catch (error) {
        console.error('Error updating link:', error);
        throw error;
    }
}

// Delete a link
export async function deleteLink(id: string): Promise<boolean> {
    try {
        if (!pb.authStore.isValid) {
            throw new Error('User not authenticated');
        }
        
        await pb.collection('links').delete(id);
        return true;
    } catch (error) {
        console.error('Error deleting link:', error);
        throw error;
    }
}

// Get a single link by ID
export async function getLinkById(id: string): Promise<Link> {
    try {
        const record = await pb.collection('links').getOne(id);
        return record as unknown as Link;
    } catch (error) {
        console.error('Error fetching link:', error);
        throw error;
    }
}

// Check if a URL already exists in the user's links
export async function checkDuplicateUrl(url: string, checkPublicOnly = false): Promise<boolean> {
    try {
        if (!pb.authStore.isValid && !checkPublicOnly) {
            throw new Error('User not authenticated');
        }
        
        const userId = pb.authStore.model?.id;
        
        // Normalize the URL for comparison
        // Remove protocol (http/https) and trailing slashes for better matching
        const normalizedUrl = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
        
        let filter;
        if (checkPublicOnly) {
            // Only check for public links (for checking others' public links)
            filter = `visibility = "public"`;
        } else {
            // Check only the current user's links
            filter = `user = "${userId}"`;
        }
        
        // Get relevant links based on the filter
        const records = await pb.collection('links').getList(1, 100, {
            filter: filter
        });
        
        // Check if any of the links have a matching URL (normalized)
        const hasDuplicate = records.items.some(item => {
            const itemUrl = (item.url as string).replace(/^https?:\/\//, '').replace(/\/$/, '');
            
            // If checking user's own links, return true for any match
            if (!checkPublicOnly) {
                return itemUrl === normalizedUrl;
            }
            
            // If checking other users' public links, only return true if the link isn't owned by current user
            return itemUrl === normalizedUrl && item.user !== userId;
        });
        
        return hasDuplicate;
    } catch (error) {
        console.error('Error checking for duplicate URL:', error);
        throw error;
    }
}

// Check if a domain already exists in the user's links
export async function checkDuplicateDomain(url: string): Promise<boolean> {
    try {
        if (!pb.authStore.isValid) {
            throw new Error('User not authenticated');
        }
        
        const userId = pb.authStore.model?.id;
        if (!userId) {
            throw new Error('User ID not found');
        }
        
        // Extract domain from URL
        let domain;
        try {
            const urlObj = new URL(url);
            domain = urlObj.hostname;
        } catch (e) {
            throw new Error('Invalid URL');
        }
        
        // Get all user links
        const records = await pb.collection('links').getList(1, 100, {
            filter: `user = "${userId}"`
        });
        
        // Check if any of the user's links have a matching domain
        const hasDuplicate = records.items.some(item => {
            try {
                const itemUrl = new URL(item.url as string);
                return itemUrl.hostname === domain;
            } catch {
                return false;
            }
        });
        
        return hasDuplicate;
    } catch (error) {
        console.error('Error checking for duplicate domain:', error);
        throw error;
    }
}

// Check if a link is already public (by any user)
export async function checkPublicDuplicateUrl(url: string): Promise<boolean> {
    return checkDuplicateUrl(url, true);
}

// Get all public links from all users
export async function getPublicLinks(): Promise<Link[]> {
    try {
        const records = await pb.collection('links').getList(1, 100, {
            filter: 'visibility = "public"',
            sort: '-created'
        });
        
        return records.items as unknown as Link[];
    } catch (error) {
        console.error('Error fetching public links:', error);
        throw error;
    }
}

// Search links by keyword (in name, description, or tags)
export async function searchLinks(query: string, includePrivate: boolean = false): Promise<Link[]> {
    try {
        let filter = 'visibility = "public"';
        
        // If user is authenticated and we want to include private links
        if (pb.authStore.isValid && includePrivate) {
            const userId = pb.authStore.model?.id;
            if (!userId) {
                throw new Error('User ID not found');
            }
            filter = `(visibility = "public" || (visibility = "private" && user = "${userId}"))`;
        }
        
        // Add search conditions if query is provided
        if (query && query.trim() !== '') {
            const searchQuery = query.trim().toLowerCase();
            filter += ` && (name ~ "${searchQuery}" || description ~ "${searchQuery}" || tags ~ "${searchQuery}")`;
        }
        
        const records = await pb.collection('links').getList(1, 100, {
            filter: filter,
            sort: '-created'
        });
        
        return records.items as unknown as Link[];
    } catch (error) {
        console.error('Error searching links:', error);
        throw error;
    }
}

// Subscribe to realtime search results
export function subscribeToSearchResults(
    query: string, 
    includePrivate: boolean = false, 
    callback: (links: Link[]) => void
): Promise<() => void> {
    try {
        let filter = 'visibility = "public"';
        
        // If user is authenticated and we want to include private links
        if (pb.authStore.isValid && includePrivate) {
            const userId = pb.authStore.model?.id;
            if (!userId) {
                throw new Error('User ID not found');
            }
            filter = `(visibility = "public" || (visibility = "private" && user = "${userId}"))`;
        }
        
        // Add search conditions if query is provided
        if (query && query.trim() !== '') {
            const searchQuery = query.trim().toLowerCase();
            filter += ` && (name ~ "${searchQuery}" || description ~ "${searchQuery}" || tags ~ "${searchQuery}")`;
        }
        
        // Initial fetch of results
        pb.collection('links').getList(1, 100, {
            filter: filter,
            sort: '-created'
        }).then(records => {
            callback(records.items as unknown as Link[]);
        }).catch(error => {
            console.error('Error in initial search:', error);
        });
        
        // Subscribe to realtime updates
        return pb.collection('links').subscribe('*', function(e) {
            // When data changes, refetch the filtered results
            pb.collection('links').getList(1, 100, {
                filter: filter,
                sort: '-created'
            }).then(records => {
                callback(records.items as unknown as Link[]);
            }).catch(error => {
                console.error('Error in realtime search update:', error);
            });
        });
    } catch (error) {
        console.error('Error setting up search subscription:', error);
        // Return empty promise with unsubscribe function in case of error
        return Promise.resolve(() => {});
    }
}
