import { useState, useEffect } from 'react';

export interface TeamResult {
    id: number;
    name: string;
    code: string | null;
    country: string;
    logo: string;
    venue: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useTeamSearch(debounceMs = 400) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<TeamResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (!query || query.length < 3) {
            setResults([]);
            return;
        }

        const handler = setTimeout(async () => {
            setIsLoading(true);
            try {
                const res = await fetch(`${API_URL}/api/teams?q=${encodeURIComponent(query)}`);
                if (!res.ok) throw new Error('Failed to fetch teams');
                const data = await res.json();
                setResults(data.teams || []);
            } catch (error) {
                console.error("Team search failed:", error);
                setResults([]);
            } finally {
                setIsLoading(false);
            }
        }, debounceMs);

        return () => clearTimeout(handler);
    }, [query, debounceMs]);

    return { query, setQuery, results, isLoading };
}
