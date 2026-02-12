import httpx
import time
import random
import datetime
import asyncio
import os

# --- CONFIGURATION ---
API_URL = os.getenv("API_URL", "http://localhost:8080/api/telemetry")
DEVICE_ID = os.getenv("DEVICE_ID", "default-device")
API_KEY = os.getenv("API_KEY", "my-local-test-key")
TOTAL_PACKETS = int(os.getenv("TOTAL_PACKETS", "50"))      # How many packets to generate
PACKET_DURATION = int(os.getenv("PACKET_DURATION", "120"))  # Seconds per packet

# Epoch offset (Jan 1, 2000)
EPOCH_START = datetime.datetime(2000, 1, 1).timestamp()

def get_custom_timestamp():
    """Returns seconds since Jan 1, 2000"""
    return int(time.time() - EPOCH_START)

def generate_packet(start_offset=0):
    """
    Generates a single valid JSON payload representing 
    one chunk (e.g., 60 seconds) of driving data.
    """
    
    # Calculate timestamps relative to the custom epoch
    base_time = get_custom_timestamp() - (start_offset * PACKET_DURATION)
    start_time = base_time
    end_time = base_time + PACKET_DURATION

    # Structures for the JSON body
    timed_data = {}
    aggregated_distance = 0.0
    
    # Simulation state
    current_speed = random.randint(0, 30) # Start with some speed
    current_rpm = 1000
    current_temp = 85

    # Generate data points for every second in this packet
    for i in range(PACKET_DURATION):
        tick_time = str(start_time + i)
        
        # 1. Simulate Physics (Simple Random Walk)
        if i < 10: # Accelerate
            current_speed += 2
            current_rpm = 2000 + (current_speed * 50)
        elif i > 50: # Decelerate
            current_speed = max(0, current_speed - 2)
            current_rpm = max(800, current_speed * 40)
        else: # Cruise
            current_speed += random.randint(-1, 1)
            current_rpm = 1500 + (random.randint(-50, 50))

        # Ensure values aren't negative
        current_speed = max(0, current_speed)
        
        # 2. Calculate Distance (Speed is km/h, convert to m/s -> meters per second)
        # distance = speed * time. (Time is 1 second)
        meters_traveled = (current_speed / 3.6)
        aggregated_distance += meters_traveled

        # 3. Add to timed_data
        # Randomly decide which sensors report data this second (to match your sparse example)
        entry = {}
        
        # Speed and RPM usually come together
        entry["speed"] = int(current_speed)
        entry["rpm"] = int(current_rpm)
        
        # Temp updates less often
        if i % 5 == 0:
            current_temp += random.uniform(-0.1, 0.1)
            entry["temp"] = round(current_temp, 1)

        timed_data[tick_time] = entry

    # Construct the final Payload
    payload = {
        "deviceId": DEVICE_ID,
        "start_time": start_time,
        "end_time": end_time,
        "aggregated_data": {
            "distance": round(aggregated_distance, 2)
        },
        "timed_data": timed_data
    }
    
    return payload

async def main():
    print(f"--- Starting Data Generation for {API_URL} ---")
    
    headers = {
        "X-API-KEY": API_KEY,             # Auth Header
        "X-Device-Source": DEVICE_ID,     # Custom header from your original code
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        for i in range(TOTAL_PACKETS):
            # Generate a packet (simulating data from 'i' minutes ago)
            data = generate_packet(start_offset=TOTAL_PACKETS - i)
            
            print(f"[{i+1}/{TOTAL_PACKETS}] Sending packet (Time: {data['start_time']})...")
            
            try:
                response = await client.post(API_URL, json=data, headers=headers)
                if response.status_code in [200, 201]:
                    print(" -> Success")
                else:
                    print(f" -> Failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f" -> Error: {e}")
            
            # Tiny sleep just to not hammer the DB instantly
            await asyncio.sleep(0.1)

    print("--- Done ---")

if __name__ == "__main__":
    asyncio.run(main())
