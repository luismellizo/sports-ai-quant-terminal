'use client';

import { ProbabilityDistribution } from '@/types';

interface ProbabilityBarsProps {
    probabilities: ProbabilityDistribution;
    homeTeam: string;
    awayTeam: string;
}

const BAR_COLORS = {
    home_win: { bar: 'var(--accent-green)', glow: 'var(--glow-green)' },
    draw: { bar: 'var(--accent-cyan)', glow: 'var(--glow-cyan)' },
    away_win: { bar: 'var(--accent-orange)', glow: 'var(--glow-orange)' },
};

export default function ProbabilityBars({ probabilities, homeTeam, awayTeam }: ProbabilityBarsProps) {
    const items = [
        { key: 'home_win' as const, label: `${homeTeam} (Local)`, value: probabilities.home_win },
        { key: 'draw' as const, label: 'Empate', value: probabilities.draw },
        { key: 'away_win' as const, label: `${awayTeam} (Visita)`, value: probabilities.away_win },
    ];

    return (
        <div className="panel animate-fade-in-up">
            <div className="panel-header">
                <span style={{ color: 'var(--accent-cyan)' }}>◆</span>
                DISTRIBUCIÓN DE PROBABILIDAD
            </div>
            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {items.map(item => {
                    const colors = BAR_COLORS[item.key];
                    return (
                        <div key={item.key}>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                marginBottom: '4px',
                                fontSize: '13px',
                            }}>
                                <span style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
                                <span style={{ color: colors.bar, fontWeight: 700, fontSize: '15px' }}>{item.value.toFixed(1)}%</span>
                            </div>
                            <div style={{
                                height: '10px',
                                background: 'var(--bg-primary)',
                                borderRadius: '4px',
                                overflow: 'hidden',
                                position: 'relative',
                            }}>
                                <div
                                    style={{
                                        height: '100%',
                                        width: `${item.value}%`,
                                        background: `linear-gradient(90deg, ${colors.bar}88, ${colors.bar})`,
                                        borderRadius: '4px',
                                        boxShadow: `0 0 10px ${colors.bar}40`,
                                        transition: 'width 1s ease-out',
                                    }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
