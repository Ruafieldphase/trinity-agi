'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Loader2, Zap, Clock, Wind, Cpu, Brain } from 'lucide-react'
import FSDLiveMonitor from './components/FSDLiveMonitor'

interface FrontEngineResult {
    rhythm: 'urgent' | 'normal' | 'calm'
    emotional_resonance: string
    meaning: string
    action: {
        selected_model?: 'shion' | 'sena'
    }
    validated: boolean
    warnings: string[]
}

interface PendingAction {
    type: string
    target?: string
    params?: Record<string, unknown>
}

interface AntigravityStatus {
    status: string
    rpa_available: boolean
    safe_commands: string[]
    supported_actions: string[]
}

interface Message {
    id: string
    type: 'user' | 'assistant' | 'system' | 'action'
    content: string
    timestamp: Date
    // Front-Engine 메타데이터
    rhythm?: 'urgent' | 'normal' | 'calm'
    emotion?: string
    model?: 'shion' | 'sena'
    meaning?: string
    // Antigravity 메타데이터
    pendingActions?: PendingAction[]
}

interface EngineStatus {
    status: string
    state: 'folded' | 'unfolded'
    layers: Record<string, string>
    current_model: string
}

// 리듬 아이콘 컴포넌트
function RhythmBadge({ rhythm }: { rhythm?: string }) {
    if (!rhythm) return null

    const config = {
        urgent: { icon: Zap, color: 'text-trinity-urgent', label: '긴급' },
        normal: { icon: Clock, color: 'text-trinity-accent', label: '보통' },
        calm: { icon: Wind, color: 'text-trinity-calm', label: '차분' }
    }[rhythm] || { icon: Clock, color: 'text-gray-500', label: rhythm }

    const Icon = config.icon
    return (
        <span className={`inline-flex items-center gap-1 text-xs ${config.color}`}>
            <Icon className="w-3 h-3" />
            {config.label}
        </span>
    )
}


// 모델 뱃지 컴포넌트  
function ModelBadge({ model }: { model?: string }) {
    if (!model) return null

    const isShion = model === 'shion'
    return (
        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${isShion ? 'bg-purple-500/20 text-purple-300' : 'bg-blue-500/20 text-blue-300'}`}>
            {isShion ? <Cpu className="w-3 h-3" /> : <Brain className="w-3 h-3" />}
            {isShion ? 'Shion' : 'Sena'}
        </span>
    )
}

// 상태 바 컴포넌트
function StatusBar({ status }: { status: EngineStatus | null }) {
    if (!status) return null

    return (
        <div className="flex items-center gap-4 px-4 py-2 bg-trinity-panel/80 border-b border-trinity-accent/20 text-xs">
            <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${status.status === 'active' ? 'bg-trinity-success animate-pulse' : 'bg-gray-500'}`} />
                <span className="text-gray-400">Front-Engine</span>
                <span className="text-trinity-accent">{status.state}</span>
            </div>
            <div className="flex items-center gap-2 text-gray-500">
                {Object.entries(status.layers).map(([layer, state]) => (
                    <span key={layer} className={state === 'ready' ? 'text-trinity-success' : 'text-gray-600'}>
                        {layer}
                    </span>
                ))}
            </div>
            <div className="ml-auto">
                <ModelBadge model={status.current_model} />
            </div>
        </div>
    )
}

// FSD 상태 패널 컴포넌트
interface FSDStatus {
    active: boolean
    goal?: string
    step?: number
    maxSteps?: number
    message?: string
    success?: boolean
}

function FSDPanel({ status, visible }: { status: FSDStatus | null; visible: boolean }) {
    if (!visible || !status?.active) return null

    return (
        <div className="fixed top-16 right-4 w-72 bg-trinity-panel/95 backdrop-blur-md rounded-xl border border-trinity-accent/30 shadow-lg z-50 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-trinity-accent/20 to-transparent border-b border-trinity-accent/20">
                <span className="text-lg">🚗</span>
                <span className="font-medium text-white">FSD 자율 실행</span>
                <span className="ml-auto text-xs text-trinity-accent">Running</span>
            </div>

            <div className="p-4 space-y-3">
                {/* 목표 */}
                <div>
                    <div className="text-xs text-gray-400 mb-1">목표</div>
                    <div className="text-sm text-white truncate">{status.goal || '...'}</div>
                </div>

                {/* 진행 상황 */}
                {status.step !== undefined && (
                    <div>
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-400">진행</span>
                            <span className="text-trinity-accent">Step {status.step}/{status.maxSteps || 20}</span>
                        </div>
                        <div className="h-1.5 bg-trinity-bg rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-trinity-accent to-trinity-success transition-all duration-300"
                                style={{ width: `${((status.step || 0) / (status.maxSteps || 20)) * 100}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* 현재 상태 */}
                {status.message && (
                    <div className="text-xs text-gray-300 bg-trinity-bg/50 rounded-lg px-3 py-2">
                        {status.message}
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
            type: 'system',
            content: '✨ Trinity Dashboard v2 온라인. Front-Engine 연결됨.',
            timestamp: new Date()
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [engineStatus, setEngineStatus] = useState<EngineStatus | null>(null)
    const [fsdStatus, setFsdStatus] = useState<FSDStatus | null>(null)
    const [connectionError, setConnectionError] = useState(false)
    const fsdTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // 🌟 Timeout이 있는 fetch 래퍼
    const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeoutMs = 5000) => {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            })
            return response
        } finally {
            clearTimeout(timeoutId)
        }
    }

    // Front-Engine 상태 폴링 (15초 간격으로 변경)
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetchWithTimeout('http://localhost:8104/front-engine/status', {}, 3000)
                if (res.ok) {
                    setEngineStatus(await res.json())
                    setConnectionError(false)
                }
            } catch (e) {
                // 연결 실패 시 상태 표시
                setConnectionError(true)
            }
        }
        fetchStatus()
        const interval = setInterval(fetchStatus, 15000)  // 15초로 변경
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
            // Step 1: Front-Engine 분석 (10초 타임아웃)
            let frontEngineResult: FrontEngineResult | null = null

            try {
                const feRes = await fetchWithTimeout('http://localhost:8104/front-engine/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input: currentInput })
                }, 10000)
                if (feRes.ok) {
                    frontEngineResult = await feRes.json()
                }
            } catch (e) {
                console.warn('Front-Engine not available:', e)
            }

            // 프론트엔진 분석 결과가 실행 의미일 때 FSD 상태 표시
            const fsdLikely = frontEngineResult && ['NAVIGATE', 'CREATE', 'MODIFY', 'VERIFY'].includes(frontEngineResult.meaning)
            if (fsdLikely) {
                if (fsdTimeoutRef.current) clearTimeout(fsdTimeoutRef.current)
                setFsdStatus({
                    active: true,
                    goal: currentInput,
                    step: 0,
                    maxSteps: 20,
                    message: 'FSD 실행 트리거됨'
                })
                fsdTimeoutRef.current = setTimeout(() => {
                    setFsdStatus(prev => prev ? { ...prev, active: false, message: prev.message || 'FSD 상태 타임아웃' } : null)
                }, 30000)
            }

            // Step 3: Chat 요청 (10초 타임아웃)
            const response = await fetchWithTimeout('http://localhost:8104/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: currentInput })
            }, 10000)

            if (!response.ok) throw new Error('Network response was not ok')

            const data = await response.json()
            const assistantMessage: Message = {
                id: (Date.now() + 3).toString(),
                type: 'assistant',
                content: data.response || '응답을 받지 못했습니다.',
                timestamp: new Date(),
                rhythm: frontEngineResult?.rhythm,
                emotion: frontEngineResult?.emotional_resonance,
                model: frontEngineResult?.action?.selected_model,
                meaning: frontEngineResult?.meaning
            }

            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                type: 'system',
                content: `⚠️ 오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col h-screen bg-trinity-bg">
            {/* Status Bar */}
            <StatusBar status={engineStatus} />

            {/* 연결 오류 배너 */}
            {connectionError && (
                <div className="px-4 py-2 bg-trinity-warning/20 text-trinity-warning border-b border-trinity-warning/30 text-sm">
                    백엔드 연결이 불안정합니다. 다시 시도 중...
                </div>
            )}

            {/* FSD 상태 패널 */}
            <FSDPanel status={fsdStatus} visible={loading || !!fsdStatus?.active} />

            {/* Chat Container */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-2xl px-4 py-3 ${message.type === 'user'
                                    ? 'bg-trinity-accent text-white'
                                    : message.type === 'system'
                                        ? 'bg-trinity-warning/20 text-trinity-warning border border-trinity-warning/30'
                                        : message.type === 'action'
                                            ? 'bg-trinity-success/10 text-trinity-success border border-trinity-success/30'
                                            : `bg-trinity-panel text-gray-100 ${message.rhythm === 'urgent' ? 'border-l-2 border-trinity-urgent' :
                                                message.rhythm === 'calm' ? 'border-l-2 border-trinity-calm' : ''
                                            }`
                                    }`}
                            >
                                <div className="text-sm whitespace-pre-wrap">{message.content}</div>

                                {/* 실행 버튼 - action 타입일 때만 */}
                                {message.type === 'action' && message.pendingActions && (
                                    <div className="flex gap-2 mt-3">
                                        {message.pendingActions.map((action, idx) => (
                                            <button
                                                key={idx}
                                                onClick={async () => {
                                                    try {
                                                        const res = await fetch('http://localhost:8104/antigravity/execute', {
                                                            method: 'POST',
                                                            headers: { 'Content-Type': 'application/json' },
                                                            body: JSON.stringify({
                                                                action_type: action.type,
                                                                target: action.target,
                                                                params: action.params
                                                            })
                                                        })
                                                        const result = await res.json()
                                                        setMessages(prev => [...prev, {
                                                            id: Date.now().toString(),
                                                            type: 'system',
                                                            content: result.success
                                                                ? `✅ 실행됨: ${result.message}`
                                                                : `❌ 실패: ${result.message}`,
                                                            timestamp: new Date()
                                                        }])
                                                    } catch (e) {
                                                        console.error('Execute error:', e)
                                                    }
                                                }}
                                                className="px-3 py-1 bg-trinity-success/20 hover:bg-trinity-success/40 text-trinity-success rounded-lg text-xs font-medium transition-colors"
                                            >
                                                ▶ {action.type === 'open_app' ? action.target : action.type}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                <div className="flex items-center justify-between gap-2 mt-2">
                                    <div className="flex items-center gap-2">
                                        {(message.type === 'assistant' || message.type === 'action') && (
                                            <>
                                                <RhythmBadge rhythm={message.rhythm} />
                                                <ModelBadge model={message.model} />
                                            </>
                                        )}
                                    </div>
                                    <div className="text-xs opacity-50" suppressHydrationWarning>
                                        {message.timestamp.toLocaleTimeString('ko-KR')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-trinity-panel rounded-2xl px-4 py-3">
                                <Loader2 className="w-5 h-5 animate-spin text-trinity-accent" />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <form onSubmit={sendMessage} className="p-4 bg-trinity-panel/50 backdrop-blur-sm">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="메시지를 입력하세요..."
                            className="flex-1 bg-trinity-bg border border-trinity-accent/30 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-trinity-accent transition-colors"
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="bg-trinity-accent hover:bg-trinity-accent/80 disabled:bg-trinity-accent/30 text-white rounded-xl px-6 py-3 font-medium transition-all flex items-center gap-2"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                </form>
            </div>
            <FSDLiveMonitor />
        </div>
    )
}
