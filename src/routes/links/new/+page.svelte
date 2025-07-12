<script lang="ts">
    import { createLink, checkDuplicateUrl, checkPublicDuplicateUrl } from '$lib/services/link-service';
    import { currentUser } from '$lib/services/pocketbase';
    import { fetchUrlMetadata } from '$lib/services/metadata-service';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import type { LinkFormData } from '$lib/models/link';
    
    let formData: LinkFormData = {
        url: '',
        name: '',
        description: '',
        tags: '',
        visibility: 'private'
    };
    
    let isSubmitting = false;
    let isFetchingMetadata = false;
    let isCheckingDuplicate = false;
    let error = '';
    let urlError = '';
    let duplicateUrlError = '';
    let publicDuplicateError = '';
    
    onMount(() => {
        // Redirect to home if not authenticated
        if (!$currentUser) {
            goto('/');
        }
    });
    
    // Validate URL format
    function validateUrl(url: string): boolean {
        try {
            new URL(url);
            urlError = '';
            return true;
        } catch (e) {
            urlError = 'Please enter a valid URL (include http:// or https://)';
            return false;
        }
    }
    
    // Check for duplicate URL when the URL field changes
    async function checkUrlDuplicate() {
        if (!formData.url || !validateUrl(formData.url)) {
            duplicateUrlError = '';
            publicDuplicateError = '';
            return;
        }
        
        isCheckingDuplicate = true;
        
        try {
            // Check user's own links
            const isDuplicate = await checkDuplicateUrl(formData.url);
            duplicateUrlError = isDuplicate ? 'This URL already exists in your links' : '';
            
            // If setting to public, also check for other users' public links
            if (formData.visibility === 'public' && !duplicateUrlError) {
                const isPublicDuplicate = await checkPublicDuplicateUrl(formData.url);
                publicDuplicateError = isPublicDuplicate ? 'This URL is already public from another user' : '';
            } else {
                publicDuplicateError = '';
            }
        } catch (err) {
            console.error('Error checking duplicate URL:', err);
        } finally {
            isCheckingDuplicate = false;
        }
    }
    
    // Handle URL input changes
    function handleUrlChange() {
        // Clear duplicate errors when URL changes
        duplicateUrlError = '';
        publicDuplicateError = '';
        
        // Validate URL format
        validateUrl(formData.url);
        
        // Debounce duplicate check to avoid too many requests
        clearTimeout(urlChangeTimeout);
        urlChangeTimeout = setTimeout(checkUrlDuplicate, 500);
    }
    
    // Handle visibility changes
    function handleVisibilityChange() {
        // If changing to public, check if URL is already public
        if (formData.visibility === 'public' && formData.url && validateUrl(formData.url)) {
            clearTimeout(urlChangeTimeout);
            urlChangeTimeout = setTimeout(checkUrlDuplicate, 100);
        } else {
            publicDuplicateError = '';
        }
    }
    
    let urlChangeTimeout: ReturnType<typeof setTimeout>;
    
    // Fetch metadata for the URL and autofill form fields
    async function fetchMetadata() {
        if (!formData.url || !validateUrl(formData.url)) {
            return;
        }
        
        isFetchingMetadata = true;
        error = '';
        
        try {
            const metadata = await fetchUrlMetadata(formData.url);
            
            // Always update fields with the latest metadata
            if (metadata.title) {
                formData.name = metadata.title;
            }
            
            if (metadata.description) {
                formData.description = metadata.description;
            }
            
        } catch (err: any) {
            console.error('Error autofilling metadata:', err);
            // We don't show an error to the user here as this is just a convenience feature
        } finally {
            isFetchingMetadata = false;
        }
    }
    
    // Handle URL input blur event to auto-fetch metadata
    function handleUrlBlur() {
        if (formData.url && validateUrl(formData.url)) {
            fetchMetadata();
        }
    }
    
    async function handleSubmit() {
        // Reset error state
        error = '';
        
        // Validate URL
        if (!validateUrl(formData.url)) {
            return;
        }
        
        // Validate required fields
        if (!formData.name) {
            error = 'Name is required';
            return;
        }
        
        isSubmitting = true;
        
        try {
            // Check for duplicate URLs
            if (duplicateUrlError) {
                error = duplicateUrlError;
                isSubmitting = false;
                return;
            }
            
            // Check for public duplicate URLs
            if (publicDuplicateError) {
                error = publicDuplicateError;
                isSubmitting = false;
                return;
            }
            
            // If set to public, do one final check for public duplicates
            if (formData.visibility === 'public') {
                const isPublicDuplicate = await checkPublicDuplicateUrl(formData.url);
                if (isPublicDuplicate) {
                    error = 'This URL is already public from another user';
                    isSubmitting = false;
                    return;
                }
            }
            
            await createLink(formData);
            // Reset form
            formData = {
                url: '',
                name: '',
                description: '',
                tags: '',
                visibility: 'private'
            };
            
            // Redirect to links page
            goto('/links');
        } catch (err: any) {
            error = err.message || 'An error occurred while saving the link';
            console.error('Error creating link:', err);
        } finally {
            isSubmitting = false;
        }
    }
</script>

<div class="container">
    <div class="form-container">
        <h1>Add New Link</h1>
        
        {#if error}
            <div class="error-message">
                {error}
            </div>
        {/if}
        
        <form on:submit|preventDefault={handleSubmit}>
            <div class="form-group">
                <label for="url">URL <span class="required">*</span></label>
                <div class="input-with-button">
                    <input
                        type="text"
                        id="url"
                        bind:value={formData.url}
                        on:input={handleUrlChange}
                        on:blur={handleUrlBlur}
                        placeholder="https://example.com"
                        required
                    />
                    <button 
                        type="button" 
                        class="fetch-btn" 
                        on:click={fetchMetadata}
                        disabled={!formData.url || isFetchingMetadata || !validateUrl(formData.url)}
                    >
                        {isFetchingMetadata ? 'Fetching...' : 'Extract Data'}
                    </button>
                </div>
                {#if urlError}
                    <div class="field-error">{urlError}</div>
                {/if}
                {#if duplicateUrlError}
                    <div class="field-error">{duplicateUrlError}</div>
                {/if}
                {#if publicDuplicateError}
                    <div class="field-error">{publicDuplicateError}</div>
                {/if}
                {#if isCheckingDuplicate}
                    <div class="checking-indicator">Checking if URL already exists...</div>
                {/if}
                {#if isFetchingMetadata}
                    <div class="fetching-indicator">Fetching metadata from URL...</div>
                {:else if !duplicateUrlError && !isCheckingDuplicate}
                    <div class="hint-text">Click "Extract Data" to get the title and description from this URL</div>
                {/if}
            </div>
            
            <div class="form-group">
                <label for="name">Name <span class="required">*</span></label>
                <input
                    type="text"
                    id="name"
                    bind:value={formData.name}
                    placeholder="My Website"
                    required
                />
            </div>
            
            <div class="form-group">
                <label for="description">Description</label>
                <textarea
                    id="description"
                    bind:value={formData.description}
                    placeholder="A brief description of this link"
                    rows="3"
                ></textarea>
            </div>
            
            <div class="form-group">
                <label for="tags">Tags (comma separated)</label>
                <input
                    type="text"
                    id="tags"
                    bind:value={formData.tags}
                    placeholder="work, reference, favorite"
                />
            </div>
            
            <div class="form-group">
                <label for="visibility">Visibility</label>
                <select 
                    id="visibility" 
                    bind:value={formData.visibility}
                    on:change={handleVisibilityChange}
                >
                    <option value="private">Private (Only you)</option>
                    <option value="public">Public (Anyone with the link)</option>
                </select>
            </div>
            
            <div class="form-actions">
                <a href="/links" class="btn-secondary">Cancel</a>
                <button 
                    type="submit" 
                    class="btn-primary"
                    disabled={isSubmitting}
                >
                    {isSubmitting ? 'Saving...' : 'Save Link'}
                </button>
            </div>
        </form>
    </div>
</div>

<style>
    .container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .form-container {
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        padding: 2rem;
    }
    
    h1 {
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
        color: #333;
    }
    
    .form-group {
        margin-bottom: 1.25rem;
    }
    
    label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .required {
        color: #e11d48;
    }
    
    .input-with-button {
        display: flex;
        gap: 0.5rem;
    }
    
    .fetch-btn {
        padding: 0.75rem 1rem;
        background-color: #f3f4f6;
        color: #4b5563;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        white-space: nowrap;
        transition: background-color 0.2s;
    }
    
    .fetch-btn:hover:not(:disabled) {
        background-color: #e5e7eb;
    }
    
    .fetch-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    .fetching-indicator, .checking-indicator {
        margin-top: 0.5rem;
        font-size: 0.875rem;
        color: #6b7280;
        font-style: italic;
    }
    
    .hint-text {
        margin-top: 0.5rem;
        font-size: 0.875rem;
        color: #6b7280;
    }
    
    .field-error {
        margin-top: 0.5rem;
        font-size: 0.875rem;
        color: #e11d48;
    }
    
    input, textarea, select {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-size: 1rem;
        transition: border-color 0.2s;
    }
    
    input:focus, textarea:focus, select:focus {
        outline: none;
        border-color: #2563eb;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
    }
    
    .form-actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 2rem;
    }
    
    .btn-primary, .btn-secondary {
        padding: 0.75rem 1.5rem;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .btn-primary {
        background-color: #2563eb;
        color: white;
        border: none;
    }
    
    .btn-primary:hover {
        background-color: #1d4ed8;
    }
    
    .btn-primary:disabled {
        background-color: #93c5fd;
        cursor: not-allowed;
    }
    
    .btn-secondary {
        background-color: white;
        color: #4b5563;
        border: 1px solid #d1d5db;
        text-decoration: none;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .btn-secondary:hover {
        background-color: #f9fafb;
        text-decoration: none;
    }
    
    .error-message {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin-bottom: 1.5rem;
    }
    
    .field-error {
        color: #e11d48;
        font-size: 0.875rem;
        margin-top: 0.375rem;
    }
</style>
