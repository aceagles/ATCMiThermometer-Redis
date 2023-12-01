import asyncio
import struct
import time
from bleak import BleakScanner, BleakClient
device_name = "ATC_72AD1A"
temp_uid = "00002a1f-0000-1000-8000-00805f9b34fb"
humidity_uid = "00002a6f-0000-1000-8000-00805f9b34fb"

async def main():
    devices = await BleakScanner.discover()
    for d in devices:
        print(f"{d.name}")

        if d.name == "ATC_72AD1A":
            myDevice = d
    address = myDevice.address
    while True:
        async with BleakClient(address) as client:
            temperature = await client.read_gatt_char(temp_uid)
            print(temperature)
            temperature = struct.unpack('<H', temperature)[0]/10

            humidity = await client.read_gatt_char(humidity_uid)
            humidity = struct.unpack('<H', humidity)[0]/100
            print(f"Temperature - {temperature} degC, Humidity - {humidity}%")
            
        time.sleep(10)

asyncio.run(main())