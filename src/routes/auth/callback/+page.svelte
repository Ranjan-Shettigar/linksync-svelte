<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import pb, { currentUser, isAuthenticated } from '$lib/services/pocketbase';
    
    let isLoading = true;
    let error = '';
    
    onMount(async () => {
        console.log('Auth callback page loaded');
        
        try {
            // Give PocketBase some time to process the OAuth callback
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Check if authentication was successful
            if (pb.authStore.isValid && pb.authStore.model) {
                console.log('Authentication successful in callback');
                
                // Force update the stores
                currentUser.set(pb.authStore.model);
                isAuthenticated.set(true);
                
                // Manually save to localStorage as backup
                try {
                    const authData = {
                        token: pb.authStore.token,
                        model: pb.authStore.model,
                        savedAt: Date.now()
                    };
                    localStorage.setItem('pocketbase_auth_v2', JSON.stringify(authData));
                    console.log('Auth data manually saved in callback');
                } catch (saveError) {
                    console.error('Failed to save auth data in callback:', saveError);
                }
                
                // Set a flag in sessionStorage to indicate fresh login
                // This will be used by the home page to refresh data
                sessionStorage.setItem('fresh_login', 'true');
                
                // Redirect to home page
                console.log('Redirecting to home page...');
                goto('/', { replaceState: true });
                
            } else {
                console.error('Authentication failed - no valid auth store');
                error = 'Authentication failed. Please try again.';
                
                // Redirect after showing error
                setTimeout(() => {
                    goto('/', { replaceState: true });
                }, 2000);
            }
        } catch (err) {
            console.error('OAuth callback error:', err);
            error = 'Authentication process encountered an error';
            
            // Redirect after showing error
            setTimeout(() => {
                goto('/', { replaceState: true });
            }, 2000);
        }
    });
</script>

<div class="auth-callback">
    {#if error}
        <div class="error-message">
            <p>{error}</p>
            <p>Redirecting to home page...</p>
        </div>
    {:else}
        <div class="spinner"></div>
        <h2>Signing you in...</h2>
    {/if}
</div>

<style>
    .auth-callback {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        text-align: center;
        padding: 1rem;
    }
    
    .spinner {
        border: 4px solid rgba(0, 0, 0, 0.1);
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border-left-color: #2563eb;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    @keyframes spin {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }
    
    h2 {
        color: #4b5563;
        font-weight: 500;
    }
    
    .error-message {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 1.5rem;
        border-radius: 0.5rem;
        max-width: 400px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
</style>
