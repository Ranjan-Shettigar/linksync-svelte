<script lang="ts">
    import { currentUser, logout, authenticateWithGoogle, isAuthenticated } from '$lib/services/pocketbase';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    
    let isLoggingIn = false;
    let loginError = '';
    
    onMount(() => {
        // Reset login state on mount
        isLoggingIn = false;
        
        // Listen for authentication changes
        isAuthenticated.subscribe(auth => {
            if (auth) {
                // If user just authenticated, reset the login state
                isLoggingIn = false;
            }
        });
    });
    
    function handleLogout() {
        isLoggingIn = false; // Reset login state before logout
        logout();
        goto('/');
    }
    
    async function handleLogin() {
        if (isLoggingIn) return; // Prevent multiple clicks
        
        isLoggingIn = true;
        loginError = '';
        
        try {
            await authenticateWithGoogle();
            // The redirect to Google's auth page will happen automatically
            // After successful auth, the callback page will handle the redirect
        } catch (err) {
            loginError = 'Authentication failed. Please try again.';
            console.error('Login error:', err);
            isLoggingIn = false;
        }
    }
</script>

<nav class="navbar">
    <div class="container">
        <a href="/" class="brand">LinkSync</a>
        
        <div class="nav-links">
            {#if $currentUser}
                <a href="/links" class="nav-link">My Links</a>
                <button class="logout-btn" on:click={handleLogout}>Sign Out</button>
            {:else}
                <button class="login-btn" on:click={handleLogin} disabled={isLoggingIn}>
                    {#if !isLoggingIn}
                        <svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
                            <g transform="matrix(1, 0, 0, 1, 0, 0)">
                                <path d="M21.35,11.1H12v3.2h5.59c-0.5,2.6-2.84,4.62-5.59,4.62c-3.31,0-6-2.69-6-6s2.69-6,6-6c1.55,0,2.95,0.6,4.07,1.56l2.37-2.37 C16.55,4.43,14.39,3.5,12,3.5c-4.97,0-9,4.03-9,9s4.03,9,9,9c5.08,0,8.5-3.58,8.5-8.73C20.5,12.01,20.4,11.37,21.35,11.1z" fill="currentColor"></path>
                            </g>
                        </svg>
                    {/if}
                    {isLoggingIn ? 'Connecting...' : 'Continue with Google'}
                </button>
            {/if}
        </div>
    </div>
</nav>

{#if loginError}
    <div class="error-toast">
        {loginError}
        <button class="close-btn" on:click={() => loginError = ''}>×</button>
    </div>
{/if}

<style>
    .navbar {
        background-color: white;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        padding: 1rem 0;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .brand {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2563eb;
        text-decoration: none;
    }
    
    .brand:hover {
        text-decoration: none;
    }
    
    .nav-links {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    
    .nav-link {
        color: #4b5563;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }
    
    .nav-link:hover {
        color: #2563eb;
        text-decoration: none;
    }
    
    .login-btn, .logout-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
        border: none;
    }
    
    .login-btn {
        background-color: white;
        color: #333;
        border: 1px solid #dadce0;
        text-decoration: none;
    }
    
    .login-btn:hover:not(:disabled) {
        background-color: #f8f9fa;
        text-decoration: none;
    }
    
    .login-btn:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
    
    .logout-btn {
        background-color: #f3f4f6;
        color: #4b5563;
        border: none;
    }
    
    .logout-btn:hover {
        background-color: #e5e7eb;
    }
    
    .error-toast {
        position: fixed;
        top: 1rem;
        right: 1rem;
        background-color: #f44336;
        color: white;
        padding: 1rem;
        border-radius: 0.375rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        z-index: 1000;
    }
    
    .close-btn {
        background: none;
        border: none;
        color: white;
        font-size: 1.25rem;
        line-height: 1;
        cursor: pointer;
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
    }
</style>
