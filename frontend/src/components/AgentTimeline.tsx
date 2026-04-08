'use client';

import { AgentEvent } from '@/types';

interface AgentTimelineProps {
    agents: AgentEvent[];
}

const AGENT_ICONS: Record<string, string> = {
    NLPAgent: '🧠',
    FixtureResolverAgent: '🧭',
    ContextAgent: '🔍',
    HistoryAgent: '📊',
    LineupAgent: '👥',
    SentimentAgent: '💬',
    EloAgent: '📈',
    OddsAgent: '💰',
    FeatureAgent: '⚙️',
    PoissonAgent: '🎯',
    MLAgent: '🤖',
    MonteCarloAgent: '🎲',
    MarketEdgeAgent: '📉',
    RiskAgent: '🛡️',
    SynthesisAgent: '🏁',
};

const AGENT_DESCRIPTIONS: Record<string, string> = {
    NLPAgent: 'Interpreta la petición en lenguaje natural',
    FixtureResolverAgent: 'Resuelve fixture y equipos real',
    ContextAgent: 'Standings y estadísticas de temporada',
    HistoryAgent: 'Historial H2H entre equipos',
    LineupAgent: 'Alineaciones, lesiones y suspensiones',
    SentimentAgent: 'Sentimiento en noticias recientes',
    EloAgent: 'Rating ELO dinámico de equipos',
    OddsAgent: 'Análisis de cuotas del mercado',
    FeatureAgent: 'Vector de features para ML',
    PoissonAgent: 'Distribución de goles (Poisson)',
    MLAgent: 'Ensemble ML — probabilidades finales',
    MonteCarloAgent: '50K simulaciones Monte Carlo',
    MarketEdgeAgent: 'Ineficiencias modelo vs. mercado',
    RiskAgent: 'Evaluación de riesgo profesional',
    SynthesisAgent: 'Executive Summary y recomendación',
};

export default function AgentTimeline({ agents }: AgentTimelineProps) {
    if (agents.length === 0) return null;

    const completed = agents.filter(a => a.status === 'completed').length;
    const total = agents.length;
    const progress = (completed / Math.max(total, 15)) * 100;
    const isRunning = agents.some(a => a.status === 'running');

    return (
        <div className="animate-fade-in-up" style={{ 
            border: '1px solid var(--border-active)', 
            padding: '24px', 
            background: 'var(--bg-primary)',
            marginBottom: '32px'
        }}>
            {/* Header with progress */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className={isRunning ? 'animate-blink' : ''} style={{ 
                        width: '12px', height: '12px', 
                        background: isRunning ? 'var(--text-primary)' : completed === total ? 'var(--accent-green)' : 'var(--border-primary)'
                    }} />
                    <span style={{ fontFamily: 'var(--font-doto), monospace', fontSize: '16px', letterSpacing: '4px', textTransform: 'uppercase', color: 'var(--text-primary)' }}>
                        RED_DE_AGENTES.exe
                    </span>
                    <span style={{
                        marginLeft: 'auto',
                        color: isRunning ? 'var(--text-primary)' : 'var(--accent-green)',
                        fontFamily: 'var(--font-space-mono), monospace',
                        fontSize: '14px',
                        fontWeight: 700,
                        letterSpacing: '2px'
                    }}>
                        {completed}/{total > 0 ? total : 15}
                        <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: '12px', fontSize: '12px' }}>
                            {isRunning ? '[ PROCESANDO ]' : completed === total ? '[ COMPLETO ]' : ''}
                        </span>
                    </span>
                </div>
                {/* Progress bar */}
                <div style={{
                    width: '100%',
                    height: '2px',
                    background: 'var(--border-primary)',
                }}>
                    <div style={{
                        width: `${progress}%`,
                        height: '100%',
                        background: isRunning ? 'var(--text-primary)' : 'var(--accent-green)',
                        transition: 'width 0.2s ease-out',
                    }} />
                </div>
            </div>

            {/* Agent Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                gap: '16px',
            }}>
                {agents.map((agent, i) => {
                    const icon = AGENT_ICONS[agent.name] || '◆';
                    const isActive = agent.status === 'running';
                    const isDone = agent.status === 'completed';
                    const isErr = agent.status === 'error' || agent.status === 'timeout';
                    const description = AGENT_DESCRIPTIONS[agent.name];

                    return (
                        <div
                            key={i}
                            className="animate-fade-in-up agent-card-wrapper"
                            style={{
                                position: 'relative',
                                animationDelay: `${i * 30}ms`,
                            }}
                        >
                            {/* Tooltip */}
                            {description && (
                                <div className="agent-tooltip" style={{ borderRadius: '0', border: '1px solid var(--text-primary)', fontFamily: 'var(--font-space-mono)', fontSize: '12px' }}>
                                    {description}
                                    <div className="agent-tooltip-arrow" style={{ display: 'none' }} />
                                </div>
                            )}

                            {/* Card */}
                            <div
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    padding: '16px',
                                    background: isActive 
                                        ? 'var(--text-primary)' 
                                        : 'transparent',
                                    border: `1px solid ${isActive 
                                        ? 'var(--text-primary)' 
                                        : isDone 
                                            ? 'var(--accent-green)' 
                                            : isErr 
                                                ? 'var(--accent-red)' 
                                                : 'var(--border-primary)'}`,
                                    transition: 'all 0.1s ease',
                                    cursor: 'default',
                                    minHeight: '110px'
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                    <span style={{
                                        fontSize: '20px',
                                        filter: isActive ? 'brightness(0)' : !isDone ? 'grayscale(1) opacity(0.3)' : 'none',
                                    }}>
                                        {icon}
                                    </span>
                                    {isActive && (
                                        <div className="animate-blink" style={{ width: '8px', height: '14px', background: '#000000' }} />
                                    )}
                                    {isDone && (
                                        <div style={{ width: '8px', height: '14px', background: 'var(--accent-green)' }} />
                                    )}
                                </div>

                                <div style={{ flex: 1 }}>
                                    <div style={{
                                        fontSize: '12px',
                                        fontWeight: 700,
                                        color: isActive ? '#000000' : isDone ? 'var(--accent-green)' : 'var(--text-muted)',
                                        fontFamily: 'var(--font-space-mono), monospace',
                                        textTransform: 'uppercase',
                                        letterSpacing: '1px',
                                        lineHeight: '1.4',
                                        marginBottom: '8px'
                                    }}>
                                        {agent.label}
                                    </div>
                                </div>

                                <div style={{
                                    fontSize: '11px',
                                    fontFamily: 'var(--font-doto), monospace',
                                    color: isActive ? 'rgba(0,0,0,0.6)' : isDone ? 'var(--accent-green)' : 'var(--text-muted)',
                                    textTransform: 'uppercase',
                                }}>
                                    {isActive && '> ejecutando...'}
                                    {isDone && `[ OK ] ${agent.execution_time_ms?.toFixed(0)}ms`}
                                    {agent.status === 'timeout' && '[ WARN ] timeout'}
                                    {agent.status === 'error' && '[ FAIL ] error'}
                                    {agent.status === 'pending' && '- espera -'}
                                    {agent.status === 'skipped' && '> omitido'}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
