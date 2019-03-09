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

    def __init__(self, device_path="/dev/input/touchscreen", grab=False):
        super(TftTouchscreen, self).__init__()
        self.device_path = device_path
        self.grab = grab
        self.events = Queue()
        self.shutdown = Event()
        self.devices_capacitive = ["EP0110M09"]
        self.devices_resistive = ["stmpe-ts"]

    def run(self):
        thread_process = Thread(target=self.process_device)
        thread_process.daemon = True
        thread_process.start()
        self.shutdown.wait()

    def process_device(self):
        device = None
        try:
            device = evdev.InputDevice(self.device_path)
            capibilites = device.capabilities(True, True)
            if self.grab:
                device.grab()
        except Exception as ex:
            message = "Unable to load device {0} due to a {1} exception with message: {2}.".format(
                self.device_path, type(ex).__name__, str(ex))
            logger.error(message)
            raise OSError(message)
        finally:
            if device is None:
                self.shutdown.set()
        if device.name in self.devices_capacitive:
            self.capacitive_device(device)
        elif device.name in self.devices_resistive:
            self.resistive_device(device)
        else:
            if self.grab:
                device.ungrab()
            raise OSError("Unsupported evdev device: {}".format(device.name))
        if self.grab:
            device.ungrab()

    def capacitive_device(self, device):
        logger.debug("Loaded device {} successfully.".format(self.device_path))
        event = {'time': None, 'id': None, 'x': None, 'y': None, 'touch': None}
        dropping = False
        while not self.shutdown.is_set():
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
                    if dropping:
                        event['x'] = None
                        event['y'] = None
                        event['touch'] = None
                        dropping = False
                    else:
                        event['time'] = input_event.timestamp()
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
                elif input_event.type == evdev.ecodes.SYN_DROPPED:
                    dropping = True

    def resistive_device(self, device):
        logger.debug("Loaded device {} successfully.".format(self.device_path))
        event = {'time': None, 'id': None, 'x': None, 'y': None, 'touch': None, 'pressure': None}
        dropping = False
        while not self.shutdown.is_set():
            for input_event in device.read_loop():
                if input_event.type == evdev.ecodes.EV_ABS:
                    if input_event.code == evdev.ecodes.ABS_X:
                        event['x'] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_Y:
                        event['y'] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_PRESSURE:
                        event['pressure'] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_X:
                        pass
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                        pass
                elif input_event.type == evdev.ecodes.EV_KEY:
                    event['touch'] = input_event.value
                elif input_event.type == evdev.ecodes.SYN_REPORT:
                    if dropping:
                        event['x'] = None
                        event['y'] = None
                        dropping = False
                    else:
                        if input_event.sec is not None and input_event.usec is not None:
                            event['id'] = "{0}.{1}".format(input_event.sec, input_event.usec)
                        event['time'] = input_event.timestamp()
                        self.events.put(event)
                        e = event
                        event = {'x': e['x'], 'y': e['y']}
                        try:
                            event['pressure'] = e['pressure']
                        except KeyError:
                            event['pressure'] = None
                        try:
                            event['id'] = e['id']
                        except KeyError:
                            event['id'] = None
                        try:
                            event['touch'] = e['touch']
                        except KeyError:
                            event['touch'] = None
                    event['x'] = None
                    event['y'] = None
                    event['touch'] = None
                    event['pressure'] = None
                elif input_event.type == evdev.ecodes.SYN_DROPPED:
                    dropping = True

    def get_event(self):
        if not self.events.empty():
            event = self.events.get()
            yield event
        else:
            yield None

    def queue_empty(self):
        return self.events.empty()

    def stop(self):
        self.shutdown.set()

    def __del__(self):
        self.shutdown.set()


class TftEvHandler(object):
    pitft = None
    prev_loc = {'x': False, 'y': False}
    event_state = 0
    rotation = 0
    resolution = [240, 320]

    def start(self, rotation=90, resolution=None, grab=False):
        if self.resolution is not None:
            self.resolution = resolution
        self.rotation = rotation
        self.pitft = TftTouchscreen(Screen.TouchscreenInput, grab=grab)
        self.pitft.start()

    def run(self):
        pass

    def stop(self):
        self.pitft.stop()


class TftResistiveEvHandler(TftEvHandler):

    def __init__(self):
        self.calibration = [200, 3900, 120, 3800]
        self.x_ratio = 1.0
        self.y_ratio = 1.0

    def start(self, rotation=270, resolution=None, calibration=None, grab=False):
        if calibration is not None:
            self.calibration = calibration
        if resolution is None:
            resolution = self.resolution
        self.x_ratio = float(1) / ((float(self.calibration[1]) - abs(self.calibration[0])) / resolution[0])
        self.y_ratio = float(1) / ((float(self.calibration[3]) - abs(self.calibration[2])) / resolution[1])
        super(TftResistiveEvHandler, self).start(rotation, resolution, grab)

    def run(self):
        while not self.pitft.queue_empty():
            for ts_event in self.pitft.get_event():
                # Set the pygame event coordinates to the last settings.  This
                # allows us to handle the case where a click occured in the
                # same spot on one or both of the axes.
                pg_event = {'y': self.prev_loc['y'], 'x': self.prev_loc['x']}
                if ts_event['x'] is not None:
                    if self.rotation == 0  or self.rotation == 180:
                        pg_event['x'] = int(round((ts_event['x'] - self.calibration[0]) * self.x_ratio))
                    else:
                        pg_event['y'] = int(round((ts_event['x'] - self.calibration[0]) * self.x_ratio))
                if ts_event['y'] is not None:
                    if self.rotation == 0 or self.rotation == 180:
                        pg_event['y'] = int(round((ts_event['y'] - self.calibration[2]) * self.y_ratio))
                    else:
                        pg_event['x'] = int(round((ts_event['y'] - self.calibration[2]) * self.y_ratio))
                # If there is still no X & Y coordinates at this point, throw
                # away the event....something strange is afoot
                if pg_event['x'] is None or pg_event['y'] is None:
                    break
                pg_rel = (pg_event['x'] - self.prev_loc['x'], pg_event['y'] - self.prev_loc['y'])
                self.prev_loc = {'y': pg_event['y'], 'x': pg_event['x']}
                if self.rotation == 0:
                    pg_event = {'x': self.resolution[0] - pg_event['x'], 'y': self.resolution[1] - pg_event['y']}
                    pg_rel = (pg_rel[0] * -1, pg_rel[1] * -1)
                elif self.rotation == 90:
                    pg_event = {'x': pg_event['x'], 'y': self.resolution[0] - pg_event['y']}
                    pg_rel = (pg_rel[0], pg_rel[1] * -1)
                elif self.rotation == 180:
                    pass
                elif self.rotation == 270:
                    pg_event = {'x': self.resolution[1] - pg_event['x'], 'y': pg_event['y']}
                    pg_rel = (pg_rel[0] * -1, pg_rel[1])
                else:
                    raise Exception("Unsupported display rotation")
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
                    pg_dict['rel'] = pg_rel
                    pg_dict['pos'] = (pg_event['x'], pg_event['y'])
                    pygame.mouse.set_pos(pg_event['x'], pg_event['y'])
                pe = pygame.event.Event(pg_event_type, pg_dict)
                pygame.event.post(pe)


class TftCapacitiveEvHandler(TftEvHandler):
    
    def run(self):
        while not self.pitft.queue_empty():
            for ts_event in self.pitft.get_event():
                # Set the pygame event coordinates to the last settings.  This
                # allows us to handle the case where a click occured in the
                # same spot on one or both of the axes.
                pg_event = {'y': self.prev_loc['y'], 'x': self.prev_loc['x']}
                if ts_event['x'] is not None:
                    if self.rotation == 0 or self.rotation == 180:
                        pg_event['x'] = ts_event['x']
                    else:
                        pg_event['y'] = ts_event['x']
                if ts_event['y'] is not None:
                    if self.rotation == 0 or self.rotation == 180:
                        pg_event['y'] = ts_event['y']
                    else:
                        pg_event['x'] = ts_event['y']
                # If there is still no X & Y coordinates at this point, throw
                # away the event....something strange is afoot
                if pg_event['x'] is None or pg_event['y'] is None:
                    break
                pg_rel = (pg_event['x'] - self.prev_loc['x'], pg_event['y'] - self.prev_loc['y'])
                self.prev_loc = {'y': pg_event['y'], 'x': pg_event['x']}
                if self.rotation == 0:
                    pg_event = {'x': self.resolution[0] - pg_event['x'], 'y': self.resolution[1] - pg_event['y']}
                    pg_rel = (pg_rel[0] * -1, pg_rel[1] * -1)
                elif self.rotation == 90:
                    pg_event = {'x': pg_event['x'], 'y': self.resolution[0] - pg_event['y']}
                    pg_rel = (pg_rel[0], pg_rel[1] * -1)
                elif self.rotation == 180:
                    pass
                elif self.rotation == 270:
                    pg_event = {'x': self.resolution[1] - pg_event['x'], 'y': pg_event['y']}
                    pg_rel = (pg_rel[0] * -1, pg_rel[1])
                else:
                    raise Exception("Unsupported display rotation")
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
                    pg_dict['rel'] = pg_rel
                    pg_dict['pos'] = (pg_event['x'], pg_event['y'])
                    pygame.mouse.set_pos(pg_event['x'], pg_event['y'])
                pe = pygame.event.Event(pg_event_type, pg_dict)
                pygame.event.post(pe)