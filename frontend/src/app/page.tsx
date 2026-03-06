'use client';

import { useState, useCallback } from 'react';
import TerminalInput from '@/components/TerminalInput';
import AgentTimeline from '@/components/AgentTimeline';
import ProbabilityBars from '@/components/ProbabilityBars';
import ScoreMatrix from '@/components/ScoreMatrix';
import MonteCarloChart from '@/components/MonteCarloChart';
import MarketEdgePanel from '@/components/MarketEdgePanel';
import BetRecommendation from '@/components/BetRecommendation';
import MatchInsightsPanel from '@/components/MatchInsightsPanel';
import { type AgentEvent, type PredictionResult, type SSEEvent } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [agents, setAgents] = useState<AgentEvent[]>([]);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [currentQuery, setCurrentQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = useCallback(async (query: string) => {
    setIsLoading(true);
    setAgents([]);
    setPrediction(null);
    setError(null);
    setCurrentQuery(query);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n').filter(l => l.startsWith('data: '));

        for (const line of lines) {
          try {
            const eventData: SSEEvent = JSON.parse(line.slice(6));

            switch (eventData.event) {
              case 'agent_start':
                setAgents(prev => {
                  const exists = prev.find(a => a.index === eventData.data.index);
                  if (exists) return prev;
                  return [...prev, {
                    index: eventData.data.index,
                    name: eventData.data.name,
                    label: eventData.data.label,
                    status: 'running',
                  }];
                });
                break;

              case 'agent_complete':
                setAgents(prev =>
                  prev.map(a =>
                    a.index === eventData.data.index
                      ? {
                        ...a,
                        status: eventData.data.status as AgentEvent['status'],
                        execution_time_ms: eventData.data.execution_time_ms,
                      }
                      : a
                  )
                );
                break;

              case 'pipeline_complete':
                setPrediction(eventData.data as PredictionResult);
                break;
            }
          } catch {
            // Skip malformed events
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <main style={{
      minHeight: '100vh',
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
      position: 'relative',
      zIndex: 1,
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-primary)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            color: 'var(--accent-green)',
            fontSize: '22px',
            fontWeight: 700,
            textShadow: '0 0 15px rgba(0, 255, 136, 0.4)',
            letterSpacing: '3px',
          }}>
            ◆ SPORTS AI
          </span>
          <span style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            padding: '3px 10px',
            border: '1px solid var(--border-primary)',
            borderRadius: '3px',
            letterSpacing: '1px',
          }}>
            QUANT TERMINAL v1.0
          </span>
        </div>
        <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>
            <span style={{ color: 'var(--accent-green)' }}>●</span> SISTEMA EN LÍNEA
          </span>
          <span>
            {new Date().toLocaleTimeString('en-US', { hour12: false })}
          </span>
        </div>
      </header>

      {/* Terminal Input */}
      <TerminalInput onSubmit={handleAnalyze} isLoading={isLoading} />

      {/* Error */}
      {error && (
        <div className="panel" style={{
          borderColor: 'var(--accent-red)',
          padding: '12px',
          color: 'var(--accent-red)',
          fontSize: '12px',
        }}>
          ✗ ERROR: {error}
          <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>
            — Asegúrate de que el backend esté corriendo en {API_URL}
          </span>
        </div>
      )}

      {/* Current query display */}
      {currentQuery && (
        <div style={{
          fontSize: '13px',
          color: 'var(--text-muted)',
          padding: '8px 14px',
          borderLeft: '3px solid var(--accent-cyan)',
        }}>
          ANALIZANDO: <span style={{ color: 'var(--accent-cyan)' }}>{currentQuery.toUpperCase()}</span>
          {prediction && (
            <span style={{ marginLeft: '12px', color: 'var(--text-muted)' }}>
              — {prediction.total_execution_time_ms?.toFixed(0)}ms en total
            </span>
          )}
        </div>
      )}

      {/* Agent Timeline */}
      <AgentTimeline agents={agents} />

      {/* Results Grid */}
      {prediction && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '16px',
        }}>
          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Probability Bars */}
            <ProbabilityBars
              probabilities={prediction.probabilities}
              homeTeam={prediction.home_team}
              awayTeam={prediction.away_team}
            />

            {/* Expected Goals */}
            <div className="panel animate-fade-in-up">
              <div className="panel-header">
                <span style={{ color: 'var(--accent-green)' }}>◆</span>
                GOLES ESPERADOS (xG)
              </div>
              <div className="panel-body" style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto 1fr',
                gap: '12px',
                alignItems: 'center',
                textAlign: 'center',
              }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.5px' }}>
                    {prediction.home_team.toUpperCase()}
                  </div>
                  <div style={{
                    fontSize: '36px',
                    fontWeight: 700,
                    color: 'var(--accent-green)',
                    textShadow: '0 0 15px rgba(0, 255, 136, 0.3)',
                  }}>
                    {prediction.expected_goals.home}
                  </div>
                </div>
                <div style={{
                  fontSize: '20px',
                  color: 'var(--text-muted)',
                  fontWeight: 300,
                }}>
                  vs
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.5px' }}>
                    {prediction.away_team.toUpperCase()}
                  </div>
                  <div style={{
                    fontSize: '36px',
                    fontWeight: 700,
                    color: 'var(--accent-orange)',
                    textShadow: '0 0 15px rgba(255, 140, 0, 0.3)',
                  }}>
                    {prediction.expected_goals.away}
                  </div>
                </div>
              </div>
            </div>

            {/* Market Edge */}
            <MarketEdgePanel
              edges={prediction.market_edges}
              homeTeam={prediction.home_team}
              awayTeam={prediction.away_team}
            />

            {/* ELO & H2H Stats */}
            <div className="panel animate-fade-in-up">
              <div className="panel-header">
                <span style={{ color: 'var(--accent-cyan)' }}>◆</span>
                RATING ELO & CARA A CARA (H2H)
              </div>
              <div className="panel-body">
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '8px',
                  marginBottom: '12px',
                }}>
                  <div style={{ textAlign: 'center', padding: '8px', background: 'var(--bg-primary)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>ELO LOCAL</div>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-green)' }}>
                      {prediction.elo.home}
                    </div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '8px', background: 'var(--bg-primary)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>DIF</div>
                    <div style={{
                      fontSize: '20px',
                      fontWeight: 700,
                      color: prediction.elo.difference > 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                    }}>
                      {prediction.elo.difference > 0 ? '+' : ''}{prediction.elo.difference}
                    </div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '8px', background: 'var(--bg-primary)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>ELO VISITANTE</div>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-orange)' }}>
                      {prediction.elo.away}
                    </div>
                  </div>
                </div>
                {prediction.h2h.total_matches > 0 && (
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-around',
                    padding: '8px',
                    background: 'var(--bg-primary)',
                    borderRadius: '4px',
                    fontSize: '13px',
                  }}>
                    <span>H2H: {prediction.h2h.total_matches} partidos</span>
                    <span style={{ color: 'var(--accent-green)' }}>G{prediction.h2h.home_wins}</span>
                    <span style={{ color: 'var(--text-muted)' }}>E{prediction.h2h.draws}</span>
                    <span style={{ color: 'var(--accent-orange)' }}>P{prediction.h2h.away_wins}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Tactical & Historical Insights */}
            {prediction.insights && (
              <MatchInsightsPanel
                insights={prediction.insights}
                homeTeam={prediction.home_team}
                awayTeam={prediction.away_team}
              />
            )}
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Bet Recommendation */}
            {prediction.best_bet && (
              <BetRecommendation bet={prediction.best_bet} />
            )}

            {/* Monte Carlo */}
            <MonteCarloChart data={prediction.monte_carlo} />

            {/* Score Matrix */}
            <ScoreMatrix
              scores={prediction.score_matrix}
              homeTeam={prediction.home_team}
              awayTeam={prediction.away_team}
            />

            {/* Sentiment */}
            {prediction.sentiment.narrative && (
              <div className="panel animate-fade-in-up">
                <div className="panel-header">
                  <span style={{ color: 'var(--accent-purple)' }}>◆</span>
                  ANÁLISIS DE SENTIMIENTO
                </div>
                <div className="panel-body">
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '8px',
                    marginBottom: '8px',
                  }}>
                    <div style={{ padding: '6px 8px', background: 'var(--bg-primary)', borderRadius: '4px', textAlign: 'center' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>LOCAL</div>
                      <div style={{
                        fontWeight: 700,
                        color: prediction.sentiment.home > 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                      }}>
                        {prediction.sentiment.home > 0 ? '+' : ''}{prediction.sentiment.home}
                      </div>
                    </div>
                    <div style={{ padding: '6px 8px', background: 'var(--bg-primary)', borderRadius: '4px', textAlign: 'center' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>VISITANTE</div>
                      <div style={{
                        fontWeight: 700,
                        color: prediction.sentiment.away > 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                      }}>
                        {prediction.sentiment.away > 0 ? '+' : ''}{prediction.sentiment.away}
                      </div>
                    </div>
                  </div>
                  <p style={{
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    lineHeight: '1.7',
                    fontStyle: 'italic',
                  }}>
                    {prediction.sentiment.narrative}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      {!prediction && !isLoading && (
        <div style={{
          textAlign: 'center',
          padding: '48px 16px',
          color: 'var(--text-muted)',
          fontSize: '13px',
        }}>
          <div style={{
            fontSize: '40px',
            marginBottom: '16px',
            color: 'var(--accent-green)',
            textShadow: '0 0 30px rgba(0, 255, 136, 0.3)',
          }}>
            ◆
          </div>
          <div style={{ marginBottom: '8px', color: 'var(--text-secondary)' }}>
            SPORTS AI — Análisis Predictivo Multi-Agente
          </div>
          <div style={{ marginBottom: '24px' }}>
            Escribe un partido para analizar. Ejemplos:
          </div>
          <div style={{
            display: 'flex',
            gap: '12px',
            justifyContent: 'center',
            flexWrap: 'wrap',
          }}>
            {[
              'analiza barcelona vs madrid',
              'predice inter vs juventus',
              'mejor apuesta liverpool vs arsenal',
            ].map(example => (
              <button
                key={example}
                onClick={() => handleAnalyze(example)}
                style={{
                  padding: '8px 16px',
                  background: 'var(--bg-panel)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: '4px',
                  color: 'var(--accent-cyan)',
                  cursor: 'pointer',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '13px',
                  transition: 'all 0.2s',
                }}
                onMouseOver={e => {
                  (e.target as HTMLElement).style.borderColor = 'var(--accent-cyan)';
                  (e.target as HTMLElement).style.background = 'rgba(0, 212, 255, 0.05)';
                }}
                onMouseOut={e => {
                  (e.target as HTMLElement).style.borderColor = 'var(--border-primary)';
                  (e.target as HTMLElement).style.background = 'var(--bg-panel)';
                }}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Status bar */}
      <footer style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '8px 12px',
        borderTop: '1px solid var(--border-primary)',
        fontSize: '11px',
        color: 'var(--text-muted)',
        marginTop: 'auto',
      }}>
        <span>SPORTS AI TERMINAL v1.0.0</span>
        <span>13 AGENTES | POISSON + ML + MONTE CARLO</span>
        <span>
          <span style={{ color: 'var(--accent-green)' }}>●</span> CONECTADO
        </span>
      </footer>
    </main>
  );
}
