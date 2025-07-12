<script lang="ts">
    import { onMount } from 'svelte';
    import { initAuth, currentUser, authLoaded, isAuthenticated } from '$lib/services/pocketbase';
    import Navbar from '$lib/components/Navbar.svelte';
    import '../app.css';
    
    // Import debug helper in development
    if (import.meta.env.DEV) {
        import('$lib/debug-auth');
    }
    
    let authInitialized = false;
    
    onMount(async () => {
        if (!authInitialized) {
            authInitialized = true;
            console.log('Layout mounted, initializing auth...');
            
            // Initialize authentication
            await initAuth();
            
            // Log the authentication state for debugging
            authLoaded.subscribe(loaded => {
                if (loaded) {
                    console.log('Auth loaded. Authenticated:', $isAuthenticated, 'User:', !!$currentUser);
                }
            });
            
            // Also log when authentication status changes
            isAuthenticated.subscribe(auth => {
                console.log('Authentication status changed:', auth);
            });
        }
    });
</script>

<div class="app">
    <Navbar />
    <main>
        <slot></slot>
    </main>
</div>

<style>
    .app {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }
    
    main {
        flex: 1;
        background-color: #f9fafb;
    }
</style>
