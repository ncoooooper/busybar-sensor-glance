"""Listen to one Bluetooth Heart Rate Service broadcaster on the companion host."""
import asyncio,threading,time
from serve import page
HR="00002a37-0000-1000-8000-00805f9b34fb"
def decode(raw):
    if len(raw)<2:raise ValueError("Short HR packet")
    end=3 if raw[0]&1 else 2
    if len(raw)<end:raise ValueError("Short 16-bit HR packet")
    return int.from_bytes(raw[1:end],"little")
def reading(name,m):
    if "worker" not in m:
        from bleak import BleakClient,BleakScanner
        async def listen():
            while True:
                try:
                    device=await BleakScanner.find_device_by_name(name,timeout=8)
                    if device:
                        async with BleakClient(device) as client:
                            def update(_,payload):m["pulse"]=(time.monotonic(),decode(payload))
                            await client.start_notify(HR,update)
                            while client.is_connected:await asyncio.sleep(1)
                except Exception as error:
                    print("Bluetooth:",type(error).__name__,flush=True)
                await asyncio.sleep(3)
        worker=threading.Thread(target=lambda:asyncio.run(listen()),daemon=True);m["worker"]=worker;worker.start()
    at,bpm=m.get("pulse",(0,0));current=time.monotonic()-at<12
    return page("HEART RATE",f"{bpm} bpm" if current else "Waiting",name,"Bluetooth HR broadcast","Live" if current else "No fresh packets")
