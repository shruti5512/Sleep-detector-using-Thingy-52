import asyncio
from bleak import BleakClient
import struct
import csv
from datetime import datetime
import math
import os
import json

DEVICE_ADDRESS = "D1:69:CD:7E:B9:3B"  
ACCEL_UUID = "ef680406-9b35-4933-9b10-52ffa9740042"

SLEEP_THRESHOLD = 0.05
CSV_FILE = "multiuser_sleep_data.csv"


def get_active_user():
    try:
        with open("active_user.json", "r") as f:
            data = json.load(f)
            return data.get("user")
    except Exception as e:
        print("No active user found. Using default user.")
        return "default_user"


USER_ID = get_active_user()


def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "timestamp", "date", "sleep_state"])


def calculate_magnitude(x, y, z):
    return math.sqrt(x*x + y*y + z*z)


def detect_sleep(magnitude):
    return 1 if magnitude < SLEEP_THRESHOLD else 0


def parse_accel_data(data):
    try:
        x, y, z = struct.unpack("<hhh", data)
        scale = 1 / 16384.0
        return x * scale, y * scale, z * scale
    except Exception as e:
        print("Error parsing data:", e)
        return 0, 0, 0

def handle_notification(sender, data):
    x, y, z = parse_accel_data(data)

    magnitude = calculate_magnitude(x, y, z)
    sleep_state = detect_sleep(magnitude)

    timestamp = datetime.now()
    date = timestamp.date()

    print(f"[{USER_ID}] {timestamp} | Mag: {magnitude:.3f} | Sleep: {sleep_state}")

    try:
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([USER_ID, timestamp, date, sleep_state])
    except Exception as e:
        print("Error writing to CSV:", e)



async def main():
    initialize_csv()

    print("Starting BLE Data Collector...")
    print(f"Active User: {USER_ID}")
    print("Connecting to device...")

    try:
        async with BleakClient(DEVICE_ADDRESS) as client:
            if not client.is_connected:
                print("Failed to connect to device")
                return

            print("Connected! Collecting data...")

            await client.start_notify(ACCEL_UUID, handle_notification)

            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping data collection...")

            await client.stop_notify(ACCEL_UUID)

    except Exception as e:
        print("BLE Error:", e)

if __name__ == "__main__":
    asyncio.run(main())