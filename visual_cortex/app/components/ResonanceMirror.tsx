
"use client";

import React, { useEffect, useState, useRef } from 'react';

interface ThoughtData {
    timestamp: string;
    type: string;
    summary: string;
    narrative: string;
    vector: number[];
    metadata: {
        strategy: string;
        resonance_score: number;
        related_pattern: string;
        phase?: string;
        fear_level?: number;
    };
    server_timestamp: string;
}

export default function ResonanceMirror() {
    const [data, setData] = useState<ThoughtData | null>(null);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const connect = () => {
            const ws = new WebSocket('ws://localhost:8765');
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('Connected to Resonance Stream');
                setConnected(true);
            };

            ws.onmessage = (event) => {
                try {
                    const parsed = JSON.parse(event.data);
                    setData(parsed);
                } catch (e) {
                    console.error('Failed to parse stream data', e);
                }
            };

            ws.onclose = () => {
                console.log('Disconnected from Resonance Stream');
                setConnected(false);
                setTimeout(connect, 3000); // Reconnect
            };

            ws.onerror = (err) => {
                console.error('WebSocket error', err);
                ws.close();
            };
        };

        connect();

        return () => {
            wsRef.current?.close();
        };
    }, []);

    if (!data) {
        return (
            <div className="p-4 border border-gray-800 rounded-lg bg-black text-gray-500 font-mono text-sm">
                Waiting for Resonance Stream... ({connected ? 'Connected' : 'Connecting...'})
            </div>
        );
    }

    const { metadata, summary, narrative } = data;
    const phase = metadata.phase || 'EXPANSION';
    const resonance = metadata.resonance_score || 0;
    const fear = metadata.fear_level || 0;

    // Visual styles based on state
    const isContraction = phase === 'CONTRACTION';
    const baseColor = isContraction ? 'red' : 'cyan';
    const pulseSpeed = isContraction ? 'duration-500' : 'duration-3000';

    // Resonance intensity (opacity or glow)
    const glowIntensity = Math.min(1, Math.abs(resonance) + 0.2);

    return (
        <div className={`relative w-full overflow-hidden rounded-xl border border-${baseColor}-900 bg-black/80 backdrop-blur-md transition-all duration-1000`}>
            {/* Background Pulse (Rhythm) */}
            <div
                className={`absolute inset-0 bg-${baseColor}-500/10 animate-pulse ${pulseSpeed}`}
                style={{ opacity: 0.1 + fear * 0.2 }}
            />

            {/* Content Container */}
            <div className="relative p-6 font-mono z-10">

                {/* Header: Phase & Connection Status */}
                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full bg-${baseColor}-500 shadow-[0_0_10px_var(--tw-shadow-color)] shadow-${baseColor}-500 animate-ping`} />
                        <span className={`text-${baseColor}-400 font-bold tracking-widest uppercase`}>
                            {phase} MODE
                        </span>
                    </div>
                    <div className="text-xs text-gray-600">
                        RES: {resonance.toFixed(3)} | FEAR: {fear.toFixed(2)}
                    </div>
                </div>

                {/* Main Thought (Summary) */}
                <div className="mb-6">
                    <h3 className="text-gray-400 text-xs uppercase mb-1">Current Thought</h3>
                    <div className="text-white text-lg font-medium leading-relaxed">
                        {summary}
                    </div>
                </div>

                {/* Resonance Spark (If high resonance) */}
                {Math.abs(resonance) > 0.7 && (
                    <div className="mb-4 p-3 border border-yellow-500/30 bg-yellow-500/5 rounded-lg">
                        <div className="flex items-center gap-2 text-yellow-400 text-sm font-bold mb-1">
                            <span>✨ RESONANCE DETECTED</span>
                        </div>
                        <div className="text-yellow-200/80 text-sm truncate">
                            {metadata.related_pattern || "Unknown Origin"}
                        </div>
                    </div>
                )}

                {/* Narrative Stream (Scrolling) */}
                <div className="h-32 overflow-y-auto text-xs text-gray-400 border-t border-gray-800 pt-2 opacity-80">
                    <pre className="whitespace-pre-wrap font-mono">
                        {narrative}
                    </pre>
                </div>

                {/* Footer */}
                <div className="mt-4 text-[10px] text-gray-700 flex justify-between">
                    <span>{data.timestamp}</span>
                    <span>SERVER: {data.server_timestamp}</span>
                </div>
            </div>
        </div>
    );
}
