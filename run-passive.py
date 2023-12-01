import asyncio
import json
import aioblescan as aiobs
from aioblescan.plugins import ATCMiThermometer

# global
opts = None
decoders = []

def my_process(data):
    ev = aiobs.HCI_Event()
    xx = ev.decode(data)
    
    xx = ATCMiThermometer().decode(ev)
    if xx:       
        print(f"Thermo {json.dumps(xx)}")
       
 

async def amain(args=None):
    global opts

    event_loop = asyncio.get_running_loop()

    # First create and configure a raw socket
    mysocket = aiobs.create_bt_socket(0)

    conn, btctrl = await event_loop._create_connection_transport(
        mysocket, aiobs.BLEScanRequester, None, None
    )

    # Attach your processing
    btctrl.process = my_process
    
    # Probe
    await btctrl.send_scan_request()
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("keyboard interrupt")
    finally:
        print("closing event loop")
        # event_loop.run_until_complete(btctrl.stop_scan_request())
        await btctrl.stop_scan_request()
        command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
        await btctrl.send_command(command)
        conn.close()



if __name__ == "__main__":
    asyncio.run(amain())