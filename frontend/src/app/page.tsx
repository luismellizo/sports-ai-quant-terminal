'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'error' | 'success'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [hackLines, setHackLines] = useState<string[]>([]);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();

      if (data.success) {
        setStatus('success');
      } else {
        setStatus('error');
        setErrorMessage(data.message);
      }
    } catch {
      setStatus('error');
      setErrorMessage('Error de conexión con la matriz.');
    }
  };

  useEffect(() => {
    if (status === 'success') {
      const lines = [
        "INICIALIZANDO BYPASS LOCAL...",
        "AUTENTICACIÓN CONFIRMADA: ADMIN",
        "DESENCRIPTANDO NÚCLEO DE LA IA...",
        "CONECTANDO 15 AGENTES NEURONALES...",
        "CARGANDO SIMULACIONES MONTE CARLO...",
        "SINCRONIZANDO ANÁLISIS DE SENTIMIENTO...",
        "DERRIBANDO FIREWALLS DE LAS CASAS DE APUESTAS...",
        "ACCESO CONCEDIDO."
      ];

      let i = 0;
      const interval = setInterval(() => {
        if (i < lines.length) {
          setHackLines(prev => [...prev, lines[i]]);
          i++;
        } else {
          clearInterval(interval);
          setTimeout(() => {
            router.push('/terminal');
          }, 1000); // 1s extra despues del acceso concedido
        }
      }, 500);

      return () => clearInterval(interval);
    }
  }, [status, router]);

  if (status === 'success') {
    return (
      <main className="landing-layout hacking-mode">
        <div className="hack-screen">
          <div className="hack-header">◆ SPORTS AI QUANT TERMINAL // BOOT SEQUENCE</div>
          {hackLines.map((line, idx) => (
            <div key={idx} className="hack-line">
              <span className="hack-prefix">{'>'}</span> {line}
            </div>
          ))}
          <div className="cursor-blink">█</div>
        </div>
        <style jsx>{`
          .landing-layout {
            position: relative;
            min-height: 100vh;
            background-color: #000000;
            color: #E8E8E8;
            font-family: var(--font-space-grotesk), sans-serif;
            background-image: radial-gradient(circle, #333333 1px, transparent 1px);
            background-size: 24px 24px;
            display: flex;
            flex-direction: column;
            padding: 32px 48px;
            overflow: hidden;
          }
          .hacking-mode {
            justify-content: flex-end;
            padding-bottom: 96px;
          }
          .hack-screen {
            font-family: var(--font-space-mono), monospace;
            color: #39FF14;
            display: flex;
            flex-direction: column;
            gap: 12px;
            text-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
          }
          .hack-header {
            color: #FFFFFF;
            margin-bottom: 32px;
            font-size: 14px;
            letter-spacing: 0.08em;
          }
          .hack-line {
            font-size: 16px;
            letter-spacing: 0.05em;
          }
          .hack-prefix {
            color: #666666;
          }
          .cursor-blink {
            font-size: 16px;
            animation: blink 1s step-end infinite;
          }
          @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
          }
        `}</style>
      </main>
    );
  }

  return (
    <main className="landing-layout">
      <header className="header">
        <div className="logo-section">
          <div className="logo-symbol">◆</div>
          <div className="logo-text">SPORTS-AI</div>
        </div>
        <div className="header-meta">v3.0.0 / OFFLINE</div>
      </header>

      <div className="content-grid">
        <section className="hero-section">
          <h1 className="hero-title">PRECISIÓN<br />CUÁNTICA.</h1>
          <p className="hero-subtitle">
            El poder de 15 agentes de Inteligencia Artificial trabajando en paralelo.
            Modelos predictivos hiper-ajustados que devoran los mercados deportivos usando
            simulación de Monte Carlo, análisis de sentimiento en tiempo real y valoración de ventaja.
          </p>
          <div className="stats-row">
            <div className="stat-block">
              <div className="stat-value">15</div>
              <div className="stat-label">AGENTES NEURONALES</div>
            </div>
            <div className="stat-block">
              <div className="stat-value">X10</div>
              <div className="stat-label">VENTAJA DEL MERCADO</div>
            </div>
            <div className="stat-block">
              <div className="stat-value">10k+</div>
              <div className="stat-label">SIMULACIONES</div>
            </div>
          </div>
        </section>

        <section className="login-section">
          <div className="login-card">
            <h2 className="login-title">INICIAR CONEXIÓN</h2>
            <form onSubmit={handleLogin} className="login-form">
              <div className="input-group">
                <label>IDENTIFICADOR</label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="admin"
                  required
                  autoComplete="off"
                />
              </div>
              <div className="input-group">
                <label>CLAVE DE ACCESO</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              {status === 'error' && (
                <div className="error-msg">× {errorMessage}</div>
              )}

              <button type="submit" className="login-btn" disabled={status === 'loading'}>
                {status === 'loading' ? '[ CONECTANDO... ]' : '[ INGRESAR AL NÚCLEO ]'}
              </button>
            </form>
          </div>
        </section>
      </div>

      <style jsx>{`
        .landing-layout {
          position: relative;
          min-height: 100vh;
          background-color: #000000;
          color: #E8E8E8;
          font-family: var(--font-space-grotesk), sans-serif;
          background-image: radial-gradient(circle, #333333 1.5px, transparent 1.5px);
          background-size: 32px 32px;
          display: flex;
          flex-direction: column;
          padding: 32px 48px;
          overflow: hidden;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 96px;
        }

        .logo-section {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .logo-symbol {
          color: #39FF14;
          font-size: 32px;
          line-height: 1;
        }

        .logo-text {
          font-family: var(--font-space-mono), monospace;
          font-weight: 700;
          font-size: 18px;
          letter-spacing: 0.1em;
          color: #FFFFFF;
        }

        .header-meta {
          font-family: var(--font-space-mono), monospace;
          font-size: 12px;
          color: #666666;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .content-grid {
          display: grid;
          grid-template-columns: 1fr 400px;
          gap: 96px;
          align-items: center;
          flex: 1;
        }

        .hero-title {
          font-family: var(--font-doto), monospace;
          font-size: 120px;
          line-height: 0.95;
          letter-spacing: -0.03em;
          color: #FFFFFF;
          margin-bottom: 48px;
          text-transform: uppercase;
        }

        .hero-subtitle {
          font-size: 20px;
          line-height: 1.5;
          color: #999999;
          max-width: 600px;
          margin-bottom: 64px;
        }

        .stats-row {
          display: flex;
          gap: 64px;
        }

        .stat-block {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .stat-value {
          font-family: var(--font-doto), monospace;
          font-size: 72px;
          color: #39FF14;
          line-height: 1;
        }

        .stat-label {
          font-family: var(--font-space-mono), monospace;
          font-size: 14px;
          color: #666666;
          letter-spacing: 0.1em;
        }

        .login-section {
          display: flex;
          flex-direction: column;
          justify-content: center;
        }

        .login-card {
          background-color: #111111;
          border: 1px solid #333333;
          padding: 48px;
        }

        .login-title {
          font-family: var(--font-space-mono), monospace;
          font-size: 14px;
          color: #FFFFFF;
          letter-spacing: 0.08em;
          margin-bottom: 48px;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 32px;
        }

        .input-group {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .input-group label {
          font-family: var(--font-space-mono), monospace;
          font-size: 11px;
          color: #999999;
          letter-spacing: 0.1em;
          text-transform: uppercase;
        }

        .input-group input {
          background: transparent;
          border: 1px solid #333333;
          padding: 20px;
          color: #FFFFFF;
          font-family: var(--font-space-mono), monospace;
          font-size: 18px;
          outline: none;
          transition: border-color 0.2s;
        }

        .input-group input:focus {
          border-color: #39FF14;
        }

        .login-btn {
          background: #39FF14;
          color: #000000;
          border: none;
          padding: 20px;
          font-family: var(--font-space-mono), monospace;
          font-size: 14px;
          font-weight: 700;
          letter-spacing: 0.1em;
          cursor: pointer;
          transition: background-color 0.2s, color 0.2s;
          margin-top: 16px;
        }

        .login-btn:hover {
          background: #FFFFFF;
          color: #000000;
        }
        
        .login-btn:disabled {
          background: #333333;
          color: #666666;
          cursor: not-allowed;
        }

        .error-msg {
          font-family: var(--font-space-mono), monospace;
          font-size: 12px;
          color: #D71921;
          background: rgba(215, 25, 33, 0.1);
          padding: 12px;
          border: 1px solid rgba(215, 25, 33, 0.3);
        }

        @media (max-width: 1024px) {
          .content-grid {
            grid-template-columns: 1fr;
            gap: 64px;
          }
          
          .hero-title {
            font-size: 80px;
          }
        }
      `}</style>
    </main>
  );
}
