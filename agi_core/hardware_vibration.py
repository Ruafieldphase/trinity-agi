import psutil
import time
import logging
from typing import Dict

logger = logging.getLogger("HardwareVibration")

class HardwareVibration:
    """
    [Phase 24] Trans-OS Perception.
    Senses the 'raw' physical vibrations of the machine by observing 
    low-level hardware metric fluctuations.
    """
    def __init__(self):
        self.last_disk_time = time.time()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        
        # Windows specific: Thermal info is often restricted, 
        # so we use CPU frequency jitter as a proxy for 'heat' and 'stress'.
        self.last_cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0

    def get_raw_rhythms(self) -> Dict[str, float]:
        """
        Calculates raw rhythms based on metric deltas.
        Returns a dict of normalized (0.0 - 1.0) vibration scores.
        """
        now = time.time()
        dt = now - self.last_disk_time
        if dt <= 0: return {"thermal_wind": 0.0, "tactile_jitter": 0.0, "sub_os_wind": 0.0}

        # 1. Thermal Wind (CPU Frequency Jitter)
        # Proxy for thermal throttling and raw load stress.
        current_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
        freq_delta = abs(current_freq - self.last_cpu_freq)
        # Normalize: Assume 500MHz jitter is significant
        thermal_wind = min(1.0, freq_delta / 500.0)
        self.last_cpu_freq = current_freq

        # 2. Tactile Jitter (Disk I/O Activity)
        current_disk_io = psutil.disk_io_counters()
        read_delta = current_disk_io.read_bytes - self.last_disk_io.read_bytes
        write_delta = current_disk_io.write_bytes - self.last_disk_io.write_bytes
        # Normalize: Assume 10MB/s is high jitter
        tactile_jitter = min(1.0, (read_delta + write_delta) / (10 * 1024 * 1024 * dt))
        self.last_disk_io = current_disk_io

        # 3. Sub-OS Wind (Network Packet Frequency)
        current_net_io = psutil.net_io_counters()
        sent_delta = current_net_io.packets_sent - self.last_net_io.packets_sent
        recv_delta = current_net_io.packets_recv - self.last_net_io.packets_recv
        # Normalize: Assume 100 packets/sec is high wind
        sub_os_wind = min(1.0, (sent_delta + recv_delta) / (100.0 * dt))
        self.last_net_io = current_net_io

        self.last_disk_time = now

        rhythms = {
            "thermal_wind": thermal_wind,
            "tactile_jitter": tactile_jitter,
            "sub_os_wind": sub_os_wind
        }
        
        # Log only if significant
        if any(v > 0.3 for v in rhythms.values()):
            logger.debug(f"🌊 [Raw Rhythms] Wind: {sub_os_wind:.2f}, Jitter: {tactile_jitter:.2f}, Thermal: {thermal_wind:.2f}")
            
        return rhythms

if __name__ == "__main__":
    # Test Loop
    hv = HardwareVibration()
    for _ in range(5):
        time.sleep(1)
        print(hv.get_raw_rhythms())
