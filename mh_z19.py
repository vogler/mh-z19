# -*- coding: utf-8 -*-
# original: https://raw.githubusercontent.com/UedaTakeyuki/slider/master/mh_z19.py
#
# © Takeyuki UEDA 2015 -

import serial
import time
import traceback
import struct
import platform
import argparse
import sys
import json

import paho.mqtt.client as mqtt
client = mqtt.Client()
client.connect("localhost")
client.loop_start()

# setting
version = "0.3.7"

serial_dev = '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.5:1.0-port0'

# major version of running python
p_ver = platform.python_version_tuple()[0]

def connect_serial():
  return serial.Serial(serial_dev,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1.0)

def mh_z19():
  try:
    ser = connect_serial()
    while 1:
      result=ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=ser.read(9)

      if p_ver == '2':
        if len(s) >= 4 and s[0] == "\xff" and s[1] == "\x86":
          return {'co2': ord(s[2])*256 + ord(s[3])}
        break
      else:
        if len(s) >= 4 and s[0] == 0xff and s[1] == 0x86:
          return {'co2': s[2]*256 + s[3]}
        break
  except:
     traceback.print_exc()

def read():
  result = mh_z19()
  if result is not None:
    return result

def read_all():
  try:
    ser = connect_serial()
    while 1:
      result=ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=ser.read(9)

      if p_ver == '2':
        if len(s) >= 9 and s[0] == "\xff" and s[1] == "\x86":
          return {'co2': ord(s[2])*256 + ord(s[3]),
                  'temperature': ord(s[4]) - 40,
                  'TT': ord(s[4]),
                  'SS': ord(s[5]),
                  'UhUl': ord(s[6])*256 + ord(s[7])
                  }
        break
      else:
        if len(s) >= 9 and s[0] == 0xff and s[1] == 0x86:
          return {'co2': s[2]*256 + s[3],
                  'temperature': s[4] - 40,
                  'TT': s[4],
                  'SS': s[5],
                  'UhUl': s[6]*256 + s[7]
                  }
        break
  except:
     traceback.print_exc()

  if result is not None:
    return result

def abc_on():
  ser = connect_serial()
  result=ser.write(b"\xff\x01\x79\xa0\x00\x00\x00\x00\xe6")
  ser.close()

def abc_off():
  ser = connect_serial()
  result=ser.write(b"\xff\x01\x79\x00\x00\x00\x00\x00\x86")
  ser.close()

def span_point_calibration(span):
  ser = connect_serial()
  if p_ver == '2':
    b3 = span / 256;
  else:
    b3 = span // 256;
  byte3 = struct.pack('B', b3)
  b4 = span % 256; byte4 = struct.pack('B', b4)
  c = checksum([0x01, 0x88, b3, b4])
  request = b"\xff\x01\x88" + byte3 + byte4 + b"\x00\x00\x00" + c
  result = ser.write(request)
  ser.close()

def zero_point_calibration():
  ser = connect_serial()
  request = b"\xff\x01\x87\x00\x00\x00\x00\x00\x78"
  result = ser.write(request)
  ser.close()

def detection_range_5000():
  ser = connect_serial()
  request = b"\xff\x01\x99\x00\x00\x00\x13\x88\xcb"
  result = ser.write(request)
  ser.close()

def detection_range_2000():
  ser = connect_serial()
  request = b"\xff\x01\x99\x00\x00\x00\x07\xd0\x8F"
  result = ser.write(request)
  ser.close()

def checksum(array):
  return struct.pack('B', 0xff - (sum(array) % 0x100) + 1)

if __name__ == '__main__':
#  value = read()
#  print (value)
  parser = argparse.ArgumentParser(
    description='''return CO2 concentration as object as {'co2': 416}''',
  )
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--version",
                      action='store_true',
                      help='''show version''')
  group.add_argument("--all",
                      action='store_true',
                      help='''return all (co2, temperature, TT, SS and UhUl) as json''')
  group.add_argument("--mqtt",
                      action='store_true',
                      help='''publish all data to mqtt every 10s''')
  group.add_argument("--abc_on",
                      action='store_true',
                      help='''Set ABC functionality on model B as ON.''')
  group.add_argument("--abc_off",
                      action='store_true',
                      help='''Set ABC functionality on model B as OFF.''')
  parser.add_argument("--span_point_calibration",
                      type=int,
                      help='''Call calibration function with SPAN point''')
  parser.add_argument("--zero_point_calibration",
                      action='store_true',
                      help='''Call calibration function with ZERO point''')
  parser.add_argument("--detection_range_5000",
                      action='store_true',
                      help='''Set detection range as 5000''')
  parser.add_argument("--detection_range_2000",
                      action='store_true',
                      help='''Set detection range as 2000''')

  args = parser.parse_args()

  if args.abc_on:
    abc_on()
    print ("Set ABC logic as on.")
  elif args.abc_off:
    abc_off()
    print ("Set ABC logic as off.")
  elif args.span_point_calibration is not None:
    span_point_calibration(args.span_point_calibration)
    print ("Call Calibration with SPAN point.")
  elif args.zero_point_calibration:
    print ("Call Calibration with ZERO point.")
    zero_point_calibration()
  elif args.detection_range_5000:
    detection_range_5000()
    print ("Set Detection range as 5000.")
  elif args.detection_range_2000:
    detection_range_2000()
    print ("Set Detection range as 2000.")
  elif args.version:
    print (version)
  elif args.all:
    value = read_all()
    print (json.dumps(value))
  elif args.mqtt:
    while True:
      data = json.dumps(read_all())
      print (data)
      client.publish("sensors/mh-z19b", data)
      time.sleep(10)
  else:
    value = read()
    print (json.dumps(value))

  sys.exit(0)
