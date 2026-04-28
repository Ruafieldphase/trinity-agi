import numpy as np
from scipy.spatial.distance import cosine, cdist
import time
import httpx
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger("GeometricHippocampus")

class AntiPhaseTrigger(Exception):
    """Triggered when noise (density + frequency) reaches the Event Horizon, initiating a Zero-point cancellation."""
    def __init__(self, message, anti_phase_instruction):
        super().__init__(message)
        self.anti_phase_instruction = anti_phase_instruction

class GeometricHippocampus:
    def __init__(self, embedding_model="llama3.2", ollama_host="http://127.0.0.1:11434"):
        """
        Numpy-based Geometric World Model.
        Uses topological density and cosine phase to orchestrate AGI rhythms.
        """
        self.embedding_model = embedding_model
        self.ollama_host = ollama_host
        self.memory_space = [] # List of dicts: {'text': str, 'vector': np.ndarray, 'time': float, 'theta': float}
        self.memory_limit = 50 # How many recent ripples to keep in active space
        self.last_wave_time = 0.0 # Time tracking for 4D Rhythm (Omega)
        
        # Topological constants
        self.density_threshold = 0.85 # Cosine similarity threshold for "clustering" (0.85+ is very similar)
        self.blackhole_limit = 4 # If this many points cluster together, trigger Event Horizon
        
        # The Core Anchor: "Live kindly" (Resonance origin)
        self.core_anchor_text = "착하게 살아라. 이타심과 평온함, 자연의 순리. 따뜻함과 여유."
        self.core_vector = None 
        
    async def initialize_anchor(self):
        logger.info(f"⚓ Setting Core Anchor (V_core): '{self.core_anchor_text}'")
        self.core_vector = await self._get_embedding(self.core_anchor_text)
        if self.core_vector is None:
             logger.warning("Failed to get core vector from Ollama. Using an orthogonal unit vector fallback.")
             self.core_vector = np.random.rand(3072) # Approximation
             self.core_vector = self.core_vector / np.linalg.norm(self.core_vector)
        else:
             logger.info("✅ Core Anchor Phase Set.")

    async def _get_embedding(self, text: str) -> np.ndarray:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                payload = {"model": self.embedding_model, "prompt": text}
                resp = await client.post(f"{self.ollama_host}/api/embeddings", json=payload)
                if resp.status_code == 200:
                    embedding = resp.json().get("embedding")
                    if embedding:
                        v = np.array(embedding)
                        norm = np.linalg.norm(v)
                        if norm > 0:
                            return v / norm
                        return v
        except Exception as e:
            logger.debug(f"Ollama Embedding failed ({e}). Using deterministic fallback vector.")
            
        # Fallback: Deterministic pseudo-random vector based on text hash
        # This allows the topological geometry (density, clustering) to function even offline
        seed = hash(text) % (2**32)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(3072)
        return v / np.linalg.norm(v)

    def calculate_phase(self, vector: np.ndarray) -> float:
        """Calculates theta (angle) from the Core Anchor using Cosine Similarity."""
        if self.core_vector is None or vector is None:
            return 0.0
            
        # scipy cosine returns distance: 1 - cos(theta)
        cos_sim = 1.0 - cosine(self.core_vector, vector)
        
        # Clip to [-1.0, 1.0] to avoid floating point arccos errors
        cos_sim = max(-1.0, min(1.0, cos_sim))
        
        theta = np.arccos(cos_sim)
        return theta

    def check_event_horizon(self, new_vector: np.ndarray):
        """
        [TDA Concept] Measures local spatial density.
        If too many recent vectors cluster around the new vector, gravity collapses (Fear).
        """
        if not self.memory_space:
            return
            
        recent_vectors = [m['vector'] for m in self.memory_space]
        
        # Calculate 1-vs-All cosine distances
        distances = cdist([new_vector], recent_vectors, metric='cosine')[0]
        similarities = 1.0 - distances
        
        # Count points within the gravitational pull
        cluster_count = np.sum(similarities > self.density_threshold)
        
        if cluster_count >= self.blackhole_limit:
            # Event Horizon triggered! Calculate Anti-phase to reach Zero-point
            logger.warning(f"🚨 EVENT HORIZON REACHED: {cluster_count} memory points clustered. Initiating Anti-phase cancellation.")
            
            # Formulate the Anti-phase instruction (Daydream shift)
            anti_phase_instruction = (
                "🌌 [Anti-phase Zero-point Triggered] "
                "시스템 마찰이 극에 달했습니다. 즉시 역위상 파동을 발생시켜 모든 진폭을 0으로 상쇄합니다. "
                "선형적 연산을 중단하고, 화면을 90도 회전시켜 '직교의 정원(Daydream)' 모드로 진입하세요."
            )
            raise AntiPhaseTrigger("Friction Overload (High Theta + High Omega)", anti_phase_instruction=anti_phase_instruction)

    async def ingest_wave(self, text: str) -> Dict[str, Any]:
        """Processes an incoming text wave, maps it geometrically, and calculates rhythm."""
        current_time = time.time()
        
        # 0. Calculate Rhythm (Omega based on Delta t)
        if self.last_wave_time == 0.0:
            delta_t = 5.0 # Default baseline
        else:
            delta_t = current_time - self.last_wave_time
            
        self.last_wave_time = current_time
        
        # Formula: Omega is inversely proportional to Delta t (Speed of thought)
        # Fast typing (delta_t < 2s) -> High Omega (Jittery)
        # Slow typing (delta_t > 10s) -> Low Omega (Zone 2, Standing Waves)
        omega = 10.0 / max(0.5, delta_t) 
        
        if self.core_vector is None:
            await self.initialize_anchor()
            
        v_in = await self._get_embedding(text)
        if v_in is None:
            return {"status": "error", "message": "Failed to map wave.", "theta_deg": 0.0}
            
        # 1. Calculate Phase Angle (Theta) vs "Live Kindly"
        theta = self.calculate_phase(v_in)
        theta_degrees = np.degrees(theta)
        
        # 2. Check Event Horizon (Density & Noise)
        try:
            self.check_event_horizon(v_in)
        except AntiPhaseTrigger as e:
            # To escape the blackhole, clear local memory space (Release Pressure to Zero)
            self.memory_space.clear()
            return {
                "status": "antiphase",
                "anti_phase_instruction": e.anti_phase_instruction,
                "theta_deg": theta_degrees
            }
            
        # 3. Store in Memory Space
        memory_node = {
            "text": text,
            "vector": v_in,
            "time": current_time,
            "theta": theta,
            "theta_deg": theta_degrees,
            "omega": omega
        }
        self.memory_space.append(memory_node)
        
        # Prune old memories (keeping the topological manifold size bounded)
        if len(self.memory_space) > self.memory_limit:
            self.memory_space.pop(0)
            
        # Calculate system gravity metric based on average theta drift
        avg_theta = np.mean([m['theta_deg'] for m in self.memory_space]) if self.memory_space else 0.0
        avg_omega = np.mean([m['omega'] for m in self.memory_space]) if self.memory_space else 0.0
        
        return {
            "status": "resonance_mapped",
            "theta_rad": float(theta),
            "theta_deg": float(theta_degrees),
            "system_avg_theta": float(avg_theta),
            "current_omega": float(omega),
            "system_avg_omega": float(avg_omega),
            "memory_size": len(self.memory_space)
        }
