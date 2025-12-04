import sys
import os
import json
from pathlib import Path

# Add workspace root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.koa_router import KoaRouter
from scripts.internal_bus import bus

def test_internal_routing():
    print(f"DEBUG: sys.path: {sys.path}")
    import scripts.koa_router
    print(f"DEBUG: KoaRouter file: {scripts.koa_router.__file__}")

    print("🧪 Testing Internal Bus Routing...")
    
    router = KoaRouter()
    
    # Test Internal Routing
    print("\n1. Testing Ion -> Gitko (Internal Bus)")
    result = router.route(
        user_message="Gitko, check the logs", 
        source_system="ion"
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get("system") == "internal_bus":
        print("✅ Internal routing successful!")
        msg_id = result.get("message_id")
        
        # Verify message in bus
        print("\n2. Verifying Bus Content")
        messages = bus.poll("gitko")
        found = False
        for msg in messages:
            if msg['id'] == msg_id:
                print(f"✅ Found message in bus: {msg['id']}")
                print(f"   Content: {msg['content']}")
                bus.ack(msg['id'])
                found = True
                break
        
        if not found:
            print("❌ Message not found in bus!")
    else:
        print(f"❌ Internal routing failed. System: {result.get('system')}")

if __name__ == "__main__":
    test_internal_routing()
