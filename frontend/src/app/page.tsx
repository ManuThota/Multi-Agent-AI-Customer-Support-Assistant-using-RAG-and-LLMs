'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';

// Define Interface Types
interface Session {
  id: string;
  title: string;
  created_at: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agents?: string[];
  timestamp: string;
}

interface Analytics {
  total_sessions: number;
  total_messages: number;
  agent_usage: {
    billing: number;
    technical: number;
    product: number;
    complaint: number;
    faq: number;
  };
}

export default function Home() {
  const { token, user, isAuthenticated, login, logout } = useAuth();

  // Auth Screen State
  const [isRegistering, setIsRegistering] = useState(false);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authName, setAuthName] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Chat State
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Panel States
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<Analytics | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom helper
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatLoading]);

  // Load chat sessions if authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchSessions();
      fetchAnalytics();
    }
  }, [isAuthenticated, token]);

  // Fetch messages when active session changes
  useEffect(() => {
    if (activeSessionId && token) {
      fetchHistory(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  // --- API Integrations ---

  const fetchSessions = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0 && !activeSessionId) {
          setActiveSessionId(data[0].id);
        }
      }
    } catch (e) {
      console.error('Error fetching sessions:', e);
    }
  };

  const fetchHistory = async (sessionId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/sessions/${sessionId}/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      }
    } catch (e) {
      console.error('Error fetching history:', e);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/analytics', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAnalyticsData(data);
      }
    } catch (e) {
      console.error('Error fetching analytics:', e);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);

    const url = isRegistering
      ? 'http://127.0.0.1:8000/api/auth/register'
      : 'http://127.0.0.1:8000/api/auth/login';

    const body = isRegistering
      ? JSON.stringify({ email: authEmail, password: authPassword, full_name: authName })
      : JSON.stringify({ email: authEmail, password: authPassword });

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body,
      });

      const data = await res.json();
      if (!res.ok) {
        // Intelligently parse array or nested object validation errors to prevent [object Object]
        let errorMessage = 'Authentication failed';
        if (data && data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
          } else {
            errorMessage = JSON.stringify(data.detail);
          }
        }
        throw new Error(errorMessage);
      }

      if (isRegistering) {
        setIsRegistering(false);
        const loginRes = await fetch('http://127.0.0.1:8000/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: authEmail, password: authPassword }),
        });
        const loginData = await loginRes.json();
        if (loginRes.ok) {
          login(loginData.access_token);
        }
      } else {
        login(data.access_token);
      }
    } catch (err: any) {
      setAuthError(err.message || 'Something went wrong');
    } finally {
      setAuthLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        const newSession = await res.json();
        setSessions(prev => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        setShowAnalytics(false);
      }
    } catch (e) {
      console.error('Error creating session:', e);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeSessionId || chatLoading) return;

    const userText = inputMessage;
    setInputMessage('');
    setChatLoading(true);

    const tempUserMsg: Message = {
      id: Math.random().toString(),
      role: 'user',
      content: userText,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/sessions/${activeSessionId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content: userText }),
      });

      if (res.ok) {
        const data = await res.json();

        const tempAssistantMsg: Message = {
          id: Math.random().toString(),
          role: 'assistant',
          content: data.response,
          agents: data.agents,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, tempAssistantMsg]);

        fetchSessions();
        fetchAnalytics();
      } else {
        throw new Error('Failed to send message');
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: Math.random().toString(),
        role: 'assistant',
        content: 'Sorry, there was an issue communicating with the agents. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const getAgentBadgeColor = (agent: string) => {
    switch (agent.toLowerCase()) {
      case 'billing': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'technical': return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
      case 'product': return 'bg-violet-500/10 text-violet-400 border-violet-500/20';
      case 'complaint': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default: return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen relative flex items-center justify-center overflow-hidden py-12 px-4 sm:px-6 lg:px-8 bg-[#0B0F19]">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-violet-600/10 blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-blue-600/10 blur-[120px] pointer-events-none"></div>

        <div className="w-full max-w-md z-10">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-violet-400 via-indigo-200 to-sky-400">
              TechMart Support
            </h1>
            <p className="mt-2 text-sm text-slate-400">
              Multi-Agent AI Customer Support Portal
            </p>
          </div>

          <div className="bg-white/[0.02] backdrop-blur-xl border border-white/[0.08] shadow-2xl rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-slate-100 mb-6">
              {isRegistering ? 'Create an Account' : 'Welcome Back'}
            </h2>

            {authError && (
              <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
                {authError}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              {isRegistering && (
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Full Name</label>
                  <input
                    type="text"
                    required
                    value={authName}
                    onChange={(e) => setAuthName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full px-4 py-3 bg-slate-900/60 border border-white/[0.08] rounded-xl focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition text-slate-100 placeholder-slate-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Email Address</label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full px-4 py-3 bg-slate-900/60 border border-white/[0.08] rounded-xl focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition text-slate-100 placeholder-slate-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Password</label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 bg-slate-900/60 border border-white/[0.08] rounded-xl focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition text-slate-100 placeholder-slate-500"
                />
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium rounded-xl focus:outline-none transition-all duration-200 transform hover:scale-[1.01] active:scale-[0.99] shadow-lg shadow-violet-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {authLoading ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 text-white mr-2" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </div>
                ) : (
                  isRegistering ? 'Register Account' : 'Sign In'
                )}
              </button>
            </form>

            <div className="mt-6 text-center text-sm">
              <button
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setAuthError('');
                }}
                className="text-violet-400 hover:text-violet-300 font-medium transition"
              >
                {isRegistering ? 'Already have an account? Sign In' : "Don't have an account? Register"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0A0D14]">
      {/* Sidebar */}
      <aside className="w-80 bg-slate-950/80 border-r border-white/[0.06] flex flex-col h-full shrink-0">
        <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-violet-500 animate-pulse"></span>
            <h2 className="font-bold text-slate-100 tracking-wide text-sm uppercase">TechMart Agent Network</h2>
          </div>
        </div>

        <div className="p-4">
          <button
            onClick={createNewSession}
            className="w-full py-3 px-4 bg-white/5 hover:bg-white/10 border border-white/[0.08] text-slate-100 font-medium rounded-xl flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99]"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path>
            </svg>
            New Session
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1 scrollbar-thin scrollbar-thumb-white/5">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => {
                setActiveSessionId(session.id);
                setShowAnalytics(false);
              }}
              className={`w-full text-left p-3 rounded-xl flex items-center gap-3 transition ${activeSessionId === session.id && !showAnalytics
                  ? 'bg-violet-600/20 border border-violet-500/20 text-white'
                  : 'hover:bg-white/[0.02] border border-transparent text-slate-400 hover:text-slate-200'
                }`}
            >
              <svg className="w-5 h-5 shrink-0 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
              <div className="truncate text-sm font-medium">{session.title}</div>
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-white/[0.06] bg-slate-950/40 flex items-center justify-between">
          <div className="flex items-center gap-3 truncate">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-bold shrink-0">
              {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
            </div>
            <div className="truncate">
              <div className="text-sm font-semibold text-slate-200 truncate">{user?.full_name}</div>
              <div className="text-xs text-slate-500 truncate">Customer Portal</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="p-2 hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 rounded-lg transition"
            title="Log Out"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
            </svg>
          </button>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col h-full bg-[#0D101D]/40 relative">
        <div className="absolute top-[-10%] right-[-10%] w-[400px] h-[400px] rounded-full bg-violet-500/5 blur-[100px] pointer-events-none"></div>

        {/* Top Header */}
        <header className="h-16 border-b border-white/[0.06] flex items-center justify-between px-6 z-10 bg-slate-950/20 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <h1 className="font-semibold text-slate-100 text-lg">
              {showAnalytics ? 'Analytics Dashboard' : (sessions.find(s => s.id === activeSessionId)?.title || 'Chat Desk')}
            </h1>
          </div>

          <button
            onClick={() => {
              setShowAnalytics(!showAnalytics);
              if (!showAnalytics) fetchAnalytics();
            }}
            className={`py-2 px-4 rounded-xl border flex items-center gap-2 text-xs font-semibold transition ${showAnalytics
                ? 'bg-violet-600 border-violet-500 text-white'
                : 'bg-white/5 border-white/[0.08] hover:bg-white/10 text-slate-300'
              }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            {showAnalytics ? 'Back to Chat' : 'Admin Panel'}
          </button>
        </header>

        {showAnalytics ? (
          /* --- ADMIN ANALYTICS --- */
          <div className="flex-1 overflow-y-auto p-8 space-y-8 max-w-4xl mx-auto w-full">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-6 backdrop-blur-md flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Conversations</span>
                  <h3 className="text-4xl font-extrabold text-white mt-1">{analyticsData?.total_sessions || 0}</h3>
                </div>
                <div className="w-12 h-12 rounded-xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"></path>
                  </svg>
                </div>
              </div>

              <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-6 backdrop-blur-md flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Messages Exchanged</span>
                  <h3 className="text-4xl font-extrabold text-white mt-1">{analyticsData?.total_messages || 0}</h3>
                </div>
                <div className="w-12 h-12 rounded-xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-6 backdrop-blur-md">
              <h4 className="font-bold text-slate-200 text-lg mb-6">Specialized Agent Trigger Distribution</h4>
              <div className="space-y-5">
                {analyticsData && Object.entries(analyticsData.agent_usage).map(([agent, count]) => {
                  const maxVal = Math.max(...Object.values(analyticsData.agent_usage), 1);
                  const percentage = (count / maxVal) * 100;
                  return (
                    <div key={agent} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="capitalize font-medium text-slate-300">{agent} Agent</span>
                        <span className="font-semibold text-white">{count} triggers</span>
                      </div>
                      <div className="h-3 w-full bg-slate-900 rounded-full overflow-hidden border border-white/[0.04]">
                        <div
                          className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          /* --- CHAT VIEW --- */
          <>
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/5">
              {messages.length === 0 && !chatLoading && (
                <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400 shadow-xl shadow-violet-500/5">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-slate-200">How can we assist you today?</h3>
                  <p className="text-sm text-slate-500">
                    Describe your issue. The agent network will parse your request and pull instructions from our documents.
                  </p>
                </div>
              )}

              {messages.map((message) => {
                const isUser = message.role === 'user';
                return (
                  <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[75%] rounded-2xl px-5 py-4 border shadow-sm ${isUser
                        ? 'bg-violet-600 border-violet-500 text-white rounded-br-none'
                        : 'bg-white/[0.02] border-white/[0.06] text-slate-200 rounded-bl-none'
                      }`}>
                      {!isUser && message.agents && message.agents.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-2">
                          {message.agents.map((agent) => (
                            <span
                              key={agent}
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getAgentBadgeColor(agent)}`}
                            >
                              {agent} Agent
                            </span>
                          ))}
                        </div>
                      )}

                      <p className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>

                      <span className="block text-[10px] mt-2 opacity-40 text-right">
                        {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                );
              })}

              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl rounded-bl-none px-5 py-4 flex flex-col gap-2">
                    <span className="text-[10px] text-violet-400 font-bold uppercase tracking-wider">
                      Routing and Processing request...
                    </span>
                    <div className="flex items-center gap-1.5 py-1">
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-500 animate-bounce duration-500" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-500 animate-bounce duration-500" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-500 animate-bounce duration-500" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <footer className="p-4 border-t border-white/[0.06] bg-slate-950/20 backdrop-blur-md">
              <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={activeSessionId ? "Describe your support issue..." : "Create a new session to begin chatting."}
                  disabled={!activeSessionId || chatLoading}
                  className="flex-1 px-4 py-3 bg-slate-950 border border-white/[0.08] rounded-xl focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 text-slate-200 placeholder-slate-500 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  type="submit"
                  disabled={!activeSessionId || !inputMessage.trim() || chatLoading}
                  className="px-5 py-3 bg-violet-600 hover:bg-violet-500 text-white font-medium rounded-xl flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9-2-9-18-9 18 9-2zm0 0v-8"></path>
                  </svg>
                </button>
              </form>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}