'use client';

import { MarketEdge } from '@/types';

interface MarketEdgePanelProps {
    edges: MarketEdge[];
    homeTeam: string;
    awayTeam: string;
}

export default function MarketEdgePanel({ edges, homeTeam, awayTeam }: MarketEdgePanelProps) {
    if (edges.length === 0) return null;

    return (
        <div className="panel animate-fade-in-up">
            <div className="panel-header">
                <span style={{ color: 'var(--accent-yellow)' }}>◆</span>
                DETECCIÓN DE INEFICIENCIAS DEL MERCADO
            </div>
            <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {edges.map((edge, i) => {
                    const isValue = edge.is_value_bet;
                    const edgePct = (edge.edge * 100).toFixed(1);
                    const sign = edge.edge >= 0 ? '+' : '';

                    return (
                        <div
                            key={i}
                            style={{
                                display: 'grid',
                                gridTemplateColumns: '1fr 1fr 1fr 1fr',
                                gap: '8px',
                                alignItems: 'center',
                                padding: '8px 10px',
                                background: isValue ? 'rgba(0, 255, 136, 0.05)' : 'var(--bg-primary)',
                                border: `1px solid ${isValue ? 'rgba(0, 255, 136, 0.2)' : 'var(--border-primary)'}`,
                                borderRadius: '4px',
                            }}
                        >
                            <div>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>TIPO</div>
                                <div style={{ fontSize: '13px', fontWeight: 600 }}>{edge.bet_type}</div>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MODELO</div>
                                <div style={{ fontSize: '14px', color: 'var(--accent-cyan)' }}>
                                    {(edge.model_probability * 100).toFixed(1)}%
                                </div>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MERCADO</div>
                                <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                                    {(edge.market_probability * 100).toFixed(1)}%
                                </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>VENTAJA (EDGE)</div>
                                <div style={{
                                    fontSize: '16px',
                                    fontWeight: 700,
                                    color: isValue ? 'var(--accent-green)' : edge.edge < 0 ? 'var(--accent-red)' : 'var(--text-secondary)',
                                }}>
                                    {sign}{edgePct}%
                                    {isValue && <span style={{ marginLeft: '4px', fontSize: '10px' }}>★</span>}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
