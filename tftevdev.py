#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
import evdev
import pygame
from Queue import Queue
from threading import Thread, Event
from pygame.locals import *
from tftutility import logger, Screen


# Class for handling events from piTFT
class TftTouchscreen(Thread):
    def __init__(self, device_path="/dev/input/touchscreen"):
        super(TftTouchscreen, self).__init__()
        self.device_path = device_path
        self.events = Queue()
        self.shutdown = Event()
        self.rotation = 0

    def run(self):

        thread_process = Thread(target=self.process_device)
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
        except Exception as ex:
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
            for input_event in device.read_loop():
                if input_event.type == evdev.ecodes.EV_ABS:
                    if input_event.code == evdev.ecodes.ABS_X:
                        event['x'] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_Y:
                        event['y'] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                        event['id'] = input_event.value
                        if input_event.value == -1:
                            event['x'] = None
                            event['y'] = None
                            event['touch'] = None
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_X:
                        pass
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                        pass
                elif input_event.type == evdev.ecodes.EV_KEY:
                    event['touch'] = input_event.value
                elif input_event.type == evdev.ecodes.SYN_REPORT:
                    event['time'] = input_event.timestamp()
                    print("{}".format(event))
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
    prev_loc = {'x': False, 'y': False}
    event_state = 0

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
            for ts_event in self.pitft.get_event():
                pg_event = {'y': self.prev_loc['y'], 'x': self.prev_loc['x']}
                if ts_event['x'] is not None:
                    pg_event['y'] = ts_event['x']
                if ts_event['y'] is not None:
                    pg_event['x'] = ts_event['y']
                if  pg_event['x'] is None or pg_event['y'] is None:
                    break
                self.prev_loc = {'y': pg_event['y'], 'x': pg_event['x']}
                if self.pitft.rotation == 90:
                    pg_event = {'x': pg_event['x'], 'y': 240 - pg_event['y']}
                elif self.pitft.rotation == 270:
                    pg_event = {'x': 320 - pg_event['x'], 'y': pg_event['y']}
                else:
                    raise (Exception("Unsupported display rotation"))
                pg_dict = {}
                pg_event_type = MOUSEBUTTONUP if ts_event['touch'] == 0 else (
                    MOUSEBUTTONDOWN if self.event_state == 0 else MOUSEMOTION)
                if pg_event_type == MOUSEBUTTONDOWN:
                    self.event_state = 1
                    pg_dict['button'] = 1
                    pg_dict['pos'] = (pg_event['x'], pg_event['y'])
                    pygame.mouse.set_pos(pg_event['x'], pg_event['y'])
                elif pg_event_type == MOUSEBUTTONUP:
                    self.event_state = 0
                    pg_dict['button'] = 1
                    pg_dict['pos'] = (pg_event['x'], pg_event['y'])
                else:
                    pg_dict['buttons'] = (True, False, False)
                    pg_dict['rel'] = (0, 0)
                    pg_dict['pos'] = (pg_event['x'], pg_event['y'])
                    pygame.mouse.set_pos(pg_event['x'], pg_event['y'])
                pe = pygame.event.Event(pg_event_type, pg_dict)
                pygame.event.post(pe)