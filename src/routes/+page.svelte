<script lang="ts">
    import { currentUser } from '$lib/services/pocketbase';
    import { getPublicLinks, getUserLinks, searchLinks, subscribeToSearchResults } from '$lib/services/link-service';
    import { onMount, onDestroy } from 'svelte';
    import { debounce } from 'lodash-es';
    import LinkCard from '$lib/components/LinkCard.svelte';
    import type { Link } from '$lib/models/link';
    import { browser } from '$app/environment';
    
    let isLoading = true;
    let links: Link[] = [];
    let searchQuery = '';
    let error = '';
    let unsubscribeFunction: (() => void) | null = null;
    
    // Debounce the search to avoid too many requests while typing
    const debouncedSearch = debounce(async (query: string) => {
        error = '';
        
        if (!unsubscribeFunction) {
            isLoading = true;
        }
        
        try {
            // Clean up previous subscription if exists
            if (unsubscribeFunction) {
                await unsubscribeFunction();
                unsubscribeFunction = null;
            }
            
            // Set up new subscription
            const unsubscribe = await subscribeToSearchResults(
                query, 
                !!$currentUser, 
                (results) => {
                    links = results;
                    isLoading = false;
                }
            );
            
            unsubscribeFunction = unsubscribe;
        } catch (err: any) {
            console.error('Error searching links:', err);
            error = err.message || 'Failed to search links';
            isLoading = false;
        }
    }, 300); // 300ms debounce delay
    
    // Watch for search query changes
    $: {
        debouncedSearch(searchQuery);
    }
    
    // Watch for authentication changes to refresh links
    $: if ($currentUser !== undefined) {
        debouncedSearch(searchQuery);
    }
    
    onMount(async () => {
        // Initial load of links
        await debouncedSearch('');
        
        // Check if this is a fresh login and clear the flag
        if (browser && sessionStorage.getItem('fresh_login') === 'true') {
            console.log('Fresh login detected, refreshing links data');
            sessionStorage.removeItem('fresh_login');
            // Allow a moment for UI to render initial results
            setTimeout(() => {
                debouncedSearch(searchQuery);
            }, 500);
        }
    });
    
    onDestroy(async () => {
        // Clean up subscription when component is destroyed
        if (unsubscribeFunction) {
            await unsubscribeFunction();
        }
    });
</script>

<div class="container">
    <div class="header-section">
        <!-- Removed subtitle and Add New Link button -->
    </div>
    
    <div class="search-section">
        <div class="search-form">
            <input 
                type="text" 
                bind:value={searchQuery} 
                placeholder="Search links by name, description, or tags..." 
                class="search-input"
            />
        </div>
    </div>
    
    <div class="links-section">
        {#if error}
            <div class="error-message">
                {error}
            </div>
        {/if}
        
        {#if isLoading}
            <div class="loading-indicator">Loading links...</div>
        {:else if links.length === 0}
            <div class="empty-state">
                {#if searchQuery}
                    <p>No links found matching "{searchQuery}"</p>
                {:else}
                    <p>No links available yet.</p>
                {/if}
            </div>
        {:else}
            <div class="links-grid">
                {#each links as link}
                    <LinkCard 
                        {link} 
                        showActions={false} 
                    />
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    .header-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    .search-section {
        margin-bottom: 2rem;
    }
    
    .search-form {
        display: flex;
        width: 100%;
    }
    
    .search-input {
        flex: 1;
        padding: 0.75rem 1rem;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-size: 1rem;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    
    .search-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
    }
    
    .links-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
    }
    
    .loading-indicator {
        text-align: center;
        padding: 2rem;
        color: #6b7280;
        font-style: italic;
        grid-column: 1 / -1;
    }
    
    .empty-state {
        text-align: center;
        padding: 3rem;
        background-color: #f9fafb;
        border-radius: 0.5rem;
        color: #6b7280;
        grid-column: 1 / -1;
    }
    
    .error-message {
        padding: 1rem;
        background-color: #fee2e2;
        border-radius: 0.375rem;
        color: #991b1b;
        margin-bottom: 1.5rem;
        grid-column: 1 / -1;
    }
    
    @media (max-width: 1200px) {
        .links-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    @media (max-width: 900px) {
        .links-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 600px) {
        .links-grid {
            grid-template-columns: 1fr;
        }
        
        .header-section {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
        
        .search-form {
            flex-direction: column;
        }
    }
</style>
