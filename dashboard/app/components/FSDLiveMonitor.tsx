'use client'

import { useState, useRef, useEffect } from 'react'
import { Maximize2, Minimize2, Monitor } from 'lucide-react'

// Backend URL
const STREAM_URL = "http://localhost:8104/fsd/stream"
const EVENTS_URL = "http://localhost:8104/fsd/events"

export default function FSDLiveMonitor() {
    const [position, setPosition] = useState({ x: 0, y: 0 })
    const [isClient, setIsClient] = useState(false)
    const [auraColor, setAuraColor] = useState('#00FFFF') // Default Cyan

    useEffect(() => {
        setIsClient(true)
        setPosition({ x: window.innerWidth - 340, y: 80 })

        // SSE Connection for Aura State
        const es = new EventSource(EVENTS_URL)
        es.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data)
                if (data.aura_color) {
                    setAuraColor(data.aura_color)
                }
            } catch (err) {
                console.error("SSE Parse Error", err)
            }
        }

        return () => {
            es.close()
        }
    }, [])

    const [minimized, setMinimized] = useState(false)
    const [isDragging, setIsDragging] = useState(false)
    const dragOffset = useRef({ x: 0, y: 0 })

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true)
        dragOffset.current = {
            x: e.clientX - position.x,
            y: e.clientY - position.y
        }
    }

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) {
                setPosition({
                    x: e.clientX - dragOffset.current.x,
                    y: e.clientY - dragOffset.current.y
                })
            }
        }
        const handleMouseUp = () => setIsDragging(false)

        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove)
            window.addEventListener('mouseup', handleMouseUp)
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove)
            window.removeEventListener('mouseup', handleMouseUp)
        }
    }, [isDragging])

    if (!isClient) return null

    return (
        <div
            className="fixed z-[100] bg-[#1a1b26]/90 rounded-lg overflow-hidden backdrop-blur-md transition-colors duration-500"
            style={{
                left: position.x,
                top: position.y,
                width: minimized ? 'auto' : '320px',
                transition: isDragging ? 'none' : 'width 0.3s, border-color 0.5s, box-shadow 0.5s',
                border: `2px solid ${auraColor}`,
                boxShadow: `0 0 20px ${auraColor}40` // Glow effect
            }}
        >
            {/* Header */}
            <div
                className="flex items-center justify-between px-3 py-2 bg-slate-800/80 cursor-move select-none border-b border-white/10"
                onMouseDown={handleMouseDown}
            >
                <div
                    className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider transition-colors duration-500"
                    style={{ color: auraColor }}
                >
                    <Monitor className="w-3 h-3" />
                    {!minimized && "AGI Vision"}
                </div>
                <button
                    onClick={() => setMinimized(!minimized)}
                    className="p-1 hover:bg-white/10 rounded text-slate-400 hover:text-white transition-colors"
                >
                    {minimized ? <Maximize2 className="w-3 h-3" /> : <Minimize2 className="w-3 h-3" />}
                </button>
            </div>

            {/* Video Feed */}
            {!minimized && (
                <div className="relative aspect-video bg-black flex items-center justify-center group overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                        src={STREAM_URL}
                        alt="FSD Live Stream"
                        className="w-full h-full object-contain"
                        onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.opacity = '0.3';
                        }}
                    />

                    {/* Status Overlay */}
                    <div
                        className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 px-2 py-0.5 rounded-full text-[10px] font-mono border transition-colors duration-500"
                        style={{ color: auraColor, borderColor: `${auraColor}80` }}
                    >
                        <div
                            className="w-1.5 h-1.5 rounded-full animate-pulse shadow-[0_0_8px]"
                            style={{ backgroundColor: auraColor, boxShadow: `0 0 8px ${auraColor}` }}
                        />
                        LIVE
                    </div>

                    {/* Scanline Effect */}
                    <div className="absolute inset-0 pointer-events-none opacity-10 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px]" />
                </div>
            )}
        </div>
    )
}
