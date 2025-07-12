// Development helper for debugging authentication issues
import { currentUser, isAuthenticated, authLoaded } from '$lib/services/pocketbase';
import { browser } from '$app/environment';

if (browser && import.meta.env.DEV) {
    // Add global debugging functions
    (window as any).debugAuth = {
        // Check current auth state
        checkState: () => {
            console.log('=== Auth Debug Info ===');
            console.log('Current User:', currentUser);
            console.log('Is Authenticated:', isAuthenticated);
            console.log('Auth Loaded:', authLoaded);
            
            // Check localStorage
            const stored = localStorage.getItem('pocketbase_auth_v2');
            console.log('Stored Auth Data:', stored ? JSON.parse(stored) : 'None');
            
            // Check PocketBase auth store
            const pb = (window as any).pb;
            if (pb) {
                console.log('PB Auth Valid:', pb.authStore.isValid);
                console.log('PB Auth Model:', pb.authStore.model);
                console.log('PB Auth Token:', pb.authStore.token ? 'Present' : 'None');
            }
            console.log('====================');
        },
        
        // Clear all auth data
        clearAll: () => {
            localStorage.removeItem('pocketbase_auth_v2');
            localStorage.removeItem('pocketbase_auth');
            console.log('All auth data cleared');
        }
    };
    
    console.log('Auth debugging available: window.debugAuth.checkState() and window.debugAuth.clearAll()');
}
