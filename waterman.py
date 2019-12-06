#!/usr/bin/env python3
import time
from threading import Thread
import camera_server
from gpiozero import DigitalInputDevice, DigitalOutputDevice

POLL_TIME_SEC = 10
PUMP_TIME_SEC = 5

cam_mq = []
cam_thread = Thread(target=camera_server.serve, args=(cam_mq,), daemon=True)
cam_thread.start()

in_pins = [18, 23, 24]
sensors = [DigitalInputDevice(p) for p in in_pins]
sensor_last_state = [s.value for s in sensors]
print(sensor_last_state)

out_pins = [17, 27, 22]
pumps = [DigitalOutputDevice(p, active_high=False) for p in out_pins]

def run_pump(pump):
    pump.on()
    time.sleep(PUMP_TIME_SEC)
    pump.off()

while True:
    time.sleep(POLL_TIME_SEC)

    while len(cam_mq) > 0:
        msg = cam_mq.pop()

    for i in range(len(in_pins)):
        if sensors[i].value and not pumps[i].value:
            Thread(target=run_pump, args=(pumps[i],), daemon=True).start()
