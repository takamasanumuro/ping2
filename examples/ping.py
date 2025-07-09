#!/usr/bin/env python

# ping_influxdb.py
from brping import Ping1D
import time
import argparse
import os

# Import InfluxDB client library
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from builtins import input

## Parse Command line options
############################

parser = argparse.ArgumentParser(description="Ping python library example with InfluxDB integration.")

# Echosounder arguments
parser.add_argument('--device', action="store", required=False, type=str, help="Ping device port. E.g: /dev/ttyUSB0")
parser.add_argument('--baudrate', action="store", type=int, default=115200, help="Ping device baudrate. E.g: 115200")
parser.add_argument('--udp', action="store", required=False, type=str, help="Ping UDP server. E.g: 192.168.2.2:9090")

# InfluxDB arguments
# parser.add_argument('--influx-url', action="store", required=True, type=str, help="InfluxDB server URL. E.g: http://localhost:8086")
# parser.add_argument('--influx-token', action="store", required=True, type=str, help="InfluxDB authentication token.")
# parser.add_argument('--influx-org', action="store", required=True, type=str, help="InfluxDB organization.")
# parser.add_argument('--influx-bucket', action="store", required=True, type=str, help="InfluxDB destination bucket.")


args = parser.parse_args()
if args.device is None and args.udp is None:
    parser.print_help()
    exit(1)

## Initialize InfluxDB Client
#############################
try:
    bucket = "Innoboat"
    token = os.environ.get('INFLUX_TOKEN')
    org = "Innomaker"
    url = "http://144.22.131.217:8086" 
    influx_client = InfluxDBClient(url=url, token=token, org=org)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    print("Successfully connected to InfluxDB.")
except Exception as e:
    print(f"Failed to connect to InfluxDB: {e}")
    exit(1)


## Initialize Ping Device
##########################
myPing = Ping1D()
if args.device is not None:
    myPing.connect_serial(args.device, args.baudrate)
elif args.udp is not None:
    (host, port) = args.udp.split(':')
    myPing.connect_udp(host, int(port))

if myPing.initialize() is False:
    print("Failed to initialize Ping!")
    exit(1)

print("------------------------------------")
print("Starting Ping..")
print("Press CTRL+C to exit")
print("------------------------------------")

input("Press Enter to continue...")

# Read and print distance measurements with confidence
while True:
    data = myPing.get_distance()
    if data:
        distance_mm = data["distance"]
        confidence_percent = data["confidence"]

        print(f"Distance: {distance_mm} mm\tConfidence: {confidence_percent}%")

        # Create a data point
        point = (
            Point("echosounder_reading")
            .tag("sensor_id", "Ping1D")
            .field("distance", distance_mm)
            .field("confidence", confidence_percent)
        )
        
        # Write the point to InfluxDB
        try:
            write_api.write(bucket=bucket, org=org, record=point)
            print(" -> Point successfully sent to InfluxDB.")
        except Exception as e:
            print(f" -> Failed to write to InfluxDB: {e}")
            
    else:
        print("Failed to get distance data")
        
    time.sleep(0.1)