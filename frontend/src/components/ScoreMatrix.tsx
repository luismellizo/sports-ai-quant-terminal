'use client';

import { ScoreProb } from '@/types';

interface ScoreMatrixProps {
    scores: ScoreProb[];
    homeTeam: string;
    awayTeam: string;
}

export default function ScoreMatrix({ scores, homeTeam, awayTeam }: ScoreMatrixProps) {
    if (scores.length === 0) return null;

    // Build 6x6 matrix
    const maxGoals = 5;
    const matrix: number[][] = Array.from({ length: maxGoals + 1 }, () =>
        Array(maxGoals + 1).fill(0)
    );

    let maxProb = 0;
    scores.forEach(s => {
        if (s.home_goals <= maxGoals && s.away_goals <= maxGoals) {
            matrix[s.home_goals][s.away_goals] = s.probability;
            maxProb = Math.max(maxProb, s.probability);
        }
    });

    const getHeatColor = (prob: number): string => {
        if (prob === 0) return 'transparent';
        const intensity = prob / maxProb;
        if (intensity > 0.7) return `rgba(0, 255, 136, ${0.3 + intensity * 0.5})`;
        if (intensity > 0.4) return `rgba(0, 212, 255, ${0.2 + intensity * 0.4})`;
        return `rgba(136, 136, 168, ${0.1 + intensity * 0.3})`;
    };

    return (
        <div className="panel animate-fade-in-up">
            <div className="panel-header">
                <span style={{ color: 'var(--accent-orange)' }}>◆</span>
                MATRIZ DE PROBABILIDAD DE RESULTADOS
            </div>
            <div className="panel-body">
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                        <thead>
                            <tr>
                                <th style={{
                                    padding: '4px 8px',
                                    color: 'var(--text-muted)',
                                    textAlign: 'left',
                                    fontSize: '10px',
                                    borderBottom: '1px solid var(--border-primary)',
                                }}>
                                    {homeTeam.substring(0, 3).toUpperCase()} \ {awayTeam.substring(0, 3).toUpperCase()}
                                </th>
                                {Array.from({ length: maxGoals + 1 }, (_, i) => (
                                    <th key={i} style={{
                                        padding: '4px 8px',
                                        color: 'var(--accent-orange)',
                                        textAlign: 'center',
                                        borderBottom: '1px solid var(--border-primary)',
                                    }}>
                                        {i}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {matrix.map((row, hg) => (
                                <tr key={hg}>
                                    <td style={{
                                        padding: '4px 8px',
                                        color: 'var(--accent-green)',
                                        fontWeight: 600,
                                        borderRight: '1px solid var(--border-primary)',
                                    }}>
                                        {hg}
                                    </td>
                                    {row.map((prob, ag) => (
                                        <td
                                            key={ag}
                                            style={{
                                                padding: '4px 8px',
                                                textAlign: 'center',
                                                background: getHeatColor(prob),
                                                color: prob > 0 ? 'var(--text-primary)' : 'var(--text-muted)',
                                                borderRadius: '2px',
                                                fontWeight: prob === maxProb ? 700 : 400,
                                                transition: 'all 0.3s',
                                            }}
                                        >
                                            {prob > 0 ? `${(prob * 100).toFixed(1)}%` : '·'}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
