#!/usr/bin/env python3
from gpiozero import DigitalInputDevice, DigitalOutputDevice
import time

SLEEP_TIME_SEC = 30

in_pins = [18, 23, 24]
sensors = [DigitalInputDevice(p) for p in in_pins]
last_state = [s.value for s in sensors]
print(last_state)

out_pins = [17, 27, 22]
pumps = [DigitalOutputDevice(p, active_high=False) for p in out_pins]
timeouts = [0, 0, 0]

def toggler(i):
    if sensors[i].value != last_state[i]:
        pumps[i].toggle()
        last_state[i] = sensors[i].value

def timeouter(i):
    if sensors[i].value and not timeouts[i]:
        timeouts[i] = 10000

    if timeouts[i]:
        pumps[i].on()
        timeouts[i] -= 1
    else:
        pumps[i].off()

while True:
    for i in range(len(in_pins)):
        pumps[i].value = sensors[i].value

    time.sleep(SLEEP_TIME_SEC)
