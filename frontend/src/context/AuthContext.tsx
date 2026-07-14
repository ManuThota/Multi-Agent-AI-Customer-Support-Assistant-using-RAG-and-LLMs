'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
    token: string | null;
    user: { full_name: string; email: string } | null;
    isAuthenticated: boolean;
    login: (token: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [token, setToken] = useState<string | null>(null);
    const [user, setUser] = useState<{ full_name: string; email: string } | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const savedToken = localStorage.getItem('auth_token');
        if (savedToken) {
            setToken(savedToken);
            fetchUserProfile(savedToken);
        } else {
            setLoading(false);
        }
    }, []);

    const fetchUserProfile = async (authToken: string) => {
        try {
            // Calls the new lightweight user profile endpoint instead of analytics
            const response = await fetch('http://127.0.0.1:8000/api/auth/me', {
                headers: {
                    Authorization: `Bearer ${authToken}`,
                },
            });
            if (response.ok) {
                const data = await response.json();
                setUser({
                    full_name: data.full_name,
                    email: data.email,
                });
            } else {
                // Token is invalid/expired
                logout();
            }
        } catch (error) {
            console.error('Failed to fetch profile:', error);
            logout();
        } finally {
            setLoading(false);
        }
    };

    const login = async (newToken: string) => {
        localStorage.setItem('auth_token', newToken);
        setToken(newToken);
        setLoading(true);
        await fetchUserProfile(newToken);
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
        setLoading(false);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
                <div className="relative w-16 h-16">
                    <div className="absolute inset-0 border-4 border-teal-500/20 rounded-full"></div>
                    <div className="absolute inset-0 border-4 border-t-teal-500 rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    return (
        <AuthContext.Provider value={{ token, user, isAuthenticated: !!token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};