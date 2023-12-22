import asyncio
import json
import aioblescan as aiobs
from aioblescan.plugins import ATCMiThermometer
import redis
import os
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Broker details
mqtt_broker = os.environ.get("MQTT_BROKER", "localhost")
mqtt_port = 1883
mqtt_topic = "bluetooth_temp"

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = 6379
redis_db = 0

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, charset='utf-8', decode_responses=True)

mqtt_client = mqtt.Client()
mqtt_client.connect(mqtt_broker, mqtt_port, 60)

def publish_discovery_data(sensor):
    device_name = sensor['name'] if sensor['name'] is not None else sensor['mac address']
    device_dict = {
            "identifiers":[
                device_name
            ],
            "name":device_name
    }
    temp_dict = {
        "device_class":"temperature",
        "state_class": "measurement",
        "state_topic": f"bluetooth_temp/{sensor['mac address']}/temperature",
        "name": "Temperature",
        "suggested_display_precision": 1,
        "unit_of_measurement": "°C",
        "unique_id":f"temp{sensor['mac address']}",
        "device" : device_dict
    }
    hum_dict = {
        "device_class":"humidity",
        "state_topic": f"bluetooth_temp/{sensor['mac address']}/humidity",
        "name": "Humidity",
        "suggested_display_precision": 1,
        "unit_of_measurement": "%",
        "unique_id":f"hum{sensor['mac address']}",
        "device" : device_dict
    }
    bat_dict = {
        "device_class":"battery",
        "state_topic": f"bluetooth_temp/{sensor['mac address']}/battery",
        "name": "Battery",
        "suggested_display_precision": 1,
        "unit_of_measurement": "%",
        "unique_id":f"bat{sensor['mac address']}",
        "device" : device_dict
    }
    mac_short = sensor['mac address'][-4:].replace(":", "")
    mqtt_client.publish(f"homeassistant/sensor/temp{mac_short}/config", json.dumps(temp_dict))
    mqtt_client.publish(f"homeassistant/sensor/hum{mac_short}/config", json.dumps(hum_dict))
    mqtt_client.publish(f"homeassistant/sensor/bat{mac_short}/config", json.dumps(bat_dict))

def my_process(data):
    ev = aiobs.HCI_Event()
    xx = ev.decode(data)
    xx = ATCMiThermometer().decode(ev)
    if xx:
        try:
            redis_client.sadd("bluetooth_sensors", xx['mac address'])
            xx['time'] = datetime.now().timestamp()
            print(f"Thermo {json.dumps(xx)}")
            redis_client.hset(xx['mac address'], mapping=xx)
        except:
            pass
        try:
            xx['name'] = redis_client.hget(xx['mac address'], "name")
        except:
            pass
        publish_discovery_data(xx)
        for key, value in xx.items():
            subtopic = f"{mqtt_topic}/{xx['mac address']}/{key}"
            mqtt_client.publish(subtopic, str(value))
            
 

async def amain(args=None):
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