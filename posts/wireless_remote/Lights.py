#!/usr/bin/env python3
# ####################################################################################################
#
# Project:  Wireless remote light switch
# File:     Lights.py
# Authors:  Chris Lovett
#
# Requires: Python 3.5+
#
####################################################################################################
import argparse
from datetime import datetime
import time
import typing
import sys
import serial

from astral import Location

class LightController:
    def __init__(self, port):
        
        self.southLights = 4; # south lights
        self.northLights = 12; # north lights

        self.log = open("lights.log", "w")
        self.port = port
        self.serial = serial.Serial()
        self.serial.port = port
        self.baudrate = 115200
        self.serial.open()
        if self.serial.isOpen():
            self.serial.write("\r".encode())
            response = self.serial.readline().decode()
            response2 = self.serial.readline().decode()
            if response2.strip() == "Remote Light Controller:":
                self.writeln("connected")
            else:
                self.writeln("Unexpected response from controller: {}".format(response2))
                sys.exit(1)

    def write(self, msg):
        self.log.write(msg)
        self.log.flush()

    def writeln(self, msg):
        self.log.write(msg)
        self.log.write("\n")
        self.log.flush()

    def run(self):
        while True:
            secondsToNextEvent = self.checkLights()
            time.sleep(secondsToNextEvent)

    def turnOff(self):    
        self.serial.write("off:{}\r".format(self.southLights).encode())
        response = self.serial.readline().decode()
        response = self.serial.readline().decode()
        self.writeln("south:" + response.strip())
        self.serial.write("off:{}\r".format(self.northLights).encode())
        response = self.serial.readline().decode()
        response = self.serial.readline().decode()
        self.writeln("north:" + response.strip())

    def turnOn(self):
        self.serial.write("on:{}\r".format(self.southLights).encode())
        response = self.serial.readline().decode()
        response = self.serial.readline().decode()
        self.writeln("south:" + response.strip())
        self.serial.write("on:{}\r".format(self.northLights).encode())
        response = self.serial.readline().decode()
        response = self.serial.readline().decode()
        self.writeln("north:" + response.strip())

    def checkLights(self):
        # Get sunrise and sunset for Woodinville, WA
        l = Location()
        l.latitude =  47.763212
        l.longitude =  -122.068400
        l.timezone = 'US/Pacific'

        sunrise = l.sun()['dawn']
        sunrise = sunrise.replace(tzinfo=None)
        sunrise_hour = sunrise.strftime('%H')
        sunrise_minute = sunrise.strftime('%M')
        self.writeln('sunrise {}:{}'.format(sunrise_hour, sunrise_minute))

        sunset = l.sun()['sunset']
        sunset = sunset.replace(tzinfo=None)
        sunset_hour = sunset.strftime('%H')
        sunset_minute = sunset.strftime('%M')
        self.writeln('sunset {}:{}'.format(sunset_hour, sunset_minute))

        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute

        self.writeln('current time={}:{}'.format(current_hour, current_minute))

        sunrise_delta = sunrise - current_time
        sunrise_seconds = sunrise_delta.total_seconds()
        self.writeln('time till sunrise is {} seconds'.format(sunrise_seconds))

        sunset_delta = sunset - current_time
        sunset_seconds = sunset_delta.total_seconds()
        self.writeln('time till sunset is {} seconds'.format(sunset_seconds))

        if sunrise_seconds < 0 and sunset_seconds <= 0:
            self.writeln("Turning on the lights")
            self.turnOn()
            self.writeln("Turning off the lights in {} seconds".format(-sunrise_seconds))
            return -sunrise_seconds
        elif sunrise_seconds > 0 and sunset_seconds > 0:
            self.writeln("Turning on the lights")
            self.turnOn()
            self.writeln("Turning off the lights in {} seconds".format(sunrise_seconds))
            return sunrise_seconds
        elif sunrise_seconds <= 0 and sunset_seconds > 0:
            self.writeln("Turning off the lights")
            self.turnOff()
            self.writeln("Turning on the lights in {} seconds".format(sunset_seconds))
            return sunset_seconds
        
if __name__ == "__main__":    
    parser = argparse.ArgumentParser("Control the lights on given serial port so they turn on at sunset and off at sunrise")
    parser.add_argument("port", help="Name of COM port to talk to Arduino")
    args = parser.parse_args()    

    controller = LightController(args.port)
    controller.run()
