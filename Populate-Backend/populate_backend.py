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
TRIPS_PER_DAY = int(os.getenv("TRIPS_PER_DAY", "0"))  # Avg trips per day
PACKET_DURATION = int(
    os.getenv("PACKET_DURATION", "60")
)  # Duration of each trip (seconds)
DEVICE_ID = os.getenv("DEVICE_ID", "default-device")
API_URL = os.getenv("API_URL", "http://localhost:8080/api/telemetry")
API_KEY = os.getenv("API_KEY", "my-local-test-key")

# Custom Epoch (Jan 1, 2000) - as used in your system
EPOCH_START_DT = datetime(2000, 1, 1)
EPOCH_START_TS = EPOCH_START_DT.timestamp()


def to_custom_timestamp(dt_object):
    """Converts a standard datetime object to your custom 2000-epoch timestamp."""
    return int(dt_object.timestamp() - EPOCH_START_TS)


def generate_packet(start_dt):
    """
    Generates a packet starting at a specific datetime object.
    """
    start_time_custom = to_custom_timestamp(start_dt)
    end_time_custom = start_time_custom + PACKET_DURATION

    timed_data = {}
    aggregated_distance = 0.0

    # Randomize start conditions slightly
    current_speed = random.randint(0, 40)
    current_rpm = 1000
    current_temp = 80.0 + random.uniform(-5, 5)

    for i in range(PACKET_DURATION):
        tick_time = str(start_time_custom + i)

        # 1. Physics Logic (Accelerate/Cruise/Decelerate)
        if i < 15:  # Accelerate
            current_speed += random.uniform(1, 3)
        elif i > (PACKET_DURATION - 15):  # Decelerate
            current_speed -= random.uniform(1, 3)
        else:  # Cruise
            current_speed += random.uniform(-2, 2)

        # Constraints
        current_speed = max(0, min(180, current_speed))
        current_rpm = 800 + (current_speed * 45) + random.randint(-50, 50)

        # 2. Distance aggregation (m/s)
        aggregated_distance += current_speed / 3.6

        # 3. Create Data Entry
        entry = {"speed": int(current_speed), "rpm": int(current_rpm)}

        # Temp updates every 10 ticks
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


async def main():
    # Parse dates
    start_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE_STR, "%Y-%m-%d")

    # Calculate total days
    delta = end_date - start_date
    total_days = delta.days + 1

    print(f"--- Generating Data ---")
    print(f"Range: {START_DATE_STR} to {END_DATE_STR} ({total_days} days)")
    print(f"Device: {DEVICE_ID} | Target: {API_URL}")

    headers = {
        "X-API-KEY": API_KEY,
        "X-Device-Source": DEVICE_ID,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        # Loop through every day in the range
        for day_offset in range(total_days):
            current_day = start_date + timedelta(days=day_offset)

            # Determine how many trips to fake for this specific day
            # (Randomize it slightly so it doesn't look robotic)
            num_trips = random.randint(TRIPS_PER_DAY - 2, TRIPS_PER_DAY + 2)
            if num_trips < 1:
                num_trips = 0

            print(f"📅 Processing {current_day.date()} ({num_trips} trips)...")

            for _ in range(num_trips):
                # Pick a random time of day (e.g., between 06:00 and 22:00)
                hour = random.randint(6, 22)
                minute = random.randint(0, 59)
                trip_start_time = current_day.replace(
                    hour=hour, minute=minute, second=0
                )

                # Generate Payload
                payload = generate_packet(trip_start_time)

                # Send
                try:
                    response = await client.post(API_URL, json=payload, headers=headers)
                    if response.status_code not in [200, 201]:
                        print(f"   ❌ Failed: {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️ Error: {e}")

                # Tiny pause
                await asyncio.sleep(0.01)

    print("--- Done ---")


if __name__ == "__main__":
    asyncio.run(main())
