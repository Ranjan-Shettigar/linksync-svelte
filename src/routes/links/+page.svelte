<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { currentUser } from '$lib/services/pocketbase';
    import { getUserLinks, deleteLink, searchLinks, subscribeToSearchResults } from '$lib/services/link-service';
    import { goto } from '$app/navigation';
    import { debounce } from 'lodash-es';
    import type { Link } from '$lib/models/link';
    import LinkCard from '$lib/components/LinkCard.svelte';
    
    let links: Link[] = [];
    let isLoading = true;
    let error = '';
    let searchQuery = '';
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
            
            // Only search user's own links in this page
            const userId = $currentUser?.id;
            if (!userId) return;
            
            // Set up new subscription
            const unsubscribe = await subscribeToSearchResults(
                query, 
                true, 
                (results) => {
                    // Filter to only show the current user's links
                    links = results.filter(link => link.user === userId);
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
        if ($currentUser) {
            debouncedSearch(searchQuery);
        }
    }
    
    onMount(async () => {
        // Redirect to home if not authenticated
        if (!$currentUser) {
            goto('/');
            return;
        }
        
        // Initial load of links
        await debouncedSearch('');
    });
    
    onDestroy(async () => {
        // Clean up subscription when component is destroyed
        if (unsubscribeFunction) {
            await unsubscribeFunction();
        }
    });
    
    async function handleDelete(id: string) {
        if (!confirm('Are you sure you want to delete this link?')) {
            return;
        }
        
        try {
            await deleteLink(id);
            // No need to manually reload - the realtime subscription will handle it
        } catch (err: any) {
            error = err.message || 'Failed to delete link';
            console.error('Error deleting link:', err);
        }
    }
    
    function resetSearch() {
        searchQuery = '';
        // debouncedSearch will be triggered by the reactive statement
    }
</script>

<div class="container">
    <div class="header-section">
        <div class="title-area">
            <h1 class="page-title">My Links</h1>
            <p class="subtitle">Manage your personal link collection</p>
        </div>
        
        <div class="action-area">
            <a href="/links/new" class="primary-btn">Add New Link</a>
        </div>
    </div>
    
    <div class="search-section">
        <div class="search-form">
            <input 
                type="text" 
                bind:value={searchQuery} 
                placeholder="Search your links..." 
                class="search-input"
            />
        </div>
    </div>
    
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
                <button class="reset-btn" on:click={resetSearch}>Show All Links</button>
            {:else}
                <p>You haven't added any links yet.</p>
                <a href="/links/new" class="primary-btn">Add Your First Link</a>
            {/if}
        </div>
    {:else}
        <div class="links-grid">
            {#each links as link (link.id)}
                <LinkCard 
                    {link} 
                    showActions={true} 
                    on:delete={(e) => handleDelete(e.detail)} 
                />
            {/each}
        </div>
    {/if}
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
    
    .page-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0;
    }
    
    .subtitle {
        font-size: 1.125rem;
        color: #64748b;
        margin: 0.5rem 0 0 0;
    }
    
    .primary-btn {
        display: inline-block;
        background-color: #2563eb;
        color: white;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border-radius: 0.375rem;
        text-decoration: none;
        transition: background-color 0.2s;
    }
    
    .primary-btn:hover {
        background-color: #1d4ed8;
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
        gap: 1.5rem;
    }
    
    .loading-indicator {
        text-align: center;
        padding: 2rem;
        color: #6b7280;
        font-style: italic;
    }
    
    .empty-state {
        text-align: center;
        padding: 3rem;
        background-color: #f9fafb;
        border-radius: 0.5rem;
        color: #6b7280;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }
    
    .error-message {
        padding: 1rem;
        background-color: #fee2e2;
        border-radius: 0.375rem;
        color: #991b1b;
        margin-bottom: 1.5rem;
    }
    
    .reset-btn {
        background-color: #e5e7eb;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        cursor: pointer;
        font-size: 0.875rem;
    }
    
    .reset-btn:hover {
        background-color: #d1d5db;
    }
    
    @media (max-width: 768px) {
        .header-section {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
        
        .action-area {
            width: 100%;
        }
        
        .primary-btn {
            width: 100%;
            text-align: center;
        }
        
        .search-form {
            flex-direction: column;
        }
    }

    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem;
    }
    .error-message {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin-bottom: 1.5rem;
    }
</style>
