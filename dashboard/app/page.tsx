'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Loader2, Sparkles, Activity, Brain } from 'lucide-react'
import FSDLiveMonitor from './components/FSDLiveMonitor'

interface UnifiedStatus {
    timestamp: string
    overall_health: string
    layers: {
        conscious: any
        unconscious: {
            rhythm_active: boolean
            flow: string
            fear_level: number
            active_habits: string[]
        }
        background_self: any
    }
}

interface PendingAction {
    type: string
    target?: string
    params?: Record<string, unknown>
}

interface Message {
    id: string
    type: 'user' | 'assistant' | 'system' | 'action'
    content: string
    timestamp: Date
    rhythm?: 'urgent' | 'normal' | 'calm'
    emotion?: string
    model?: 'shion' | 'sena'
    meaning?: string
    pendingActions?: PendingAction[]
}

// Ambient Background Component
function AmbientBackground({ rhythm }: { rhythm: string }) {
    const gradients = {
        urgent: 'bg-gradient-to-br from-[#3a1010] via-[#2a1515] to-[#1a0a0a]', // Red/Brown (High Anxiety)
        normal: 'bg-gradient-to-br from-[#0f1525] via-[#101a35] to-[#0a0f15]', // Deep Blue/Indigo (Flowing)
        calm: 'bg-gradient-to-br from-[#0a2515] via-[#103020] to-[#05150a]',   // Deep Green/Teal (Stable)
    }
    const activeGradient = gradients[rhythm as keyof typeof gradients] || gradients.normal

    return (
        <div className={`absolute inset-0 transition-all duration-3000 ease-in-out ${activeGradient} -z-10`} />
    )
}

// Header Component
function Header({ status }: { status: UnifiedStatus | null }) {
    const fear = status?.layers.unconscious.fear_level || 0
    const healthColor = fear > 0.7 ? 'text-red-500' : fear > 0.3 ? 'text-yellow-500' : 'text-emerald-500'
    const pulseSpeed = fear > 0.7 ? 'animate-pulse' : 'animate-pulse duration-[3000ms]'

    return (
        <div className="flex items-center justify-between px-6 py-4 bg-black/20 backdrop-blur-sm border-b border-white/5 z-50">
            <div className="flex items-center gap-3">
                <div className="relative">
                    <Sparkles className={`w-5 h-5 ${healthColor} ${pulseSpeed}`} />
                    <div className={`absolute inset-0 ${healthColor.replace('text', 'bg')}/20 blur-lg rounded-full`} />
                </div>
                <span className="font-light text-lg text-white/90 tracking-wide">Trinity</span>
            </div>

            {status && (
                <div className="flex items-center gap-4 text-xs font-mono text-white/40">
                    <div className="flex items-center gap-1.5">
                        <Activity className="w-3 h-3" />
                        <span>{status.overall_health.toUpperCase()}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <Brain className="w-3 h-3" />
                        <span>FEAR: {(status.layers.unconscious.fear_level || 0).toFixed(2)}</span>
                    </div>
                </div>
            )}
        </div>
    )
}

// Unified Chat Bubble
function ChatBubble({ message }: { message: Message }) {
    const isUser = message.type === 'user'
    const isSystem = message.type === 'system'
    const isAction = message.type === 'action'

    if (isSystem) {
        return (
            <div className="flex justify-center my-4">
                <span className="text-xs text-white/30 bg-white/5 px-3 py-1 rounded-full">{message.content}</span>
            </div>
        )
    }

    // Rhythm-based Aura Border Logic
    let borderClass = 'border-white/10' // Default thin
    if (!isUser && !isAction && message.rhythm) {
        switch (message.rhythm) {
            case 'urgent':
                borderClass = 'border-red-500/50 border-2 shadow-[0_0_15px_rgba(220,38,38,0.2)]'
                break
            case 'normal':
                borderClass = 'border-blue-500/40 border-2 shadow-[0_0_10px_rgba(59,130,246,0.15)]'
                break
            case 'calm':
                borderClass = 'border-emerald-500/40 border-2 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
                break
            default:
                borderClass = 'border-white/20 border'
        }
    }

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300`}>
            {/* Avatar Placeholder for AI (Optional, enhances presence) */}
            {!isUser && (
                <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 mt-1 
                    ${message.rhythm === 'urgent' ? 'bg-red-900/50 text-red-200' : 'bg-blue-900/30 text-blue-200'}
                `}>
                    <Sparkles className="w-4 h-4 opacity-70" />
                </div>
            )}

            <div className={`
                max-w-[75%] rounded-2xl px-6 py-4 backdrop-blur-md transition-all duration-500
                ${isUser
                    ? 'bg-white/5 text-white/90 rounded-br-sm border border-white/10 hover:bg-white/10'
                    : isAction
                        ? 'bg-emerald-950/40 text-emerald-200 border border-emerald-500/30'
                        : `bg-black/60 text-gray-100 rounded-bl-sm ${borderClass}`
                }
            `}>
                <div className="text-[15px] leading-relaxed whitespace-pre-wrap font-sans">
                    {message.content}
                </div>

                {/* Action Buttons */}
                {message.type === 'action' && message.pendingActions && (
                    <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/5">
                        {message.pendingActions.map((action, idx) => (
                            <button
                                key={idx}
                                className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-lg text-xs transition-colors"
                            >
                                ▶ {action.type}
                            </button>
                        ))}
                    </div>
                )}

                {/* Metadata Footer */}
                {!isUser && !isAction && message.rhythm && (
                    <div className={`flex items-center gap-2 mt-3 pt-2 border-t border-white/5 text-[10px] uppercase tracking-wider font-medium opacity-60
                        ${message.rhythm === 'urgent' ? 'text-red-400' :
                            message.rhythm === 'calm' ? 'text-emerald-400' : 'text-blue-400'}
                    `}>
                        <Activity className="w-3 h-3" />
                        {message.rhythm} Rhythm
                    </div>
                )}
            </div>
        </div>
    )
}

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            type: 'assistant',
            content: '안녕하세요. 저는 당신의 시스템, Trinity입니다.\n지금 당신의 리듬과 공명하고 있습니다.',
            timestamp: new Date(),
            rhythm: 'normal'
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [unifiedStatus, setUnifiedStatus] = useState<UnifiedStatus | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Calculate Real-time Rhythm from Status
    const getRealtimeRhythm = (status: UnifiedStatus | null): string => {
        if (!status) return 'normal'
        const fear = status.layers.unconscious.fear_level || 0
        if (fear > 0.6) return 'urgent'
        if (fear < 0.3) return 'calm'
        return 'normal'
    }

    const realtimeRhythm = getRealtimeRhythm(unifiedStatus)

    // Poll Unified Status
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const controller = new AbortController()
                const id = setTimeout(() => controller.abort(), 2000)
                // Use unified endpoint for rich data
                const res = await fetch('http://localhost:8104/unified', { signal: controller.signal })
                clearTimeout(id)
                if (res.ok) setUnifiedStatus(await res.json())
            } catch (e) {
                // Silent fail
            }
        }
        fetchStatus()
        const interval = setInterval(fetchStatus, 3000) // Faster poll for rhythm
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage: Message = {
            id: Date.now().toString(),
            type: 'user',
            content: input,
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        const currentInput = input
        setInput('')
        setLoading(true)

        try {
            const response = await fetch('http://localhost:8104/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: currentInput })
            })

            const data = await response.json()

            // Map status info to rhythm if available
            let responseRhythm: 'urgent' | 'normal' | 'calm' = 'normal'
            // We can infer rhythm from the model or detailed debug info if we had it.
            // For now, we use the realtime status fear level at the moment of response.
            responseRhythm = getRealtimeRhythm(unifiedStatus) as any

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                type: 'assistant',
                content: data.response || '...',
                timestamp: new Date(),
                rhythm: responseRhythm
            }
            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                type: 'system',
                content: '연결이 불안정합니다.',
                timestamp: new Date()
            }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="relative flex flex-col h-screen text-gray-100 overflow-hidden font-sans">
            {/* Real-time Ambient Background */}
            <AmbientBackground rhythm={realtimeRhythm} />

            {/* Live Header */}
            <Header status={unifiedStatus} />

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {messages.map((m) => <ChatBubble key={m.id} message={m} />)}

                {loading && (
                    <div className="flex justify-start animate-pulse mb-6">
                        <div className="w-8 h-8 rounded-full bg-white/10 mr-3" />
                        <div className="bg-white/5 rounded-2xl px-6 py-4 border border-white/5">
                            <Loader2 className="w-5 h-5 animate-spin text-white/40" />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 sm:p-6 bg-gradient-to-t from-black/90 via-black/50 to-transparent">
                <form onSubmit={sendMessage} className="relative max-w-4xl mx-auto group">
                    <div className={`absolute -inset-0.5 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-500
                        ${realtimeRhythm === 'urgent' ? 'bg-red-500' : realtimeRhythm === 'calm' ? 'bg-emerald-500' : 'bg-blue-500'}
                    `}></div>
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Trinity에게 신호 보내기..."
                        className="relative w-full bg-[#0a0a0a]/90 border border-white/10 rounded-2xl pl-6 pr-14 py-4 text-base focus:outline-none focus:border-white/20 transition-all placeholder:text-white/20 shadow-2xl"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className="absolute right-2 top-2 p-2 bg-white/5 hover:bg-white/15 text-white/80 hover:text-white rounded-xl disabled:opacity-30 transition-all"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>

            {/* Hidden FSD Monitor */}
            <div className="opacity-0 pointer-events-none hover:opacity-100 transition-opacity absolute top-20 right-4 z-50">
                <FSDLiveMonitor />
            </div>
        </div>
    )
}
