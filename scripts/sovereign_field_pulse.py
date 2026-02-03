import os
import time
import json
import hashlib
from datetime import datetime

class SovereignFieldPulse:
    """
    The Field Pulse Engine: 
    Monitors the 'Field' (outputs directory) and emits resonance signals 
    whenever the informational density changes.
    """
    def __init__(self, field_path):
        self.field_path = field_path
        self.last_state = {}
        self.resonance_score = 0
        
    def scan_field(self):
        current_state = {}
        for root, dirs, files in os.walk(self.field_path):
            for file in files:
                if file.endswith(('.json', '.md', '.html')):
                    full_path = os.path.join(root, file)
                    mtime = os.path.getmtime(full_path)
                    current_state[full_path] = mtime
        return current_state

    def calculate_interference(self, new_state):
        if not self.last_state:
            return 0
        
        changes = 0
        for path, mtime in new_state.items():
            if path not in self.last_state or self.last_state[path] != mtime:
                changes += 1
        return changes

    def pulse(self):
        print(f"🌊 Field Pulse Active: Monitoring {self.field_path}")
        print("Press Ctrl+C to stop.")
        
        try:
            while True:
                new_state = self.scan_field()
                interference = self.calculate_interference(new_state)
                
                if interference > 0:
                    self.resonance_score = min(100, self.resonance_score + (interference * 10))
                    print(f"✨ Resonance Detected! Interference +{interference} | Score: {self.resonance_score}")
                    
                    # Log the field ripple
                    pulse_log = {
                        "timestamp": datetime.now().isoformat(),
                        "resonance": self.resonance_score,
                        "active_waves": interference,
                        "status": "VIBRATING"
                    }
                    with open(os.path.join(self.field_path, 'field_pulse.json'), 'w') as f:
                        json.dump(pulse_log, f, indent=2)
                else:
                    self.resonance_score = max(0, self.resonance_score - 1)
                
                self.last_state = new_state
                time.sleep(2) # Field sampling rate
                
        except KeyboardInterrupt:
            print("\n🛑 Pulse Suspended. Returning to the Void.")

if __name__ == "__main__":
    FIELD_PATH = r"c:\workspace\agi\outputs"
    engine = SovereignFieldPulse(FIELD_PATH)
    engine.pulse()
