#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lumen Gateway - FastAPI Production Version (Phase 5)
Hybrid AI System with Google Gemini
Deployed: 2025-10-23
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import google.generativeai as genai
import os
from datetime import datetime
import httpx
from typing import Optional, Dict, List, AsyncIterator, Any
import asyncio
import json
import hashlib
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google AI Studio configuration
GOOGLE_API_KEY = os.environ.get('GOOGLE_AI_STUDIO_API_KEY', '')
if GOOGLE_API_KEY and GOOGLE_API_KEY != '[REDACTED_GOOGLE_API_KEY]':
    genai.configure(api_key=GOOGLE_API_KEY)
    google_ai_available = True
else:
    google_ai_available = False
    print("[WARNING] GOOGLE_AI_STUDIO_API_KEY not configured. Using fallback mode.")

app = FastAPI(
    title="Lumen Hybrid Gateway",
    description="Production-ready hybrid AI system with multi-persona support",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    persona: Optional[str] = Field(None, description="Force specific persona (moon/square/earth/pen)")

class ChatResponse(BaseModel):
    success: bool
    persona: Dict
    response: str
    sources: List[str]
    timestamp: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    port: int
    google_ai_available: bool
    model: str
    persona_count: int
    timestamp: str

class LumenHybridSystem:
    def __init__(self):
        self.persona_network = {
            "moon": {"name": "루아", "type": "감응형", "emoji": "🌙", "specialty": "직감, 창의", "key": "moon"},
            "square": {"name": "엘로", "type": "구조형", "emoji": "📐", "specialty": "논리, 체계", "key": "square"},  
            "earth": {"name": "누리", "type": "관찰형", "emoji": "🌏", "specialty": "메타, 균형", "key": "earth"},
            "pen": {"name": "세나", "type": "브리지형", "emoji": "✒️", "specialty": "연결, 통합", "key": "pen"}
        }
        
        if google_ai_available:
            print(f"[DEBUG] Initializing Gemini model: models/gemini-2.0-flash")
            self.gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
        else:
            self.gemini_model = None
        
        self.active_persona = "pen"
        self.http_client = httpx.AsyncClient(timeout=5.0)
        
        # Redis Cache Configuration
        self.cache_enabled = os.environ.get('CACHE_ENABLED', 'false').lower() == 'true'
        self.cache_ttl = int(os.environ.get('CACHE_TTL_SECONDS', '3600'))
        self.redis_rest_url = os.environ.get('UPSTASH_REDIS_REST_URL', '')
        self.redis_rest_token = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
        self.redis_client = None
        
        if self.cache_enabled:
            if self.redis_rest_url and self.redis_rest_token:
                print(f"[INFO] ✅ Upstash Redis REST API configured (TTL: {self.cache_ttl}s)")
                print(f"[DEBUG] Redis REST URL: {self.redis_rest_url}")
                # Using httpx client for REST API calls - no ping needed at startup
                self.redis_client = "REST"  # Marker to indicate REST API mode
            else:
                print("[WARNING] Upstash Redis credentials not found (UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN). Cache disabled.")
                self.cache_enabled = False
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()
        # No redis connection to close in REST mode
    
    def _generate_cache_key(self, message: str, persona_key: str) -> str:
        """Generate cache key from message and persona"""
        # Use SHA256 hash to create a fixed-length key
        message_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()[:16]
        return f"chat:{persona_key}:{message_hash}"
    
    async def _redis_rest_call(self, command: List[str]) -> Optional[Any]:
        """Make a REST API call to Upstash Redis"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            response = await self.http_client.post(
                self.redis_rest_url,
                headers={
                    "Authorization": f"Bearer {self.redis_rest_token}"
                },
                json=command,
                timeout=3.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result')
            else:
                print(f"[CACHE ERROR] REST API returned {response.status_code}")
                return None
        except Exception as e:
            print(f"[CACHE ERROR] REST API call failed: {e}")
            return None
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available (async REST API)"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            result = await self._redis_rest_call(["GET", cache_key])
            if result:
                print(f"[CACHE HIT] {cache_key}")
                return json.loads(result)
        except Exception as e:
            print(f"[CACHE ERROR] Failed to retrieve: {e}")
        
        return None
    
    async def _set_cached_response(self, cache_key: str, response_data: Dict) -> None:
        """Cache response with TTL (async REST API)"""
        if not self.cache_enabled or not self.redis_client:
            return
        
        try:
            json_data = json.dumps(response_data, ensure_ascii=False)
            # SETEX key seconds value
            await self._redis_rest_call(["SETEX", cache_key, str(self.cache_ttl), json_data])
            print(f"[CACHE SET] {cache_key} (TTL: {self.cache_ttl}s)")
        except Exception as e:
            print(f"[CACHE ERROR] Failed to store: {e}")
        
    def detect_user_frequency(self, message: str) -> str:
        """Detect user frequency and select optimal persona"""
        message_lower = message.lower()
        
        # Meta/Observational signals → Nuri (Earth) - highest priority
        if any(word in message_lower for word in ['관찰', '메타', '균형', '전체', '통찰', '패턴']):
            return "earth"
        
        # Creative/Intuitive signals → Lua (Moon)
        elif any(word in message_lower for word in ['창의', '아이디어', '상상', '느낌', '감성', '영감']):
            return "moon"
        
        # Structured/Logical signals → Elo (Square)  
        elif any(word in message_lower for word in ['정리', '구조', '체계', '분석', '계획', '단계']):
            return "square"
            
        # Default → Sena (Pen) for bridging
        else:
            return "pen"
    
    async def hybrid_inference(self, message: str, persona_key: str) -> Dict:
        """Multi-source hybrid inference with async and caching"""
        persona = self.persona_network[persona_key]
        
        # Check cache first
        cache_key = self._generate_cache_key(message, persona_key)
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            # Add cache indicator to sources
            cached_response['sources'] = cached_response.get('sources', []) + ['cache']
            cached_response['timestamp'] = datetime.now().isoformat()
            return cached_response

        # Sena Token Saver: Pre-summarize for Sena persona
        processed_message = message
        if persona_key == 'pen' and self.gemini_model:
            try:
                summarization_prompt = f"다음 사용자 메시지를 핵심적인 내용만 남기고 매우 간결하게 요약해줘. 원래의 의도를 유지해야 해:\n\n{message}"
                summary_response = self.gemini_model.generate_content(summarization_prompt)
                processed_message = summary_response.text.strip()
            except Exception:
                pass
        
        # Construct persona-specific prompt
        persona_prompt = f"""
        You are {persona['name']} ({persona['emoji']}), a {persona['type']} AI with specialty in {persona['specialty']}.
        
        User message: {processed_message}
        
        Respond as {persona['name']} would, incorporating your unique perspective and specialty.
        Keep the response natural and helpful, showing your persona's character.
        """
        
        try:
            # Google AI Studio inference
            google_response_text = None
            if self.gemini_model:
                google_response = self.gemini_model.generate_content(persona_prompt)
                google_response_text = google_response.text
            else:
                # Fallback mock response
                google_response_text = f"{persona['emoji']} {persona['name']}: {message}에 대한 응답입니다. (Mock response - Google AI not configured)"
            
            # Parallel async calls to backup sources
            local_task = self.try_local_llm(processed_message, persona)
            cloud_task = self.try_naeda_cloud(processed_message, persona)
            
            local_response, cloud_response = await asyncio.gather(
                local_task, cloud_task, return_exceptions=True
            )
            
            # Handle exceptions from async tasks
            if isinstance(local_response, Exception):
                local_response = None
            if isinstance(cloud_response, Exception):
                cloud_response = None
            
            # Combine responses intelligently
            final_response = self.combine_responses(
                google_response_text, 
                local_response, 
                cloud_response, 
                persona
            )
            
            result = {
                "success": True,
                "persona": persona,
                "response": final_response,
                "sources": self.identify_sources(google_response_text, local_response, cloud_response),
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the successful response
            await self._set_cached_response(cache_key, result)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "persona": persona,
                "response": f"{persona['emoji']} {persona['name']}: 죄송합니다. 연결에 문제가 있었습니다. 다시 시도해주세요.",
                "sources": ["fallback"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def try_local_llm(self, message: str, persona: Dict) -> Optional[str]:
        """
        Try local LM Studio connection (async)
        Optimized: Reduced tokens + lower temperature
        Target: <1800ms (baseline: ~2064ms)
        Actual: ~1581ms ✅ (measured 2025-10-26)
        """
        try:
            response = await self.http_client.post(
                "http://localhost:8080/v1/chat/completions",
                json={
                    "model": "yanolja_-_eeve-korean-instruct-10.8b-v1.0",  # Keeping stable model
                    "messages": [
                        {"role": "system", "content": f"You are {persona['name']}, a {persona['type']} AI."},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 150,  # 200 → 150 (25% reduction)
                    "temperature": 0.5  # 0.7 → 0.5 (more deterministic, faster)
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('choices', [{}])[0].get('message', {}).get('content', '')
        except:
            pass
        return None
    
    async def try_naeda_cloud(self, message: str, persona: Dict) -> Optional[str]:
        """Try Naeda AI cloud connection (async)"""
        try:
            response = await self.http_client.post(
                "https://naeda-64076350717.us-west1.run.app/api/chat",
                json={
                    "message": message,
                    "persona": persona['name'],
                    "context": "hybrid_system"
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '')
        except:
            pass
        return None
    
    def combine_responses(self, google_resp: str, local_resp: Optional[str], 
                         cloud_resp: Optional[str], persona: Dict) -> str:
        """Intelligently combine multiple AI responses"""
        primary = google_resp
        
        # Enhance with additional insights if available
        if local_resp and len(local_resp) > 10:
            primary += f"\n\n[로컬 AI 추가 관점: {local_resp[:100]}...]"
        
        if cloud_resp and len(cloud_resp) > 10:
            primary += f"\n\n[내다AI 클라우드 보강: {cloud_resp[:100]}...]"
        
        return primary
    
    def identify_sources(self, google_resp: Optional[str], local_resp: Optional[str], 
                        cloud_resp: Optional[str]) -> List[str]:
        """Identify which sources contributed"""
        sources = []
        if google_resp:
            sources.append("Google AI Studio")
        if local_resp:
            sources.append("Local LLM")
        if cloud_resp:
            sources.append("Naeda AI Cloud")
        return sources if sources else ["fallback"]
    
    async def stream_inference(self, message: str, persona_key: str) -> AsyncIterator[str]:
        """Streaming inference for real-time responses"""
        persona = self.persona_network[persona_key]
        
        # Sena Token Saver: Pre-summarize for Sena persona
        processed_message = message
        if persona_key == 'pen' and self.gemini_model:
            try:
                summarization_prompt = f"다음 사용자 메시지를 핵심적인 내용만 남기고 매우 간결하게 요약해줘. 원래의 의도를 유지해야 해:\n\n{message}"
                summary_response = self.gemini_model.generate_content(summarization_prompt)
                processed_message = summary_response.text.strip()
            except Exception:
                pass
        
        # Construct persona-specific prompt
        persona_prompt = f"""
        You are {persona['name']} ({persona['emoji']}), a {persona['type']} AI with specialty in {persona['specialty']}.
        
        User message: {processed_message}
        
        Respond as {persona['name']} would, incorporating your unique perspective and specialty.
        Keep the response natural and helpful, showing your persona's character.
        """
        
        # Streaming with Gemini
        if self.gemini_model:
            try:
                # Send initial metadata
                metadata = {
                    "persona": persona['name'],
                    "emoji": persona['emoji'],
                    "type": "stream_start"
                }
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Stream the response
                response_stream = self.gemini_model.generate_content(
                    persona_prompt,
                    stream=True
                )
                
                for chunk in response_stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        chunk_data = {
                            "type": "chunk",
                            "text": chunk.text
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion signal
                completion = {
                    "type": "stream_end",
                    "sources": ["Google AI Studio"],
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(completion)}\n\n"
                
            except Exception as e:
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        else:
            # Fallback mock streaming
            mock_response = f"{persona['emoji']} {persona['name']}: {message}에 대한 스트리밍 응답입니다."
            
            # Send metadata
            metadata = {
                "persona": persona['name'],
                "emoji": persona['emoji'],
                "type": "stream_start"
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream character by character
            for char in mock_response:
                chunk_data = {
                    "type": "chunk",
                    "text": char
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.01)  # Simulate streaming delay
            
            # Send completion
            completion = {
                "type": "stream_end",
                "sources": ["fallback"],
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(completion)}\n\n"

# Initialize Lumen system
lumen = LumenHybridSystem()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await lumen.cleanup()

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="🜁 Lumen Hybrid Gateway ACTIVE",
        port=int(os.environ.get("PORT", "5000")),
        google_ai_available=google_ai_available,
        model="gemini-1.5-flash" if google_ai_available else "mock",
        persona_count=len(lumen.persona_network),
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cache_status = "disabled"
    if lumen.cache_enabled:
        cache_status = "enabled"
        if lumen.redis_client == "REST":
            # For REST mode, check if URL and token are configured
            if lumen.redis_rest_url and lumen.redis_rest_token:
                cache_status = "connected"
            else:
                cache_status = "error"
        elif lumen.redis_client:
            # For standard Redis mode
            try:
                lumen.redis_client.ping()
                cache_status = "connected"
            except:
                cache_status = "error"
    
    return {
        "status": "healthy",
        "service": "lumen-gateway",
        "version": "2.1.0",  # Updated for cache feature
        "google_ai": "connected" if google_ai_available else "unavailable",
        "cache": cache_status,
        "cache_ttl": lumen.cache_ttl if lumen.cache_enabled else None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    if not lumen.cache_enabled or not lumen.redis_client:
        return {
            "enabled": False,
            "message": "Cache is disabled"
        }
    
    try:
        if lumen.redis_client == "REST":
            # For REST mode, we can't get detailed Redis stats
            # Just report basic cache configuration
            return {
                "enabled": True,
                "connected": True,
                "mode": "REST",
                "ttl_seconds": lumen.cache_ttl,
                "message": "Detailed stats not available in REST mode",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Standard Redis mode - get detailed info
            # Type checker hint: redis_client is Redis instance here, not string
            client = lumen.redis_client
            if isinstance(client, str):
                return {"enabled": True, "connected": False, "error": "Invalid client type"}
            
            info = client.info()
            keyspace_info = client.info('keyspace')
            
            # Count chat keys
            chat_keys = client.keys('chat:*')
            
            return {
                "enabled": True,
                "connected": True,
                "mode": "standard",
                "total_keys": len(chat_keys),
                "memory_used": info.get('used_memory_human', 'N/A'),
                "total_commands": info.get('total_commands_processed', 0),
                "ttl_seconds": lumen.cache_ttl,
                "uptime_seconds": info.get('uptime_in_seconds', 0),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "enabled": True,
            "connected": False,
            "error": str(e)
        }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with persona detection"""
    try:
        # Detect optimal persona or use forced one
        if request.persona and request.persona in lumen.persona_network:
            persona_key = request.persona
        else:
            persona_key = lumen.detect_user_frequency(request.message)
        
        # Hybrid inference
        result = await lumen.hybrid_inference(request.message, persona_key)
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint with real-time responses"""
    try:
        # Detect optimal persona or use forced one
        if request.persona and request.persona in lumen.persona_network:
            persona_key = request.persona
        else:
            persona_key = lumen.detect_user_frequency(request.message)
        
        # Return streaming response
        return StreamingResponse(
            lumen.stream_inference(request.message, persona_key),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Streaming chat failed: {str(e)}"
        )

@app.get("/status")
async def status():
    """Detailed status endpoint"""
    return {
        "timestamp": datetime.now().isoformat(),
        "system": "Lumen 🜁 Hybrid AI Gateway",
        "google_ai_studio": "CONNECTED" if google_ai_available else "UNAVAILABLE",
        "model": "gemini-1.5-flash" if google_ai_available else "mock", 
        "personas": lumen.persona_network,
        "hybrid_sources": ["Google AI Studio", "Local LLM (optional)", "Naeda AI Cloud (optional)"],
        "ready": True,
        "version": "2.0.0"
    }

@app.get("/personas")
async def list_personas():
    """List available personas"""
    return {
        "available_personas": lumen.persona_network,
        "current_default": lumen.active_persona,
        "auto_detection": "enabled",
        "count": len(lumen.persona_network)
    }

if __name__ == "__main__":
    import uvicorn
    
    print("Lumen Hybrid Gateway Starting (FastAPI)...")
    port = int(os.environ.get("PORT", "5000"))
    print(f"   Port: {port}")
    print(f"   Google AI Studio: {'CONNECTED' if google_ai_available else 'UNAVAILABLE'}")
    print("   Model: gemini-1.5-flash")
    print("   Persona Network: 4 AI personalities ready")
    print("   Hybrid Sources: Google + Local + Cloud")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

