'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
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

  // Secret admin access: triple-click on logo
  const router = useRouter();
  const clickCountRef = useRef(0);
  const clickTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleLogoClick = useCallback(() => {
    clickCountRef.current += 1;
    if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
    if (clickCountRef.current >= 3) {
      clickCountRef.current = 0;
      router.push('/admin');
      return;
    }
    clickTimerRef.current = setTimeout(() => {
      clickCountRef.current = 0;
    }, 600);
  }, [router]);

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
      let sseBuffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        sseBuffer += decoder.decode(value, { stream: true });
        const rawEvents = sseBuffer.split('\n\n');
        sseBuffer = rawEvents.pop() ?? '';

        for (const rawEvent of rawEvents) {
          const dataLines = rawEvent
            .split('\n')
            .filter(line => line.startsWith('data:'));
          if (dataLines.length === 0) continue;

          const eventJson = dataLines
            .map(line => line.replace(/^data:\s?/, ''))
            .join('\n')
            .trim();
          if (!eventJson) continue;

          try {
            const eventData: SSEEvent = JSON.parse(eventJson);
            const payload = eventData.data as Record<string, unknown>;

            switch (eventData.event) {
              case 'agent_start':
                setAgents(prev => {
                  const index = Number(payload.index ?? -1);
                  const exists = prev.find(a => a.index === index);
                  if (exists) return prev;
                  return [...prev, {
                    index,
                    name: String(payload.name ?? ''),
                    label: String(payload.label ?? ''),
                    status: 'running',
                  }];
                });
                break;

              case 'agent_complete':
                setAgents(prev =>
                  prev.map(a =>
                    a.index === Number(payload.index ?? -1)
                      ? {
                        ...a,
                        status: String(payload.status ?? 'error') as AgentEvent['status'],
                        execution_time_ms: Number(payload.execution_time_ms ?? 0),
                      }
                      : a
                  )
                );
                break;

              case 'pipeline_complete':
                setPrediction(payload as unknown as PredictionResult);
                break;
            }
          } catch {
            // Skip malformed events
          }
        }
      }

      // Parse any trailing buffered event (in case stream ends without final \n\n)
      const trailing = sseBuffer.trim();
      if (trailing.startsWith('data:')) {
        const trailingJson = trailing
          .split('\n')
          .filter(line => line.startsWith('data:'))
          .map(line => line.replace(/^data:\s?/, ''))
          .join('\n')
          .trim();

        if (trailingJson) {
          try {
            const eventData: SSEEvent = JSON.parse(trailingJson);
            if (eventData.event === 'pipeline_complete') {
              setPrediction(eventData.data as PredictionResult);
            }
          } catch {
            // Ignore malformed tail event
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
    <main className="page-main">
      {/* Header */}
      <header className="app-header">
        <div className="app-header-left">
          <span
            onClick={handleLogoClick}
            style={{
              color: 'var(--accent-green)',
              fontSize: '22px',
              fontWeight: 700,
              textShadow: '0 0 15px rgba(0, 255, 136, 0.4)',
              letterSpacing: '3px',
              userSelect: 'none',
            }}
          >
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
        <div className="app-header-right">
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
        <div className="query-banner">
          ANALIZANDO: <span style={{ color: 'var(--accent-cyan)' }}>{currentQuery.toUpperCase()}</span>
          {prediction && (
            <span style={{ marginLeft: '12px', color: 'var(--text-muted)' }}>
              — {prediction.total_execution_time_ms?.toFixed(0)}ms en total
            </span>
          )}
        </div>
      )}

      {/* Fixture resolution status */}
      {prediction?.fixture_resolution && (
        <div
          className="panel"
          style={{
            padding: '10px 12px',
            borderColor:
              prediction.fixture_resolution.status === 'resolved'
                ? 'rgba(0, 255, 136, 0.35)'
                : 'rgba(255, 140, 0, 0.4)',
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '1px' }}>
            RESOLUCIÓN DE FIXTURE
            <span
              style={{
                marginLeft: '10px',
                color:
                  prediction.fixture_resolution.status === 'resolved'
                    ? 'var(--accent-green)'
                    : 'var(--accent-orange)',
                fontWeight: 700,
              }}
            >
              {prediction.fixture_resolution.status.toUpperCase()} · {(prediction.fixture_resolution.confidence * 100).toFixed(0)}%
            </span>
          </div>

          {prediction.fixture_resolution.confirmation_message && (
            <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-primary)' }}>
              {prediction.fixture_resolution.confirmation_message}
            </div>
          )}

          {prediction.fixture_resolution.warnings?.length > 0 && (
            <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--accent-orange)' }}>
              {prediction.fixture_resolution.warnings.join(' | ')}
            </div>
          )}
        </div>
      )}

      {/* Agent Timeline */}
      <AgentTimeline agents={agents} />

      {/* Results Grid */}
      {prediction && (
        <div className="results-grid">
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
              <div className="panel-body xg-grid">
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
                <div className="xg-vs" style={{
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
            />

            {/* ELO & H2H Stats */}
            <div className="panel animate-fade-in-up">
              <div className="panel-header">
                <span style={{ color: 'var(--accent-cyan)' }}>◆</span>
                RATING ELO & CARA A CARA (H2H)
              </div>
              <div className="panel-body">
                <div className="elo-grid">
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
                  <div className="h2h-strip">
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
                  <div className="sentiment-grid">
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
          <div className="example-buttons">
            {[
              'analiza barcelona vs madrid',
              'predice inter vs juventus',
              'mejor apuesta liverpool vs arsenal',
            ].map(example => (
              <button
                key={example}
                onClick={() => handleAnalyze(example)}
                className="example-button"
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
      <footer className="status-footer">
        <span>SPORTS AI TERMINAL v1.0.0</span>
        <span>13 AGENTES | POISSON + ML + MONTE CARLO</span>
        <span>
          <span style={{ color: 'var(--accent-green)' }}>●</span> CONECTADO
        </span>
      </footer>
    </main>
  );
}
