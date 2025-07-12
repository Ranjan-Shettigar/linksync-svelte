import PocketBase from 'pocketbase';
import { writable, type Writable } from 'svelte/store';
import { POCKETBASE_URL } from '$lib/env';
import { browser } from '$app/environment';

// Create a PocketBase client instance with optional auto-cancellation
const pb = new PocketBase(POCKETBASE_URL);

// Disable auto cancellation if we're in a server environment to prevent issues
if (!browser) {
    pb.autoCancellation(false);
}

// Create stores for authentication state
export const currentUser: Writable<any> = writable(null);
export const authLoaded: Writable<boolean> = writable(false);
export const isAuthenticated: Writable<boolean> = writable(false);

// Authentication storage key
const AUTH_STORAGE_KEY = 'pocketbase_auth_v2';

// Load authentication data from localStorage
function loadAuthFromStorage(): { token: string; model: any } | null {
    if (!browser) return null;
    
    try {
        const storedAuth = localStorage.getItem(AUTH_STORAGE_KEY);
        if (!storedAuth) return null;
        
        const authData = JSON.parse(storedAuth);
        
        // Validate the structure
        if (!authData || !authData.token || !authData.model || !authData.model.id) {
            console.warn('Invalid auth data structure in localStorage');
            localStorage.removeItem(AUTH_STORAGE_KEY);
            return null;
        }
        
        // Check if token is expired (basic check)
        const tokenParts = authData.token.split('.');
        if (tokenParts.length === 3) {
            try {
                const payload = JSON.parse(atob(tokenParts[1]));
                const now = Math.floor(Date.now() / 1000);
                
                // If token is expired, don't use it
                if (payload.exp && payload.exp < now) {
                    console.warn('Token is expired');
                    localStorage.removeItem(AUTH_STORAGE_KEY);
                    return null;
                }
            } catch (e) {
                console.warn('Failed to parse token payload:', e);
            }
        }
        
        return authData;
    } catch (err) {
        console.error('Error loading auth data from localStorage:', err);
        localStorage.removeItem(AUTH_STORAGE_KEY);
        return null;
    }
}

// Save authentication data to localStorage
function saveAuthToStorage(token: string, model: any): void {
    if (!browser || !token || !model) return;
    
    try {
        const authData = { token, model, savedAt: Date.now() };
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData));
        console.log('Auth data saved to localStorage');
    } catch (err) {
        console.error('Error saving auth data to localStorage:', err);
    }
}

// Clear authentication data
function clearAuthStorage(): void {
    if (!browser) return;
    
    try {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        // Also clear the old key if it exists
        localStorage.removeItem('pocketbase_auth');
        console.log('Auth data cleared from localStorage');
    } catch (err) {
        console.error('Error clearing auth data:', err);
    }
}

// Validate current authentication
async function validateCurrentAuth(): Promise<boolean> {
    if (!pb.authStore.isValid || !pb.authStore.model) {
        return false;
    }
    
    try {
        // Try to make a simple authenticated request to validate the token
        await pb.collection('users').getOne(pb.authStore.model.id);
        return true;
    } catch (error) {
        console.warn('Auth validation failed:', error);
        return false;
    }
}

// Initialize auth state by checking if there's a valid session
export async function initAuth() {
    if (!browser) return;
    
    console.log('Initializing authentication...');
    
    try {
        // First, try to load from localStorage
        const storedAuth = loadAuthFromStorage();
        
        if (storedAuth) {
            console.log('Found stored auth data, validating...');
            
            // Set the auth data in PocketBase
            pb.authStore.save(storedAuth.token, storedAuth.model);
            
            // Validate the authentication
            const isValid = await validateCurrentAuth();
            
            if (isValid) {
                console.log('Auth successfully restored from localStorage');
                currentUser.set(pb.authStore.model);
                isAuthenticated.set(true);
            } else {
                console.warn('Stored auth is invalid, clearing...');
                pb.authStore.clear();
                clearAuthStorage();
                currentUser.set(null);
                isAuthenticated.set(false);
            }
        } else {
            console.log('No stored auth data found');
            currentUser.set(null);
            isAuthenticated.set(false);
        }
    } catch (err) {
        console.error('Error during auth initialization:', err);
        pb.authStore.clear();
        clearAuthStorage();
        currentUser.set(null);
        isAuthenticated.set(false);
    } finally {
        authLoaded.set(true);
    }
    
    // Listen for authentication state changes
    pb.authStore.onChange((token, model) => {
        console.log('PocketBase auth state changed:', !!token, !!model);
        
        if (token && model) {
            currentUser.set(model);
            isAuthenticated.set(true);
            saveAuthToStorage(token, model);
        } else {
            currentUser.set(null);
            isAuthenticated.set(false);
            clearAuthStorage();
        }
    });
    
    // Set up periodic token refresh (every 10 minutes)
    setInterval(async () => {
        if (pb.authStore.isValid && pb.authStore.model) {
            try {
                console.log('Refreshing auth token...');
                const refreshResult = await pb.collection('users').authRefresh();
                if (refreshResult) {
                    console.log('Auth token refreshed successfully');
                }
            } catch (err) {
                console.error('Failed to refresh auth token:', err);
                
                // If refresh fails, try to validate the current token
                const isStillValid = await validateCurrentAuth();
                if (!isStillValid) {
                    console.warn('Token is no longer valid, logging out...');
                    logout();
                }
            }
        }
    }, 10 * 60 * 1000); // Every 10 minutes
}

// Google OAuth2 authentication
export async function authenticateWithGoogle() {
    try {
        console.log('Starting Google authentication...');
        
        // Redirect to Google OAuth2 page
        const authData = await pb.collection('users').authWithOAuth2({ 
            provider: 'google',
            redirectUrl: window.location.origin + '/auth/callback',
            createData: {
                emailVisibility: true,
            }
        });
        
        if (authData && authData.token && authData.record) {
            console.log('Google authentication successful');
            
            // Manually save the auth data to ensure it persists
            saveAuthToStorage(authData.token, authData.record);
            currentUser.set(authData.record);
            isAuthenticated.set(true);
            
            return authData;
        } else {
            throw new Error('Authentication response is incomplete');
        }
    } catch (error) {
        console.error('Google authentication error:', error);
        
        // Clean up on error
        pb.authStore.clear();
        clearAuthStorage();
        currentUser.set(null);
        isAuthenticated.set(false);
        
        throw error;
    }
}

// Log out the current user
export function logout() {
    try {
        console.log('Logging out user...');
        
        // Clear PocketBase auth store
        pb.authStore.clear();
        
        // Clear our stores
        currentUser.set(null);
        isAuthenticated.set(false);
        
        // Clear localStorage
        clearAuthStorage();
        
        console.log('User logged out successfully');
    } catch (error) {
        console.error('Error during logout:', error);
    }
}

// Check if user is currently authenticated
export function checkAuthStatus(): boolean {
    return pb.authStore.isValid && !!pb.authStore.model;
}

// Manually refresh authentication
export async function refreshAuth(): Promise<boolean> {
    if (!pb.authStore.isValid) {
        return false;
    }
    
    try {
        const result = await pb.collection('users').authRefresh();
        if (result) {
            console.log('Manual auth refresh successful');
            return true;
        }
        return false;
    } catch (error) {
        console.error('Manual auth refresh failed:', error);
        return false;
    }
}

// Export the PocketBase instance for direct access if needed
export default pb;
