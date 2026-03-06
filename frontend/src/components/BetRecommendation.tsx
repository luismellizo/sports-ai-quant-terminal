'use client';

import { BetRecommendation as BetRec } from '@/types';

interface BetRecommendationProps {
    bet: BetRec;
}

const RISK_COLORS: Record<string, string> = {
    LOW: 'var(--accent-green)',
    MEDIUM: 'var(--accent-cyan)',
    HIGH: 'var(--accent-orange)',
    EXTREME: 'var(--accent-red)',
};

const CONFIDENCE_COLORS: Record<string, string> = {
    'LOW': 'var(--accent-red)',
    'MEDIUM': 'var(--accent-orange)',
    'HIGH': 'var(--accent-green)',
    'VERY HIGH': 'var(--accent-green)',
};

export default function BetRecommendation({ bet }: BetRecommendationProps) {
    return (
        <div
            className="panel animate-fade-in-up"
            style={{
                borderColor: 'var(--accent-green)',
                boxShadow: '0 0 20px rgba(0, 255, 136, 0.1)',
            }}
        >
            <div className="panel-header" style={{ color: 'var(--accent-green)' }}>
                <span style={{ fontSize: '14px' }}>◆</span>
                APUESTA RECOMENDADA
                <span style={{
                    marginLeft: 'auto',
                    padding: '3px 10px',
                    borderRadius: '3px',
                    fontSize: '11px',
                    fontWeight: 700,
                    background: `${CONFIDENCE_COLORS[bet.confidence]}20`,
                    color: CONFIDENCE_COLORS[bet.confidence],
                    border: `1px solid ${CONFIDENCE_COLORS[bet.confidence]}40`,
                }}>
                    {bet.confidence === 'VERY HIGH' ? 'MUY ALTA' :
                        bet.confidence === 'HIGH' ? 'ALTA' :
                        bet.confidence === 'MEDIUM' ? 'MEDIA' : 'BAJA'}
                </span>
            </div>
            <div className="panel-body">
                {bet.recommendation_style && (
                    <div style={{
                        marginBottom: '12px',
                        textAlign: 'center',
                        fontSize: '11px',
                        letterSpacing: '1.4px',
                        color: bet.recommendation_style === 'GANARLA' ? 'var(--accent-green)' : 'var(--accent-orange)',
                        fontWeight: 700,
                    }}>
                        {bet.recommendation_style === 'GANARLA' ? 'PERFIL: PARA GANARLA' : 'PERFIL: PARA ARRIESGARSE'}
                    </div>
                )}

                {/* Main recommendation */}
                <div style={{
                    textAlign: 'center',
                    padding: '16px',
                    marginBottom: '12px',
                    background: 'var(--bg-primary)',
                    borderRadius: '4px',
                    border: '1px solid rgba(0, 255, 136, 0.15)',
                }}>
                    <div style={{
                        fontSize: '13px',
                        color: 'var(--text-muted)',
                        marginBottom: '6px',
                        textTransform: 'uppercase',
                        letterSpacing: '1.5px',
                    }}>
                        {bet.bet_type === 'Home Win' ? 'GANA LOCAL' :
                            bet.bet_type === 'Away Win' ? 'GANA VISITA' :
                                bet.bet_type === 'Draw' ? 'EMPATE' : bet.bet_type}
                    </div>
                    <div style={{
                        fontSize: '28px',
                        fontWeight: 700,
                        color: 'var(--accent-green)',
                        textShadow: '0 0 20px rgba(0, 255, 136, 0.3)',
                    }}>
                        {bet.team === 'Draw' ? 'Empate' : bet.team}
                    </div>
                </div>

                {/* Stats grid */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '8px',
                }}>
                    {[
                        {
                            label: 'PROBABILIDAD',
                            value: `${(bet.probability * 100).toFixed(1)}%`,
                            color: 'var(--accent-cyan)',
                        },
                        {
                            label: 'CUOTA DE MERCADO',
                            value: bet.market_odds.toFixed(2),
                            color: 'var(--text-primary)',
                        },
                        {
                            label: 'VENTAJA (VALUE EDGE)',
                            value: `+${(bet.value_edge * 100).toFixed(1)}%`,
                            color: 'var(--accent-green)',
                        },
                        {
                            label: 'STAKE (APUESTA)',
                            value: `${bet.recommended_stake_pct.toFixed(1)}% bankroll`,
                            color: 'var(--accent-orange)',
                        },
                        {
                            label: 'DIF. DE CONFIANZA',
                            value: `${bet.confidence_score.toFixed(1)} / 10`,
                            color: CONFIDENCE_COLORS[bet.confidence],
                        },
                        {
                            label: 'NIVEL DE RIESGO',
                            value: bet.risk_level === 'EXTREME' ? 'EXTREMO' :
                                bet.risk_level === 'HIGH' ? 'ALTO' :
                                    bet.risk_level === 'MEDIUM' ? 'MEDIO' : 'BAJO',
                            color: RISK_COLORS[bet.risk_level],
                        },
                    ].map(({ label, value, color }) => (
                        <div key={label} style={{
                            padding: '8px',
                            background: 'var(--bg-primary)',
                            borderRadius: '4px',
                            border: '1px solid var(--border-primary)',
                        }}>
                            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>
                                {label}
                            </div>
                            <div style={{ fontSize: '16px', fontWeight: 600, color }}>
                                {value}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
