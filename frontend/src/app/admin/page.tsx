'use client';

import { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PredictionSummary {
    id: number;
    prediction_id: string;
    created_at: string | null;
    query: string;
    home_team: string;
    away_team: string;
    league: string | null;
    probabilities: { home_win: number; draw: number; away_win: number } | null;
    best_bet: {
        bet_type: string;
        team: string;
        probability: number;
        confidence: string;
        risk_level: string;
        confidence_score: number;
    } | null;
    monte_carlo_summary: {
        most_likely_score: string;
        home_win_pct: number;
        draw_pct: number;
        away_win_pct: number;
    } | null;
    executive_summary: string | null;
    verdict: string | null;
    total_execution_time_ms: number;
    fixture_id: number | null;
    result_data: {
        status: string;
        home_team: string;
        away_team: string;
        goals_home: number | null;
        goals_away: number | null;
        date: string | null;
    } | null;
}

export default function AdminPage() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [token, setToken] = useState('');
    const [user, setUser] = useState('');
    const [password, setPassword] = useState('');
    const [loginError, setLoginError] = useState('');
    const [predictions, setPredictions] = useState<PredictionSummary[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingResults, setLoadingResults] = useState<Record<string, boolean>>({});
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoginError('');

        try {
            const res = await fetch(`${API_URL}/api/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user, password }),
            });

            if (!res.ok) {
                const data = await res.json();
                setLoginError(data.detail || 'Credenciales inválidas');
                return;
            }

            const data = await res.json();
            setToken(data.token);
            setIsAuthenticated(true);
        } catch {
            setLoginError('Error de conexión con el servidor');
        }
    };

    const fetchPredictions = useCallback(async () => {
        if (!token) return;
        setLoading(true);

        try {
            const res = await fetch(`${API_URL}/api/admin/predictions`, {
                headers: { Authorization: `Bearer ${token}` },
            });

            if (res.ok) {
                const data = await res.json();
                setPredictions(data.predictions || []);
            }
        } catch {
            console.error('Error fetching predictions');
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        if (isAuthenticated) {
            fetchPredictions();
        }
    }, [isAuthenticated, fetchPredictions]);

    const handleFetchResult = async (predictionId: string) => {
        setLoadingResults(prev => ({ ...prev, [predictionId]: true }));

        try {
            const res = await fetch(`${API_URL}/api/admin/predictions/${predictionId}/result`, {
                headers: { Authorization: `Bearer ${token}` },
            });

            if (res.ok) {
                const data = await res.json();
                // Update the prediction in the list
                setPredictions(prev =>
                    prev.map(p =>
                        p.prediction_id === predictionId
                            ? { ...p, result_data: data.result }
                            : p
                    )
                );
            }
        } catch {
            console.error('Error fetching result');
        } finally {
            setLoadingResults(prev => ({ ...prev, [predictionId]: false }));
        }
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '—';
        try {
            return new Date(dateStr).toLocaleString('es-CO', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return dateStr;
        }
    };

    // ── Login Screen ──────────────────────────────────────────
    if (!isAuthenticated) {
        return (
            <main className="page-main" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
                <div className="panel" style={{ width: '100%', maxWidth: '400px' }}>
                    <div className="panel-header">
                        <span style={{ color: 'var(--accent-purple)' }}>◆</span>
                        ADMIN — AUTENTICACIÓN
                    </div>
                    <form onSubmit={handleLogin} className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {loginError && (
                            <div style={{
                                padding: '8px 12px',
                                background: 'rgba(255, 59, 92, 0.1)',
                                border: '1px solid var(--accent-red)',
                                borderRadius: '4px',
                                color: 'var(--accent-red)',
                                fontSize: '12px',
                            }}>
                                ✗ {loginError}
                            </div>
                        )}

                        <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '1px', display: 'block', marginBottom: '6px' }}>
                                USUARIO
                            </label>
                            <input
                                type="text"
                                value={user}
                                onChange={e => setUser(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '10px 12px',
                                    background: 'var(--bg-primary)',
                                    border: '1px solid var(--border-primary)',
                                    borderRadius: '4px',
                                    color: 'var(--text-primary)',
                                    fontFamily: "'JetBrains Mono', monospace",
                                    fontSize: '14px',
                                    outline: 'none',
                                }}
                                onFocus={e => (e.target.style.borderColor = 'var(--accent-purple)')}
                                onBlur={e => (e.target.style.borderColor = 'var(--border-primary)')}
                                autoFocus
                            />
                        </div>

                        <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '1px', display: 'block', marginBottom: '6px' }}>
                                CONTRASEÑA
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '10px 12px',
                                    background: 'var(--bg-primary)',
                                    border: '1px solid var(--border-primary)',
                                    borderRadius: '4px',
                                    color: 'var(--text-primary)',
                                    fontFamily: "'JetBrains Mono', monospace",
                                    fontSize: '14px',
                                    outline: 'none',
                                }}
                                onFocus={e => (e.target.style.borderColor = 'var(--accent-purple)')}
                                onBlur={e => (e.target.style.borderColor = 'var(--border-primary)')}
                            />
                        </div>

                        <button
                            type="submit"
                            style={{
                                padding: '10px 16px',
                                background: 'rgba(179, 136, 255, 0.1)',
                                border: '1px solid var(--accent-purple)',
                                borderRadius: '4px',
                                color: 'var(--accent-purple)',
                                fontFamily: "'JetBrains Mono', monospace",
                                fontSize: '13px',
                                fontWeight: 600,
                                letterSpacing: '1px',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                            }}
                            onMouseOver={e => {
                                (e.target as HTMLElement).style.background = 'rgba(179, 136, 255, 0.2)';
                                (e.target as HTMLElement).style.boxShadow = '0 0 15px rgba(179, 136, 255, 0.2)';
                            }}
                            onMouseOut={e => {
                                (e.target as HTMLElement).style.background = 'rgba(179, 136, 255, 0.1)';
                                (e.target as HTMLElement).style.boxShadow = 'none';
                            }}
                        >
                            ▶ INGRESAR
                        </button>
                    </form>
                </div>

                <a href="/" style={{
                    marginTop: '16px',
                    color: 'var(--text-muted)',
                    fontSize: '12px',
                    textDecoration: 'none',
                }}>
                    ← Volver al Terminal
                </a>
            </main>
        );
    }

    // ── Dashboard ─────────────────────────────────────────────
    return (
        <main className="page-main">
            {/* Header */}
            <header className="app-header">
                <div className="app-header-left">
                    <span style={{
                        color: 'var(--accent-purple)',
                        fontSize: '22px',
                        fontWeight: 700,
                        textShadow: '0 0 15px rgba(179, 136, 255, 0.4)',
                        letterSpacing: '3px',
                    }}>
                        ◆ ADMIN PANEL
                    </span>
                    <span style={{
                        fontSize: '11px',
                        color: 'var(--text-muted)',
                        padding: '3px 10px',
                        border: '1px solid var(--border-primary)',
                        borderRadius: '3px',
                        letterSpacing: '1px',
                    }}>
                        PREDICTIONS DASHBOARD
                    </span>
                </div>
                <div className="app-header-right">
                    <span style={{ color: 'var(--accent-green)', fontSize: '11px' }}>
                        ● {predictions.length} predicciones
                    </span>
                    <button
                        onClick={fetchPredictions}
                        style={{
                            padding: '3px 10px',
                            border: '1px solid var(--border-primary)',
                            borderRadius: '3px',
                            color: 'var(--accent-cyan)',
                            background: 'transparent',
                            fontSize: '10px',
                            fontFamily: "'JetBrains Mono', monospace",
                            fontWeight: 600,
                            letterSpacing: '1px',
                            cursor: 'pointer',
                        }}
                    >
                        ↻ REFRESH
                    </button>
                    <a href="/" style={{
                        padding: '3px 10px',
                        border: '1px solid var(--border-primary)',
                        borderRadius: '3px',
                        color: 'var(--accent-green)',
                        textDecoration: 'none',
                        fontSize: '10px',
                        fontWeight: 600,
                        letterSpacing: '1px',
                    }}>
                        ← TERMINAL
                    </a>
                </div>
            </header>

            {/* Stats Bar */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '12px',
            }}>
                <div className="panel" style={{ padding: '12px 16px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px' }}>TOTAL PREDICCIONES</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--accent-cyan)' }}>{predictions.length}</div>
                </div>
                <div className="panel" style={{ padding: '12px 16px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px' }}>CON RESULTADO</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--accent-green)' }}>
                        {predictions.filter(p => p.result_data).length}
                    </div>
                </div>
                <div className="panel" style={{ padding: '12px 16px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px' }}>PENDIENTES</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--accent-orange)' }}>
                        {predictions.filter(p => !p.result_data).length}
                    </div>
                </div>
                <div className="panel" style={{ padding: '12px 16px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px' }}>TIEMPO PROM.</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {predictions.length > 0
                            ? `${(predictions.reduce((sum, p) => sum + (p.total_execution_time_ms || 0), 0) / predictions.length / 1000).toFixed(1)}s`
                            : '—'}
                    </div>
                </div>
            </div>

            {/* Loading */}
            {loading && (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '12px' }}>
                    Cargando predicciones...
                </div>
            )}

            {/* Empty state */}
            {!loading && predictions.length === 0 && (
                <div className="panel" style={{ padding: '40px', textAlign: 'center' }}>
                    <div style={{ fontSize: '32px', marginBottom: '12px', color: 'var(--text-muted)' }}>◆</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                        No hay predicciones registradas aún.
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '8px' }}>
                        Realiza una predicción desde el <a href="/" style={{ color: 'var(--accent-green)' }}>terminal</a> para verla aquí.
                    </div>
                </div>
            )}

            {/* Predictions List */}
            {predictions.map(p => (
                <div key={p.prediction_id} className="panel animate-fade-in-up" style={{ overflow: 'hidden' }}>
                    {/* Row header */}
                    <div
                        style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr auto',
                            alignItems: 'center',
                            padding: '12px 16px',
                            cursor: 'pointer',
                            borderBottom: expandedId === p.prediction_id ? '1px solid var(--border-primary)' : 'none',
                        }}
                        onClick={() => setExpandedId(expandedId === p.prediction_id ? null : p.prediction_id)}
                    >
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                                <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                                    {p.home_team || '?'} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>vs</span> {p.away_team || '?'}
                                </span>
                                {p.league && (
                                    <span style={{
                                        fontSize: '10px',
                                        color: 'var(--accent-cyan)',
                                        padding: '2px 8px',
                                        border: '1px solid rgba(0, 212, 255, 0.2)',
                                        borderRadius: '3px',
                                    }}>
                                        {p.league}
                                    </span>
                                )}
                                {p.result_data && (
                                    <span style={{
                                        fontSize: '10px',
                                        padding: '2px 8px',
                                        background: 'rgba(0, 255, 136, 0.1)',
                                        border: '1px solid rgba(0, 255, 136, 0.3)',
                                        borderRadius: '3px',
                                        color: 'var(--accent-green)',
                                        fontWeight: 600,
                                    }}>
                                        {p.result_data.goals_home ?? '?'} – {p.result_data.goals_away ?? '?'}
                                    </span>
                                )}
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                                <span>{formatDate(p.created_at)}</span>
                                {p.probabilities && (
                                    <span>
                                        L:{p.probabilities.home_win}% E:{p.probabilities.draw}% V:{p.probabilities.away_win}%
                                    </span>
                                )}
                                <span>{(p.total_execution_time_ms / 1000).toFixed(1)}s</span>
                                {p.best_bet && (
                                    <span style={{ color: 'var(--accent-yellow)' }}>
                                        Apuesta: {p.best_bet.bet_type} ({p.best_bet.confidence})
                                    </span>
                                )}
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleFetchResult(p.prediction_id);
                                }}
                                disabled={loadingResults[p.prediction_id]}
                                style={{
                                    padding: '6px 14px',
                                    background: p.result_data ? 'rgba(0, 255, 136, 0.08)' : 'rgba(255, 140, 0, 0.08)',
                                    border: `1px solid ${p.result_data ? 'rgba(0, 255, 136, 0.3)' : 'rgba(255, 140, 0, 0.3)'}`,
                                    borderRadius: '4px',
                                    color: p.result_data ? 'var(--accent-green)' : 'var(--accent-orange)',
                                    fontFamily: "'JetBrains Mono', monospace",
                                    fontSize: '11px',
                                    fontWeight: 600,
                                    cursor: loadingResults[p.prediction_id] ? 'wait' : 'pointer',
                                    opacity: loadingResults[p.prediction_id] ? 0.6 : 1,
                                    whiteSpace: 'nowrap',
                                    transition: 'all 0.2s',
                                }}
                            >
                                {loadingResults[p.prediction_id]
                                    ? '⏳ Consultando...'
                                    : p.result_data
                                        ? '↻ Actualizar Resultado'
                                        : '◆ Llamar Resultado'}
                            </button>
                            <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                                {expandedId === p.prediction_id ? '▲' : '▼'}
                            </span>
                        </div>
                    </div>

                    {/* Expanded detail */}
                    {expandedId === p.prediction_id && (
                        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {/* Result section */}
                            {p.result_data && (
                                <div style={{
                                    padding: '12px 16px',
                                    background: 'rgba(0, 255, 136, 0.04)',
                                    border: '1px solid rgba(0, 255, 136, 0.15)',
                                    borderRadius: '4px',
                                }}>
                                    <div style={{ fontSize: '11px', color: 'var(--accent-green)', letterSpacing: '1px', fontWeight: 600, marginBottom: '8px' }}>
                                        ◆ RESULTADO REAL
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                                        <span style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                                            {p.result_data.home_team} {p.result_data.goals_home ?? '?'}
                                            <span style={{ color: 'var(--text-muted)', margin: '0 8px' }}>–</span>
                                            {p.result_data.goals_away ?? '?'} {p.result_data.away_team}
                                        </span>
                                        <span style={{
                                            fontSize: '11px',
                                            padding: '3px 8px',
                                            background: 'var(--bg-primary)',
                                            borderRadius: '3px',
                                            color: 'var(--text-secondary)',
                                        }}>
                                            {p.result_data.status}
                                        </span>
                                        {p.result_data.date && (
                                            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                                {formatDate(p.result_data.date)}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Prediction summary */}
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                                gap: '12px',
                            }}>
                                {/* Probabilities */}
                                {p.probabilities && (
                                    <div style={{ padding: '10px', background: 'var(--bg-primary)', borderRadius: '4px' }}>
                                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>PROBABILIDADES</div>
                                        <div style={{ display: 'flex', gap: '12px', fontSize: '13px' }}>
                                            <span><span style={{ color: 'var(--accent-green)' }}>L:</span> {p.probabilities.home_win}%</span>
                                            <span><span style={{ color: 'var(--text-muted)' }}>E:</span> {p.probabilities.draw}%</span>
                                            <span><span style={{ color: 'var(--accent-orange)' }}>V:</span> {p.probabilities.away_win}%</span>
                                        </div>
                                    </div>
                                )}

                                {/* Monte Carlo */}
                                {p.monte_carlo_summary && (
                                    <div style={{ padding: '10px', background: 'var(--bg-primary)', borderRadius: '4px' }}>
                                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>MONTE CARLO</div>
                                        <div style={{ fontSize: '13px' }}>
                                            Score más probable: <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{p.monte_carlo_summary.most_likely_score || '—'}</span>
                                        </div>
                                    </div>
                                )}

                                {/* Best bet */}
                                {p.best_bet && (
                                    <div style={{ padding: '10px', background: 'var(--bg-primary)', borderRadius: '4px' }}>
                                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>APUESTA RECOMENDADA</div>
                                        <div style={{ fontSize: '13px' }}>
                                            <span style={{ color: 'var(--accent-yellow)', fontWeight: 600 }}>{p.best_bet.bet_type}</span>
                                            <span style={{ color: 'var(--text-muted)', margin: '0 6px' }}>·</span>
                                            {p.best_bet.team}
                                            <span style={{ color: 'var(--text-muted)', margin: '0 6px' }}>·</span>
                                            <span style={{ color: 'var(--accent-green)' }}>{p.best_bet.confidence}</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Executive summary */}
                            {(p.executive_summary || p.verdict) && (
                                <div style={{ padding: '10px', background: 'var(--bg-primary)', borderRadius: '4px' }}>
                                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '1px', marginBottom: '6px' }}>RESUMEN EJECUTIVO</div>
                                    {p.verdict && (
                                        <div style={{ fontSize: '13px', color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '6px' }}>
                                            {p.verdict}
                                        </div>
                                    )}
                                    {p.executive_summary && (
                                        <div style={{
                                            fontSize: '12px',
                                            color: 'var(--text-secondary)',
                                            lineHeight: '1.7',
                                            maxHeight: '120px',
                                            overflow: 'auto',
                                        }}>
                                            {p.executive_summary}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Query */}
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                Query: <span style={{ color: 'var(--text-secondary)' }}>{p.query}</span>
                                <span style={{ margin: '0 8px' }}>·</span>
                                ID: <span style={{ color: 'var(--text-secondary)' }}>{p.prediction_id}</span>
                            </div>
                        </div>
                    )}
                </div>
            ))}

            {/* Footer */}
            <footer className="status-footer">
                <span>SPORTS AI — ADMIN PANEL v1.0</span>
                <span>DASHBOARD DE PREDICCIONES</span>
                <span>
                    <span style={{ color: 'var(--accent-green)' }}>●</span> CONECTADO
                </span>
            </footer>
        </main>
    );
}
