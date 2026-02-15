import asyncio
import httpx
import random
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Date Range Configuration (YYYY-MM-DD)
START_DATE_STR = os.getenv("START_DATE", "2025-07-01")
END_DATE_STR = os.getenv("END_DATE", "2026-02-01")

# Simulation Settings
TRIPS_PER_DAY = int(os.getenv("TRIPS_PER_DAY", "2"))
PACKET_DURATION = int(os.getenv("PACKET_DURATION", "60"))

DEVICE_ID = os.getenv("DEVICE_ID", "default-device")
DEVICE_NAME = os.getenv("DEVICE_NAME", "Simulated Truck 01")

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8080/api/telemetry")
API_KEY = os.getenv("API_KEY", "my-local-test-key")

# Derive Base URL
BASE_URL = API_URL.replace("/api/telemetry", "")

# Custom Epoch (Jan 1, 2000)
EPOCH_START_DT = datetime(2000, 1, 1)
EPOCH_START_TS = EPOCH_START_DT.timestamp()

# Locations Pool
LOCATIONS = [
    "Berlin",
    "Hamburg",
    "Munich",
    "Cologne",
    "Frankfurt",
    "Paris",
    "Lyon",
    "Marseille",
    "London",
    "Manchester",
    "Birmingham",
    "Amsterdam",
    "Rotterdam",
    "Warsaw",
    "Krakow",
    "Prague",
    "Vienna",
]

# --- LOGGING ---
print("=" * 40)
print("🚀 INITIALIZING TELEMETRY SIMULATION")
print("=" * 40)
print(f"📅 Date Range:       {START_DATE_STR} to {END_DATE_STR}")
print(f"🆔 Device ID:        {DEVICE_ID}")
print(f"🏷️  Device Name:      {DEVICE_NAME}")
print(f"🌐 API URL:          {API_URL}")


def to_custom_timestamp(dt_object):
    return int(dt_object.timestamp() - EPOCH_START_TS)


def generate_packet(start_dt):
    start_time_custom = to_custom_timestamp(start_dt)
    end_time_custom = start_time_custom + PACKET_DURATION

    timed_data = {}
    aggregated_distance = 0.0
    current_speed = random.randint(0, 40)
    current_rpm = 1000
    current_temp = 80.0 + random.uniform(-5, 5)

    for i in range(PACKET_DURATION):
        tick_time = str(start_time_custom + i)

        if i < 15:
            current_speed += random.uniform(1, 3)
        elif i > (PACKET_DURATION - 15):
            current_speed -= random.uniform(1, 3)
        else:
            current_speed += random.uniform(-2, 2)

        current_speed = max(0, min(180, current_speed))
        current_rpm = 800 + (current_speed * 45) + random.randint(-50, 50)
        aggregated_distance += current_speed / 3.6

        entry = {"speed": int(current_speed), "rpm": int(current_rpm)}
        if i % 10 == 0:
            current_temp += random.uniform(-0.2, 0.3)
            entry["temp"] = round(current_temp, 1)

        timed_data[tick_time] = entry

    return {
        "deviceId": DEVICE_ID,
        "start_time": start_time_custom,
        "end_time": end_time_custom,
        "aggregated_data": {"distance": round(aggregated_distance, 2)},
        "timed_data": timed_data,
    }


async def update_device_name(client, headers):
    """Updates the friendly name of the device."""
    url = f"{BASE_URL}/api/devices/{DEVICE_ID}/name"
    try:
        # We send the string wrapped in JSON quotes (standard for 'type: string')
        resp = await client.put(url, json=DEVICE_NAME, headers=headers)

        if resp.status_code == 200:
            print(f"   ✅ Device Name set to: {DEVICE_NAME}")
            return True
        else:
            print(f"   ⚠️ Name Update Failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"   ⚠️ Error updating device name: {e}")
        return False


async def patch_trip_locations(client, trip_id, headers):
    """Patches the trip with start and end locations."""
    url = f"{BASE_URL}/api/trips/{trip_id}"

    start_loc = random.choice(LOCATIONS)
    end_loc = random.choice(LOCATIONS)
    while end_loc == start_loc:
        end_loc = random.choice(LOCATIONS)

    payload = {"startLocation": start_loc, "endLocation": end_loc}

    try:
        resp = await client.patch(url, json=payload, headers=headers)
        if resp.status_code == 200:
            # Optional: print less spam
            # print(f"   📍 Trip patched: {start_loc} -> {end_loc}")
            pass
        else:
            print(f"   ⚠️ Trip Patch Failed: {resp.status_code}")
    except Exception as e:
        print(f"   ⚠️ Error patching trip: {e}")


async def main():
    start_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE_STR, "%Y-%m-%d")
    delta = end_date - start_date
    total_days = delta.days + 1

    headers = {
        "X-API-KEY": API_KEY,
        "X-Device-Source": DEVICE_ID,
        "Content-Type": "application/json",
    }

    # Flag to track if we have named the device yet
    has_named_device = False

    async with httpx.AsyncClient() as client:
        print(f"--- Generating Telemetry Data ---")

        for day_offset in range(total_days):
            current_day = start_date + timedelta(days=day_offset)
            num_trips = random.randint(TRIPS_PER_DAY - 1, TRIPS_PER_DAY + 1)
            if num_trips < 0:
                num_trips = 0

            print(f"📅 Processing {current_day.date()} ({num_trips} trips)...")

            for _ in range(num_trips):
                hour = random.randint(6, 22)
                minute = random.randint(0, 59)
                trip_start_time = current_day.replace(
                    hour=hour, minute=minute, second=0
                )

                # 1. Generate Payload
                payload = generate_packet(trip_start_time)

                # 2. Send Telemetry (This creates the device if it doesn't exist)
                try:
                    response = await client.post(API_URL, json=payload, headers=headers)

                    if response.status_code in [200, 201]:
                        # 3. NOW that the device exists, name it (only once)
                        if not has_named_device:
                            success = await update_device_name(client, headers)
                            if success:
                                has_named_device = True

                        # 4. Extract Trip ID and Patch Location
                        data = response.json()
                        trip_id = data.get("tripId")

                        if trip_id:
                            await patch_trip_locations(client, trip_id, headers)
                        else:
                            print("   ⚠️ No tripId returned.")
                    else:
                        print(f"   ❌ Telemetry Failed: {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️ Error: {e}")

                await asyncio.sleep(0.01)

    print("--- Done ---")


if __name__ == "__main__":
    asyncio.run(main())
