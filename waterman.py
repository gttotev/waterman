#!/usr/bin/env python3
from gpiozero import DigitalInputDevice, DigitalOutputDevice
from threading import Thread
import time

SLEEP_TIME_SEC = 10

in_pins = [18, 23, 24]
sensors = [DigitalInputDevice(p) for p in in_pins]
last_state = [s.value for s in sensors]
print(last_state)

def run_pump(pump):
    pump.on()
    time.sleep(SLEEP_TIME_SEC)
    pump.off()

out_pins = [17, 27, 22]
pumps = [DigitalOutputDevice(p, active_high=False) for p in out_pins]

while True:
    for i in range(len(in_pins)):
        if sensors[i].value and not pumps[i].value:
            Thread(target=run_pump, args=(pumps[i],)).start()
