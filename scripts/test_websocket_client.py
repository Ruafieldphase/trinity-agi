#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_client():
    uri = "ws://localhost:8097/flow"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Wait for first message
            message = await websocket.recv()
            data = json.loads(message)
            
            print("\n📊 Received System State:")
            print(json.dumps(data, indent=2))
            
            # Check for required fields
            required = ["relationship", "time", "energy", "rhythm"]
            missing = [f for f in required if f not in data]
            
            if missing:
                print(f"\n❌ Missing fields: {missing}")
                sys.exit(1)
            else:
                print("\n✅ All Regulator Field components present.")
                
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_client())
