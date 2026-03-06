'use client';

import { MonteCarloData } from '@/types';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

interface MonteCarloChartProps {
    data: MonteCarloData;
}

export default function MonteCarloChart({ data }: MonteCarloChartProps) {
    // Extract and format score distribution
    const allScores = data.score_distribution.map(s => ({
        score: `${s.home_goals}-${s.away_goals}`,
        probability: +(s.probability * 100).toFixed(2),
    }));

    // Find the most likely score object
    const mostLikelyIndex = allScores.findIndex(s => s.score === data.most_likely_score);
    let scoreData = [];

    if (mostLikelyIndex !== -1) {
        // Remove it from the current position
        const mostLikelyScore = allScores.splice(mostLikelyIndex, 1)[0];
        // Ensure most_likely_score is the absolute first item in the chart
        scoreData = [mostLikelyScore, ...allScores].slice(0, 8);
    } else {
        // Fallback
        scoreData = allScores.slice(0, 8);
    }

    return (
        <div className="panel animate-fade-in-up">
            <div className="panel-header">
                <span style={{ color: 'var(--accent-purple)' }}>◆</span>
                SIMULACIÓN DE MONTE CARLO
                <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '11px' }}>
                    {data.simulations.toLocaleString()} sims
                </span>
            </div>
            <div className="panel-body">
                {/* Summary stats */}
                <div className="mc-summary-grid">
                    {[
                        { label: 'Gana Local', value: `${data.home_win_pct}%`, color: 'var(--accent-green)' },
                        { label: 'Empate', value: `${data.draw_pct}%`, color: 'var(--accent-cyan)' },
                        { label: 'Gana Visita', value: `${data.away_win_pct}%`, color: 'var(--accent-orange)' },
                    ].map(stat => (
                        <div key={stat.label} style={{
                            textAlign: 'center',
                            padding: '8px',
                            background: 'var(--bg-primary)',
                            borderRadius: '4px',
                            border: '1px solid var(--border-primary)',
                        }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                                {stat.label}
                            </div>
                            <div style={{ fontSize: '20px', fontWeight: 700, color: stat.color }}>
                                {stat.value}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Most likely score */}
                <div style={{
                    textAlign: 'center',
                    padding: '8px',
                    marginBottom: '16px',
                    background: 'var(--bg-primary)',
                    borderRadius: '4px',
                    border: '1px solid var(--border-primary)',
                }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>RESULTADO MÁS PROBABLE: </span>
                    <span style={{ color: 'var(--accent-yellow)', fontWeight: 700, fontSize: '20px' }}>
                        {data.most_likely_score}
                    </span>
                </div>

                {/* Score distribution chart */}
                {scoreData.length > 0 && (
                    <div className="mc-chart-wrap">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={scoreData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e2035" />
                                <XAxis
                                    dataKey="score"
                                    tick={{ fill: '#8888a8', fontSize: 11 }}
                                    axisLine={{ stroke: '#1e2035' }}
                                />
                                <YAxis
                                    tick={{ fill: '#8888a8', fontSize: 11 }}
                                    axisLine={{ stroke: '#1e2035' }}
                                    tickFormatter={(v) => `${v}%`}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: '#12131d',
                                        border: '1px solid #2a2d4a',
                                        borderRadius: '4px',
                                        color: '#e0e0ec',
                                        fontSize: '12px',
                                        fontFamily: "'JetBrains Mono', monospace",
                                    }}
                                    formatter={(value) => [`${value}%`, 'Probabilidad']}
                                />
                                <Bar dataKey="probability" radius={[3, 3, 0, 0]}>
                                    {scoreData.map((entry, i) => (
                                        <Cell
                                            key={i}
                                            fill={entry.score === data.most_likely_score ? '#00ff88' : i < 3 ? '#00d4ff' : '#555570'}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>
        </div>
    );
}
