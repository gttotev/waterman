#!/usr/bin/env python3
import time
from threading import Thread
import camera_server, logman
from gpiozero import DigitalInputDevice, DigitalOutputDevice

POLL_TIME_SEC = 10
PUMP_TIME_SEC = 3

cam_mq = camera_server.mq
cam_thread = Thread(target=camera_server.serve, daemon=True)
cam_thread.start()

in_pins = [18, 23, 24]
sensors = [DigitalInputDevice(p) for p in in_pins]
sensor_last_state = [s.value for s in sensors]
print(sensor_last_state)

out_pins = [17, 27, 22]
pumps = [DigitalOutputDevice(p, active_high=False) for p in out_pins]

def run_pump(i):
    m = pumps[i]
    if m.value:
        return
    logman.log('waterman: starting pump ' + str(i) + ' sensor is ' + str(sensors[i].value))
    m.on()
    time.sleep(PUMP_TIME_SEC)
    m.off()
    logman.log('waterman: stopped  pump ' + str(i) + ' sensor is ' + str(sensors[i].value))

poller_enabled = True
def poll():
    while True:
        time.sleep(POLL_TIME_SEC)
        #print([s.value for s in sensors])

        for i in range(len(in_pins)):
            if poller_enabled and sensors[i].value:
                Thread(target=run_pump, args=(i,), daemon=True).start()

poller = Thread(target=poll, daemon=True)
poller.start()

while True:
    if len(cam_mq) > 0:
        msg = cam_mq.pop().split('=')
        cmd = msg[0]
        if 'start_pump' in cmd:
            i = int(msg[1])
            Thread(target=run_pump, args=(i,), daemon=True).start()
        elif 'stop' in cmd:
            for m in pumps:
                m.off()
            logman.log('waterman: stopped all pumps')
        elif 'disable' in cmd:
            for m in pumps:
                m.off()
            poller_enabled = False
            logman.log('waterman: poller disabled')
        elif 'enable' in cmd:
            poller_enabled = True
            logman.log('waterman: poller enabled')
