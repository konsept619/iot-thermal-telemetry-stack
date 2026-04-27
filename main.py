import os
import serial
import time
from collections import deque
import statistics
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pythermalcomfort.models import pmv_ppd_iso


load_dotenv()

# --- InfluxDB ---
url = os.getenv("INFLUXDB_URL")
token = os.getenv("INFLUXDB_TOKEN")
org = os.getenv("INFLUXDB_ORG")
bucket = os.getenv("INFLUXDB_BUCKET")


temp_history = deque(maxlen=80)


ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def calc_comfort(temperature, med_temp, humidity, usr_model):
    result = pmv_ppd_iso(
        tdb=temperature,  # dry-bulb temperature in °C
        tr=med_temp,  # mean radiant temperature in °C
        vr=0.1,  # relative air speed in m/s
        rh=humidity,  # relative humidity in %
        met=1.4,  # metabolic rate in met
        clo=0.5,  # clothing insulation in clo
        model=usr_model,
    )
    return result

print("The connector is running, waiting from data from sensors...")

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        try:
            data = line.split(',')
            if len(data) == 4:
                temp, hum, light, fan = data

                #calculate current median for comfort calculations
                temp_history.append(float(temp))
                current_median = statistics.median(temp_history)
                comfort = calc_comfort(float(temp), float(current_median), float(hum), usr_model="7730-2005")

                point = Point("environment") \
                    .tag("device", "pico_h") \
                    .field("temperature", float(temp)) \
                    .field("humidity", float(hum)) \
                    .field("light_intensity", float(light)) \
                    .field("fan_power", float(fan)) \
                    .field("pmv", float(comfort['pmv'])) \
                    .field("ppd", float(comfort['ppd']))

                write_api.write(bucket=bucket, org=org, record=point)


                print(f"Thermal Comfort: \n{comfort}")
                print(f"Data sent -> T:{temp} H:{hum} L:{light} F:{fan}%, PMV: {comfort['pmv']}, PPD: {comfort['ppd']}")

        except ValueError:
            pass
