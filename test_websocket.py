#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/events/"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Successfully connected to {uri}")
            
            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"✅ Received initial data: {data['type']}")
                return True
            except asyncio.TimeoutError:
                print("⏱️ No initial message received (this might be normal)")
                return True
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def test_dashboard_websocket():
    uri = "ws://localhost:8000/ws/dashboard/"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Dashboard WebSocket connected to {uri}")
            return True
    except Exception as e:
        print(f"❌ Dashboard WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔌 Testing WebSocket connections...")
    
    loop = asyncio.get_event_loop()
    
    print("\n📡 Testing Events WebSocket:")
    events_result = loop.run_until_complete(test_websocket())
    
    print("\n📊 Testing Dashboard WebSocket:")
    dashboard_result = loop.run_until_complete(test_dashboard_websocket())
    
    if events_result and dashboard_result:
        print("\n🎉 All WebSocket connections working!")
    else:
        print("\n💥 Some WebSocket connections failed!") 