#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
import evdev
import pygame
import Queue
import threading
from pygame.locals import *
from tftutility import logger, Screen


# Class for handling events from piTFT
class TftTouchscreen(threading.Thread):
    def __init__(self, device_path="/dev/input/touchscreen"):
        super(TftTouchscreen, self).__init__()
        self.device_path = device_path
        self.events = Queue.Queue()
        self.shutdown = threading.Event()
        self.rotation = 0

    def run(self):

        thread_process = threading.Thread(target=self.process_device)
        thread_process.daemon = True
        thread_process.start()
        self.shutdown.wait()

    def get_event(self):
        if not self.events.empty():
            event = self.events.get()
            yield event
        else:
            yield None

    def queue_empty(self):
        return self.events.empty()

    def process_device(self):

        device = None

        try:
            device = evdev.InputDevice(self.device_path)
        except Exception, ex:
            message = "Unable to load device {0} due to a {1} exception with message: {2}.".format(
                self.device_path, type(ex).__name__, str(ex))
            logger.error(message)
            raise OSError(message)
        finally:
            if device is None:
                self.shutdown.set()

        logger.debug("Loaded device {} successfully.".format(self.device_path))
        event = {'time': None, 'id': None, 'x': None, 'y': None, 'touch': None}
        while True:
            for inputEvent in device.read_loop():
                if inputEvent.type == evdev.ecodes.EV_ABS:
                    if inputEvent.code == evdev.ecodes.ABS_X:
                        event['x'] = inputEvent.value
                    elif inputEvent.code == evdev.ecodes.ABS_Y:
                        event['y'] = inputEvent.value
                    elif inputEvent.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                        event['id'] = inputEvent.value
                        if inputEvent.value == -1:
                            event['x'] = None
                            event['y'] = None
                            event['touch'] = None
                    elif inputEvent.code == evdev.ecodes.ABS_MT_POSITION_X:
                        pass
                    elif inputEvent.code == evdev.ecodes.ABS_MT_POSITION_Y:
                        pass
                elif inputEvent.type == evdev.ecodes.EV_KEY:
                    event['touch'] = inputEvent.value
                elif inputEvent.type == evdev.ecodes.SYN_REPORT:
                    event['time'] = inputEvent.timestamp()
                    self.events.put(event)
                    e = event
                    event = {'x': e['x'], 'y': e['y']}
                    try:
                        event['id'] = e['id']
                    except KeyError:
                        event['id'] = None
                    try:
                        event['touch'] = e['touch']
                    except KeyError:
                        event['touch'] = None

    def __del__(self):
        self.shutdown.set()


class TftEvHandler(object):
    pitft = TftTouchscreen(Screen.TouchscreenInput)
    pitft.pigameevs = []

    def start(self, rotation = 90):

        self.pitft.rotation = rotation
        self.pitft.start()

    def run(self):
        pass

    def stop(self):
        self.pitft.shutdown.set()


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
                    print "Down: ", d
                    pygame.mouse.set_pos(e["x"], e["y"])
                elif t == MOUSEBUTTONUP:
                    l = []
                    for x in self.pitft.pigameevs:
                        if x != r["id"]:
                            l.append(x)
                            self.pitft.pigameevs = l
                    d["button"] = 1
                    d["pos"] = (e["x"], e["y"])
                    print "Up:   ", d
                else:
                    d["buttons"] = (True, False, False)
                    d["rel"] = (0, 0)
                    d["pos"] = (e["x"], e["y"])
                    print d
                    pygame.mouse.set_pos(e["x"], e["y"])
                pe = pygame.event.Event(t, d)
                pygame.event.post(pe)