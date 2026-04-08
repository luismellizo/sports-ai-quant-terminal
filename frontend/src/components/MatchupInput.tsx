'use client';

import { useState, useRef, useEffect } from 'react';
import { useTeamSearch, TeamResult } from '@/hooks/useTeamSearch';

interface MatchupInputProps {
    onSubmit: (query: string) => void;
    isLoading: boolean;
}

function TeamSearchInput({ 
    label, 
    onSelect, 
    disabled 
}: { 
    label: string; 
    onSelect: (team: string) => void;
    disabled: boolean;
}) {
    const { query, setQuery, results, isLoading } = useTeamSearch(300);
    const [isOpen, setIsOpen] = useState(false);
    const [selectedTeam, setSelectedTeam] = useState<TeamResult | null>(null);
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setQuery(e.target.value);
        setSelectedTeam(null);
        setIsOpen(true);
        onSelect(''); // Reset parent state if they edit
    };

    const handleSelect = (team: TeamResult) => {
        setSelectedTeam(team);
        setQuery(team.name);
        setIsOpen(false);
        onSelect(team.name);
    };

    return (
        <div ref={wrapperRef} className="flex-1 relative w-full flex flex-col items-center">
            <div style={{ fontFamily: 'var(--font-doto), monospace', fontSize: '18px', letterSpacing: '4px', color: 'var(--text-primary)', marginBottom: '20px', textTransform: 'uppercase', textAlign: 'center' }}>
                {label}
            </div>
            <div className="relative flex items-center justify-center w-full max-w-[500px]">
                {selectedTeam && selectedTeam.logo && (
                    <img src={selectedTeam.logo} alt="Logo" className="absolute left-4 w-8 h-8 object-contain z-10" />
                )}
                <input
                    type="text"
                    value={query}
                    onChange={handleChange}
                    onFocus={() => { if(query.length >= 3) setIsOpen(true) }}
                    disabled={disabled}
                    placeholder={`> BUSCAR...`}
                    className={`team-search-input ${selectedTeam ? 'has-selection' : ''}`}
                    style={{ fontSize: '24px', padding: '20px 40px', color: 'var(--text-primary)', textAlign: 'center', backgroundColor: 'transparent' }}
                    autoComplete="off"
                    spellCheck="false"
                />
                {isLoading && (
                    <span 
                       className="absolute right-4 w-5 h-5 border-2 border-[var(--border-primary)] rounded-full animate-spin" 
                       style={{ borderTopColor: 'var(--accent-green)' }} 
                    />
                )}
            </div>
            
            {isOpen && results.length > 0 && (
                <ul className="absolute top-[calc(100%+4px)] left-[50%] translate-x-[-50%] w-full max-w-[500px] max-h-[300px] overflow-y-auto bg-[var(--bg-panel)] border border-[var(--border-active)] rounded-none z-50 shadow-[0_8px_24px_rgba(0,0,0,0.8)]">
                    {results.map((team) => (
                        <li 
                            key={team.id} 
                            onClick={() => handleSelect(team)}
                            className="flex items-center gap-4 px-4 py-4 cursor-pointer border-b border-[var(--border-primary)] transition-colors hover:bg-[var(--text-primary)] hover:text-black group"
                        >
                            {team.logo && <img src={team.logo} alt="" className="w-10 h-10 object-contain" />}
                            <div className="flex flex-col text-left">
                                <span style={{ fontFamily: 'var(--font-space-mono), monospace', fontSize: '16px', fontWeight: 700 }} className="text-[var(--text-primary)] group-hover:text-black">{team.name}</span>
                                <span style={{ fontFamily: 'var(--font-space-grotesk), sans-serif', fontSize: '14px' }} className="text-[var(--text-muted)] group-hover:text-black opacity-80">{team.country}</span>
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default function MatchupInput({ onSubmit, isLoading }: MatchupInputProps) {
    const [homeTeam, setHomeTeam] = useState('');
    const [awayTeam, setAwayTeam] = useState('');

    const handleSubmit = () => {
        if (homeTeam && awayTeam && !isLoading) {
            onSubmit(`${homeTeam} vs ${awayTeam}`);
        }
    };

    const isReady = homeTeam.length > 0 && awayTeam.length > 0;

    return (
        <div className="animate-fade-in-up flex flex-col items-center justify-center" style={{ padding: '60px 0 100px 0', borderBottom: '1px dashed var(--border-primary)', width: '100%' }}>
            {isLoading && (
                <div style={{ textAlign: 'center', marginBottom: '40px', color: 'var(--accent-green)', fontFamily: 'var(--font-space-mono), monospace', fontSize: '16px', letterSpacing: '4px' }}>
                    <span className="status-dot active animate-blink mr-3" />
                    INICIANDO ANÁLISIS RED NEURONAL...
                </div>
            )}
            
            <div className="flex flex-col md:flex-row items-start justify-center gap-12 w-full max-w-[1400px] mx-auto px-4 mt-8">
                <div style={{ width: '100%', flex: 1, display: 'flex', justifyContent: 'center' }}>
                    <TeamSearchInput 
                        label="Equipo Local" 
                        onSelect={setHomeTeam}
                        disabled={isLoading}
                    />
                </div>
                
                <div className="matchup-vs flex items-center justify-center self-center" style={{ minWidth: '100px', padding: '0 20px', marginTop: '30px' }}>
                    <span style={{ fontSize: '32px' }}>VS</span>
                </div>

                <div style={{ width: '100%', flex: 1, display: 'flex', justifyContent: 'center' }}>
                    <TeamSearchInput 
                        label="Equipo Visitante" 
                        onSelect={setAwayTeam}
                        disabled={isLoading}
                    />
                </div>
            </div>

            <div className="flex flex-col items-center justify-center w-full" style={{ marginTop: '120px' }}>
                <button 
                    onClick={handleSubmit} 
                    disabled={!isReady || isLoading}
                    className={`matchup-submit-btn ${isReady && !isLoading ? 'ready' : ''}`}
                    style={{ 
                        padding: '28px 100px', 
                        fontSize: '32px', 
                        color: isReady ? 'var(--bg-primary)' : 'var(--text-primary)',
                        borderColor: isReady ? 'transparent' : 'var(--text-primary)',
                        maxWidth: '800px',
                        width: '100%'
                    }}
                >
                    {isLoading ? 'ANALIZANDO...' : '[ INICIAR ANÁLISIS ]'}
                </button>
                {!isReady && !isLoading && (
                    <span style={{ fontFamily: 'var(--font-space-mono), monospace', color: 'var(--text-muted)', fontSize: '16px', letterSpacing: '3px', textAlign: 'center', marginTop: '24px' }}>
                        INGRESA AMBOS EQUIPOS PARA HABILITAR EL ANÁLISIS
                    </span>
                )}
            </div>
        </div>
    );
}
