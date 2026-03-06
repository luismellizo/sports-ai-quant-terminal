import React from 'react';
import { MatchInsights } from '@/types';

interface MatchInsightsPanelProps {
    insights: MatchInsights;
    homeTeam: string;
    awayTeam: string;
}

const PerformanceBar = ({ wins, draws, losses }: { wins: number, draws: number, losses: number }) => {
    const total = wins + draws + losses || 1; // Evitar división por 0
    return (
        <div style={{
            display: 'flex',
            height: '6px',
            width: '100%',
            borderRadius: '3px',
            overflow: 'hidden',
            background: 'var(--bg-panel)',
            marginTop: '6px'
        }}>
            {wins > 0 && <div style={{ width: `${(wins / total) * 100}%`, background: 'var(--accent-green)' }} />}
            {draws > 0 && <div style={{ width: `${(draws / total) * 100}%`, background: 'var(--accent-orange)' }} />}
            {losses > 0 && <div style={{ width: `${(losses / total) * 100}%`, background: 'var(--accent-red)' }} />}
        </div>
    );
}

export default function MatchInsightsPanel({ insights, homeTeam, awayTeam }: MatchInsightsPanelProps) {
    if (!insights) return null;

    return (
        <div className="panel animate-fade-in-up" style={{ animationDelay: '100ms' }}>
            <div className="panel-header">
                <span className="status-dot active" style={{ background: 'var(--accent-purple)', boxShadow: '0 0 8px var(--accent-purple)' }} />
                ANÁLISIS TÁCTICO & HISTÓRICO
            </div>

            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '16px' }}>

                {/* Tactical / Lineup Section */}
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '6px',
                        background: 'rgba(179, 136, 255, 0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--accent-purple)',
                        fontSize: '18px',
                        flexShrink: 0
                    }}>
                        👥
                    </div>
                    <div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>
                            REPORTE DE ALINEACIONES
                        </div>
                        <div style={{ fontSize: '14px', lineHeight: '1.5', color: 'var(--text-primary)' }}>
                            {insights.lineup_summary}
                        </div>
                    </div>
                </div>

                <div style={{ height: '1px', background: 'var(--border-primary)', width: '100%' }} />

                {/* History / Form Section */}
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '6px',
                        background: 'rgba(255, 140, 0, 0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--accent-orange)',
                        fontSize: '18px',
                        flexShrink: 0
                    }}>
                        📊
                    </div>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>
                            MOMENTUM & HISTORIAL (Últ. 5)
                        </div>
                        <div style={{ fontSize: '14px', lineHeight: '1.5', color: 'var(--text-primary)', marginBottom: '8px' }}>
                            {insights.history_summary}
                        </div>

                        <div className="insight-form-grid">
                            <div className="insight-form-team">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{homeTeam}</span>
                                    <span style={{ fontSize: '13px', fontWeight: 700 }}>
                                        <span style={{ color: 'var(--accent-green)' }}>{insights.home_stats.wins_last_5}</span>
                                        <span style={{ color: 'var(--text-muted)', margin: '0 2px' }}>-</span>
                                        <span style={{ color: 'var(--accent-orange)' }}>{insights.home_stats.draws_last_5}</span>
                                        <span style={{ color: 'var(--text-muted)', margin: '0 2px' }}>-</span>
                                        <span style={{ color: 'var(--accent-red)' }}>{insights.home_stats.losses_last_5}</span>
                                    </span>
                                </div>
                                <PerformanceBar
                                    wins={insights.home_stats.wins_last_5}
                                    draws={insights.home_stats.draws_last_5}
                                    losses={insights.home_stats.losses_last_5}
                                />
                            </div>
                            <div className="insight-divider-vertical" />
                            <div className="insight-form-team">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{awayTeam}</span>
                                    <span style={{ fontSize: '13px', fontWeight: 700 }}>
                                        <span style={{ color: 'var(--accent-green)' }}>{insights.away_stats.wins_last_5}</span>
                                        <span style={{ color: 'var(--text-muted)', margin: '0 2px' }}>-</span>
                                        <span style={{ color: 'var(--accent-orange)' }}>{insights.away_stats.draws_last_5}</span>
                                        <span style={{ color: 'var(--text-muted)', margin: '0 2px' }}>-</span>
                                        <span style={{ color: 'var(--accent-red)' }}>{insights.away_stats.losses_last_5}</span>
                                    </span>
                                </div>
                                <PerformanceBar
                                    wins={insights.away_stats.wins_last_5}
                                    draws={insights.away_stats.draws_last_5}
                                    losses={insights.away_stats.losses_last_5}
                                />
                            </div>
                        </div>

                    </div>
                </div>

            </div>
        </div>
    );
}
