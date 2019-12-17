#!/usr/bin/env python3
import time
from threading import Thread
import camera_server, logman
from gpiozero import DigitalInputDevice, DigitalOutputDevice

POLL_TIME_SEC = 10 * 60
PUMP_TIME_SEC = 4
PUMP_TIMEOUT_MS = 23 * 3600 * 1000

in_pins = [18, 23, 24]
sensors = [DigitalInputDevice(p) for p in in_pins]

out_pins = [17, 27, 22]
pumps = [DigitalOutputDevice(p, active_high=False) for p in out_pins]
pump_auto = [False for m in pumps]
pump_last = [0 for m in pumps]

def run_pump(i, interval=PUMP_TIME_SEC):
    m = pumps[i]
    if m.value:
        return
    logman.log('waterman: starting pump', i, 'sensor is', sensors[i].value)
    m.on()
    time.sleep(interval)
    m.off()
    logman.log('waterman: stopped  pump', i, 'sensor is', sensors[i].value)

def manual_handler(cls, path):
    res = (200, 'OK')
    msg = path[1:].split('=')
    cmd = msg[0]
    # code 250 for alert
    # no k-v
    if cmd == 'is_auto':
        return (250, str(pump_auto))
    if cmd == 'when_auto':
        return (250, str([time.ctime(t) for t in pump_last]))

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
            pump_auto[i] = False
            logman.log('waterman: auto', i, 'disabled')
        elif 'enable' in cmd:
            pump_auto[i] = True
            logman.log('waterman: auto', i, 'enabled')
        else:
            return (400, 'unknown command')

    return res

def auto_pumper(interval=POLL_TIME_SEC):
    while True:
        time.sleep(interval)
        for i in range(len(in_pins)):
            now = time.time()
            if pump_auto[i] and sensors[i].value and now - pump_last[i] > PUMP_TIMEOUT_MS:
                pump_last[i] = now
                Thread(target=run_pump, args=(i,), daemon=True).start()

if __name__ == '__main__':
    auto_thread = Thread(target=auto_pumper, daemon=True)
    auto_thread.start()

    cam_thread = Thread(target=camera_server.serve, args=(manual_handler,))
    cam_thread.start()
