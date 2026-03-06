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
};

const STATUS_COLORS: Record<string, string> = {
    completed: 'var(--accent-green)',
    running: 'var(--accent-cyan)',
    pending: 'var(--text-muted)',
    error: 'var(--accent-red)',
};

export default function AgentTimeline({ agents }: AgentTimelineProps) {
    if (agents.length === 0) return null;

    const completed = agents.filter(a => a.status === 'completed').length;
    const total = agents.length;
    const progress = (completed / Math.max(total, 13)) * 100;
    const isRunning = agents.some(a => a.status === 'running');

    return (
        <div className="panel animate-fade-in-up">
            {/* Header with progress */}
            <div className="panel-header" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`status-dot ${isRunning ? 'active' : completed === total ? 'active' : 'pending'}`} />
                    <span style={{ fontSize: '12px', letterSpacing: '1.5px' }}>
                        RED DE AGENTES
                    </span>
                    <span style={{
                        marginLeft: 'auto',
                        color: isRunning ? 'var(--accent-cyan)' : 'var(--accent-green)',
                        fontSize: '12px',
                        fontWeight: 700,
                    }}>
                        {completed}/{total > 0 ? total : 13}
                        <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: '6px', fontSize: '10px' }}>
                            {isRunning ? 'PROCESANDO...' : completed === total ? 'COMPLETO' : ''}
                        </span>
                    </span>
                </div>
                {/* Progress bar */}
                <div style={{
                    width: '100%',
                    height: '3px',
                    background: 'var(--bg-primary)',
                    borderRadius: '2px',
                    overflow: 'hidden',
                }}>
                    <div style={{
                        width: `${progress}%`,
                        height: '100%',
                        background: isRunning
                            ? 'linear-gradient(90deg, var(--accent-cyan), var(--accent-green))'
                            : 'var(--accent-green)',
                        borderRadius: '2px',
                        transition: 'width 0.5s ease-out',
                        boxShadow: isRunning ? '0 0 8px var(--accent-cyan)' : 'none',
                    }} />
                </div>
            </div>

            {/* Agent Grid */}
            <div className="panel-body" style={{ padding: '16px' }}>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                    gap: '8px',
                }}>
                    {agents.map((agent, i) => {
                        const icon = AGENT_ICONS[agent.name] || '◆';
                        const isActive = agent.status === 'running';
                        const isDone = agent.status === 'completed';
                        const isErr = agent.status === 'error';

                        return (
                            <div
                                key={i}
                                className="animate-fade-in-up"
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    padding: '10px 12px',
                                    borderRadius: '6px',
                                    background: isActive
                                        ? 'rgba(0, 212, 255, 0.08)'
                                        : isDone
                                            ? 'rgba(0, 255, 136, 0.04)'
                                            : 'var(--bg-primary)',
                                    border: `1px solid ${isActive
                                        ? 'rgba(0, 212, 255, 0.3)'
                                        : isDone
                                            ? 'rgba(0, 255, 136, 0.15)'
                                            : isErr
                                                ? 'rgba(255, 59, 92, 0.3)'
                                                : 'var(--border-primary)'}`,
                                    animationDelay: `${i * 60}ms`,
                                    transition: 'all 0.3s ease',
                                    position: 'relative',
                                    overflow: 'hidden',
                                }}
                            >
                                {/* Pulse animation for running agent */}
                                {isActive && (
                                    <div style={{
                                        position: 'absolute',
                                        inset: 0,
                                        background: 'linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.05), transparent)',
                                        animation: 'shimmer 1.5s infinite',
                                    }} />
                                )}

                                {/* Agent icon */}
                                <span style={{
                                    fontSize: '18px',
                                    filter: isDone ? 'none' : isActive ? 'none' : 'grayscale(1) opacity(0.4)',
                                    transition: 'filter 0.3s',
                                }}>
                                    {icon}
                                </span>

                                {/* Agent info */}
                                <div style={{ flex: 1, minWidth: 0, position: 'relative', zIndex: 1 }}>
                                    <div style={{
                                        fontSize: '11px',
                                        fontWeight: 600,
                                        color: STATUS_COLORS[agent.status],
                                        wordBreak: 'break-word',
                                        lineHeight: '1.4',
                                    }}>
                                        {agent.label}
                                    </div>
                                    <div style={{
                                        fontSize: '10px',
                                        color: 'var(--text-muted)',
                                        marginTop: '2px',
                                    }}>
                                        {isActive && '⟳ ejecutando...'}
                                        {isDone && `✓ ${agent.execution_time_ms?.toFixed(0)}ms`}
                                        {isErr && '✗ error'}
                                        {agent.status === 'pending' && '○ en espera'}
                                    </div>
                                </div>

                                {/* Status indicator */}
                                <div style={{
                                    width: '8px',
                                    height: '8px',
                                    borderRadius: '50%',
                                    background: STATUS_COLORS[agent.status],
                                    boxShadow: isActive
                                        ? `0 0 8px ${STATUS_COLORS[agent.status]}`
                                        : isDone
                                            ? `0 0 4px ${STATUS_COLORS[agent.status]}`
                                            : 'none',
                                    animation: isActive ? 'pulse-glow 1.5s ease-in-out infinite' : 'none',
                                    flexShrink: 0,
                                    position: 'relative',
                                    zIndex: 1,
                                }} />
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
