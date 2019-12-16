#!/usr/bin/env python3
import time
from threading import Thread
import camera_server, logman
from gpiozero import DigitalInputDevice, DigitalOutputDevice

POLL_TIME_SEC = 10 * 60
PUMP_TIME_SEC = 4

in_pins = [18, 23, 24]
sensors = [DigitalInputDevice(p) for p in in_pins]

out_pins = [17, 27, 22]
pumps = [DigitalOutputDevice(p, active_high=False) for p in out_pins]
poller_enabled = [True for m in pumps]
# TODO: add timeouts

def run_pump(i):
    m = pumps[i]
    if m.value:
        return
    logman.log('waterman: starting pump', i, 'sensor is', sensors[i].value)
    #m.on()
    time.sleep(PUMP_TIME_SEC)
    m.off()
    logman.log('waterman: stopped  pump', i, 'sensor is', sensors[i].value)

def manual_handler(cls, path):
    res = (200, 'OK')
    msg = path[1:].split('=')
    cmd = msg[0]
    # code 250 for alert
    # no k-v

    if len(msg) < 2:
        return (400, 'key-value expected!')

    if cmd == 'read':
        return (250, str([s.value for s in (sensors if msg[1] == 's' else pumps)]))

    mps = [int(msg[1])] if msg[1].isdigit() else range(len(pumps))
    for i in mps:
        if 'start' in cmd:
            Thread(target=run_pump, args=(i,), daemon=True).start()
        elif 'stop' in cmd:
            pumps[i].off()
            logman.log('waterman: stopped pump', i)
        elif 'disable' in cmd:
            pumps[i].off()
            poller_enabled[i] = False
            logman.log('waterman: poller', i, 'disabled')
        elif 'enable' in cmd:
            poller_enabled[i] = True
            logman.log('waterman: poller', i, 'enabled')
        else:
            return (400, 'unknown command')

    return res

def poll_forever(interval=POLL_TIME_SEC):
    while True:
        time.sleep(interval)
        for i in range(len(in_pins)):
            if poller_enabled[i] and sensors[i].value:
                Thread(target=run_pump, args=(i,), daemon=True).start()

if __name__ == '__main__':
    poll_thread = Thread(target=poll_forever, daemon=True)
    poll_thread.start()

    cam_thread = Thread(target=camera_server.serve, args=(manual_handler,))
    cam_thread.start()
