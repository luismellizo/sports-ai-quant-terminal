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
        <div ref={wrapperRef} className="flex-1 relative w-full">
            <div className="text-[11px] text-[var(--text-muted)] font-semibold mb-2 tracking-[1px] uppercase">
                {label}
            </div>
            <div className="relative flex items-center">
                {selectedTeam && selectedTeam.logo && (
                    <img src={selectedTeam.logo} alt="Logo" className="absolute left-3 w-6 h-6 object-contain z-10" />
                )}
                <input
                    type="text"
                    value={query}
                    onChange={handleChange}
                    onFocus={() => { if(query.length >= 3) setIsOpen(true) }}
                    disabled={disabled}
                    placeholder={`Buscar ${label.toLowerCase()}...`}
                    className={`w-full py-3 pr-4 bg-[rgba(10,10,15,0.5)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] font-mono text-[15px] outline-none transition-all duration-200 focus:border-[var(--accent-cyan)] focus:shadow-[0_0_10px_rgba(0,212,255,0.1)] focus:bg-[rgba(10,10,15,0.8)] ${selectedTeam ? 'pl-11' : 'pl-[14px]'}`}
                    autoComplete="off"
                    spellCheck="false"
                />
                {isLoading && (
                    <span 
                       className="absolute right-3 w-3.5 h-3.5 border-2 border-[var(--border-primary)] rounded-full animate-spin" 
                       style={{ borderTopColor: 'var(--accent-cyan)' }} 
                    />
                )}
            </div>
            
            {isOpen && results.length > 0 && (
                <ul className="absolute top-[calc(100%+4px)] left-0 w-full max-h-60 overflow-y-auto bg-[var(--bg-secondary)] border border-[var(--border-active)] rounded z-50 shadow-[0_8px_24px_rgba(0,0,0,0.6)]">
                    {results.map((team) => (
                        <li 
                            key={team.id} 
                            onClick={() => handleSelect(team)}
                            className="flex items-center gap-3 px-3.5 py-2.5 cursor-pointer border-b border-[var(--border-primary)] transition-colors hover:bg-[rgba(0,212,255,0.08)]"
                        >
                            {team.logo && <img src={team.logo} alt="" className="w-6 h-6 object-contain" />}
                            <div className="flex flex-col">
                                <span className="text-[var(--text-primary)] text-[13px] font-medium">{team.name}</span>
                                <span className="text-[var(--text-muted)] text-[11px]">{team.country}</span>
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
        <div className="panel animate-fade-in-up border border-[var(--border-primary)] bg-[var(--bg-panel)] rounded-md">
            <div className="panel-header">
                <span className={`status-dot ${isLoading ? 'active' : 'pending'}`} />
                SELECCIONA EL ENCUENTRO
                {isLoading && (
                    <span style={{ color: 'var(--accent-orange)', marginLeft: 'auto', fontSize: '11px' }}>
                        ▌ PROCESANDO RED...
                    </span>
                )}
            </div>
            <div className="p-6">
                <div className="flex flex-col md:flex-row items-center justify-center gap-5">
                    <TeamSearchInput 
                        label="Equipo Local" 
                        onSelect={setHomeTeam}
                        disabled={isLoading}
                    />
                    
                    <div className="flex items-center justify-center mt-1 md:mt-4">
                        <span className="text-2xl font-extrabold text-[var(--accent-green)] italic tracking-widest drop-shadow-[0_0_15px_rgba(0,255,136,0.5)]">
                            VS
                        </span>
                    </div>

                    <TeamSearchInput 
                        label="Equipo Visitante" 
                        onSelect={setAwayTeam}
                        disabled={isLoading}
                    />
                </div>

                <div className="mt-6 flex flex-col items-center gap-3 border-t border-dashed border-[var(--border-primary)] pt-5">
                    <button 
                        onClick={handleSubmit} 
                        disabled={!isReady || isLoading}
                        className={`bg-transparent text-[var(--text-muted)] border border-[var(--border-primary)] px-8 py-3 rounded text-sm font-bold tracking-wider transition-all duration-300 ${isReady ? 'text-[var(--bg-primary)] bg-[var(--accent-green)] border-[var(--accent-green)] shadow-[0_0_15px_rgba(0,255,136,0.3)] hover:-translate-y-px hover:shadow-[0_0_25px_rgba(0,255,136,0.6)] cursor-pointer' : 'opacity-60 cursor-not-allowed'}`}
                    >
                        {isLoading ? 'ANALIZANDO...' : 'INICIAR ANÁLISIS'}
                    </button>
                    {!isReady && !isLoading && (
                        <span className="text-xs text-[var(--text-muted)]">
                            Ingresa ambos equipos para habilitar el análisis
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
