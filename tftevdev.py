#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
import time

import evdev
import pygame
import Queue
import select
import sys
import threading
from pygame.locals import *
from tftutility import logger

# Class for handling events from piTFT
class TftTouchscreen(threading.Thread):
    def __init__(self, device_path="/dev/input/touchscreen", timeout=0.1):
        super(TftTouchscreen, self).__init__()
        self.device = evdev.InputDevice(device_path)
        if self.device is None:
            logger.error("Input device {0} not found".format(device_path))
            sys.exit(-1)
        else:
            logger.debug("Input device {0} found".format(device_path))

        self.timeout = timeout
        self.event = {'time': None, 'id': None, 'x': None, 'y': None, 'touch': None}
        self.events = Queue.Queue()
        self.shutdown_flag = threading.Event()
        self.rotation = 0
        self.device.grab()

    def run(self):
        while not self.shutdown_flag.is_set():
            readable, writeable, exceptional  = select.select([self.device.fd], [], [], self.timeout)
            if readable:
                for event in self.device.read():
                    if event.type == evdev.ecodes.EV_ABS:
                        if event.code == evdev.ecodes.ABS_X:
                            self.event['x'] = event.value
                        elif event.code == evdev.ecodes.ABS_Y:
                            self.event['y'] = event.value
                        elif event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                            self.event['id'] = event.value
                            if event.value == -1:
                                self.event['x'] = None
                                self.event['y'] = None
                                self.event['touch'] = None
                        elif event.code == evdev.ecodes.ABS_MT_POSITION_X:
                            pass
                        elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                            pass
                    elif event.type == evdev.ecodes.EV_KEY:
                        self.event['touch'] = event.value
                    elif event.type == evdev.ecodes.SYN_REPORT:
                        self.event['time'] = event.timestamp()
                        self.events.put(self.event)
                        e = self.event
                        self.event = {'x': e['x'], 'y': e['y']}
                        try:
                            self.event['id'] = e['id']
                        except KeyError:
                            self.event['id'] = None
                        try:
                            self.event['touch'] = e['touch']
                        except KeyError:
                            self.event['touch'] = None

    def get_event(self):
        if not self.events.empty():
            event = self.events.get()
            yield event
        else:
            yield None

    def queue_empty(self):
        return self.events.empty()

    def __del__(self):
        self.device.ungrab()
        self.shutdown_flag.set()


class TftEvHandler(object):
    pitft = TftTouchscreen()
    pitft.pigameevs = []

    def start(self, rotation = 90):

        self.pitft.rotation = rotation
        self.pitft.start()

    def run(self):
        pass

    def stop(self):
        self.pitft.shutdown_flag.set()


class TftCapacitiveEvHandler(TftEvHandler):

    def run(self):
        while not self.pitft.queue_empty():
            for r in self.pitft.get_event():
                e = {"y": (r["x"] if r["x"] else pygame.mouse.get_pos()[0]),
                     "x": (r["y"] if r["y"] else pygame.mouse.get_pos()[1])}
                if self.pitft.rotation == 90:
                    e = {"x": e["x"], "y": 240 - e["y"]}
                elif self.pitft.rotation == 270:
                    e = {"x": 320 - e["x"], "y": e["y"]}
                else:
                    raise (Exception("PiTft rotation is unsupported"))
                d = {}
                t = MOUSEBUTTONUP if r["touch"] == 0 else (
                    MOUSEMOTION if r["id"] in self.pitft.pigameevs else MOUSEBUTTONDOWN)
                if t == MOUSEBUTTONDOWN:
                    d["button"] = 1
                    d["pos"] = (e["x"], e["y"])
                    self.pitft.pigameevs.append(r["id"])
                    pygame.mouse.set_pos(e["x"], e["y"])
                elif t == MOUSEBUTTONUP:
                    l = []
                    for x in self.pitft.pigameevs:
                        if x != r["id"]:
                            l.append(x)
                            self.pitft.pigameevs = l
                    d["button"] = 1
                    d["pos"] = (e["x"], e["y"])
                else:
                    d["buttons"] = (True, False, False)
                    d["rel"] = (0, 0)
                    d["pos"] = (e["x"], e["y"])
                    pygame.mouse.set_pos(e["x"], e["y"])
                pe = pygame.event.Event(t, d)
                pygame.event.post(pe)