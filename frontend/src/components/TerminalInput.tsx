'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';

interface TerminalInputProps {
    onSubmit: (query: string) => void;
    isLoading: boolean;
}

export default function TerminalInput({ onSubmit, isLoading }: TerminalInputProps) {
    const [value, setValue] = useState('');
    const [history, setHistory] = useState<string[]>([]);
    const [historyIdx, setHistoryIdx] = useState(-1);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        inputRef.current?.focus();
    }, [isLoading]);

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && value.trim() && !isLoading) {
            setHistory(prev => [value, ...prev]);
            onSubmit(value.trim());
            setValue('');
            setHistoryIdx(-1);
        }
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (history.length > 0) {
                const newIdx = Math.min(historyIdx + 1, history.length - 1);
                setHistoryIdx(newIdx);
                setValue(history[newIdx]);
            }
        }
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (historyIdx > 0) {
                const newIdx = historyIdx - 1;
                setHistoryIdx(newIdx);
                setValue(history[newIdx]);
            } else {
                setHistoryIdx(-1);
                setValue('');
            }
        }
    };

    return (
        <div className="panel">
            <div className="panel-header">
                <span className={`status-dot ${isLoading ? 'active' : 'pending'}`} />
                ENTRADA DE COMANDOS
                {isLoading && (
                    <span style={{ color: 'var(--accent-orange)', marginLeft: 'auto', fontSize: '11px' }}>
                        ▌ PROCESANDO RED...
                    </span>
                )}
            </div>
            <div className="panel-body terminal-input-body">
                <span style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: '16px' }}>{'>'}</span>
                <input
                    ref={inputRef}
                    value={value}
                    onChange={e => setValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    placeholder="analiza barcelona vs madrid"
                    spellCheck={false}
                    autoComplete="off"
                    className="terminal-input-field"
                />
                {!isLoading && value && (
                    <span className="terminal-enter-hint" style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                        ENTER ↵
                    </span>
                )}
            </div>
        </div>
    );
}
