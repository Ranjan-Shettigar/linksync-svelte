<script lang="ts">
    import type { Link } from '$lib/models/link';
    import { createEventDispatcher } from 'svelte';
    
    export let link: Link;
    export let showActions: boolean = true;
    
    const dispatch = createEventDispatcher();
    
    // Format date
    function formatDate(dateString: string | undefined): string {
        if (!dateString) return 'Unknown date';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    function handleDelete() {
        dispatch('delete', link.id);
    }
</script>

<div class="link-card">
    <div class="link-content">
        <h3 class="link-title">
            <a href={link.url} target="_blank" rel="noopener noreferrer">
                {#if link.favicon}
                    <img src={link.favicon} alt="" class="link-favicon" />
                {:else}
                    <div class="link-favicon-placeholder"></div>
                {/if}
                {link.name}
            </a>
        </h3>
        
        <p class="link-url">{link.url}</p>
        
        {#if link.description}
            <p class="link-description">{link.description}</p>
        {/if}
        
        <div class="link-meta">
            {#if link.visibility === 'public'}
                <span class="visibility-badge public">Public</span>
            {:else}
                <span class="visibility-badge private">Private</span>
            {/if}
            
            <span class="created-date">Added {formatDate(link.created)}</span>
            
            {#if link.tags && link.tags.length > 0}
                <div class="tags">
                    {#each link.tags as tag}
                        <span class="tag">{tag}</span>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
    
    {#if showActions}
        <div class="link-actions">
            <a href={`/links/${link.id}/edit`} class="edit-btn">Edit</a>
            <button class="delete-btn" on:click={handleDelete}>Delete</button>
        </div>
    {/if}
</div>

<style>
    .link-card {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        padding: 1.25rem;
        height: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .link-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .link-content {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    
    .link-title {
        margin: 0 0 0.5rem 0;
        font-size: 1.25rem;
        font-weight: 600;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.3;
    }
    
    .link-title a {
        color: #2563eb;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .link-title a:hover {
        text-decoration: underline;
    }
    
    .link-favicon {
        width: 20px;
        height: 20px;
        flex-shrink: 0;
        object-fit: contain;
    }
    
    .link-favicon-placeholder {
        width: 20px;
        height: 20px;
        flex-shrink: 0;
        background-color: #e5e7eb;
        border-radius: 4px;
    }
    
    .link-url {
        color: #6b7280;
        font-size: 0.875rem;
        margin: 0 0 0.75rem 0;
        word-break: break-all;
        display: -webkit-box;
        -webkit-line-clamp: 1;
        line-clamp: 1;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .link-description {
        margin: 0 0 1rem 0;
        color: #4b5563;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.5;
    }
    
    .link-meta {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.875rem;
        margin-top: auto;
    }
    
    .visibility-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-weight: 500;
        font-size: 0.75rem;
    }
    
    .visibility-badge.public {
        background-color: #dcfce7;
        color: #166534;
    }
    
    .visibility-badge.private {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    .created-date {
        color: #6b7280;
    }
    
    .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
        width: 100%;
    }
    
    .tag {
        background-color: #f3f4f6;
        color: #4b5563;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        white-space: nowrap;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .link-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    
    .edit-btn, .delete-btn {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 500;
        text-align: center;
        text-decoration: none;
        transition: background-color 0.2s;
        flex: 1;
    }
    
    .edit-btn {
        background-color: #f3f4f6;
        color: #4b5563;
    }
    
    .edit-btn:hover {
        background-color: #e5e7eb;
    }
    
    .delete-btn {
        background-color: #fee2e2;
        color: #b91c1c;
        border: none;
        cursor: pointer;
    }
    
    .delete-btn:hover {
        background-color: #fecaca;
    }
</style>
