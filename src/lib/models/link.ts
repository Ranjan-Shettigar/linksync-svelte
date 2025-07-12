// Link model interface
export interface Link {
    id?: string;
    url: string;
    name: string;
    description: string;
    tags: string[];
    visibility: 'public' | 'private';
    user: string; // User ID who created the link
    favicon?: string; // URL to the favicon/logo
    created?: string;
    updated?: string;
}

// Link creation interface (used for forms)
export interface LinkFormData {
    url: string;
    name: string;
    description: string;
    tags: string;
    visibility: 'public' | 'private';
}
