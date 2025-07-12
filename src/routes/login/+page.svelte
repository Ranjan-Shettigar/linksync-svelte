<script lang="ts">
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    
    onMount(() => {
        // Redirect to homepage - login is handled directly from navbar
        goto('/');
    });
</script>

<div class="redirecting">
    <p>Redirecting to homepage...</p>
</div>

<style>
    .redirecting {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        font-size: 1.2rem;
        color: #6b7280;
    }
</style>
