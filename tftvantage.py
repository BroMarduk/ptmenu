#
#    Portions Copyright (c) 2009-2016 Tom Keffer <tkeffer@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

"""Classes and functions for interfacing with a Davis VantagePro, VantagePro2,
or VantageVue weather station"""

import datetime
import math
import struct
import time

DRIVER_NAME = 'Vantage'
MAX_RETRIES = 2
VANTAGE_CONFIG = {"type": "serial", "port": "/dev/ttyUSB0", "baudrate": "19200", "wait_before_retry": 1.2,
                  "command_delay": 1, "timeout": 6}

# ===============================================================================
#                           Constants
# ===============================================================================
_ack = chr(0x06)
_resend = chr(0x15)  # NB: The Davis documentation gives this code as 0x21, but it's actually decimal 21


# ===============================================================================
#                           Exception Classes
# ===============================================================================
class DeviceIOError(IOError):
    """Base class of exceptions thrown when encountering an input/output error
    with the hardware."""


class WakeupError(DeviceIOError):
    """Exception thrown when unable to wake up or initially connect with the
    hardware."""


class CRCError(DeviceIOError):
    """Exception thrown when unable to pass a CRC check."""


class RetriesExceeded(DeviceIOError):
    """Exception thrown when max retries exceeded."""


class HardwareError(StandardError):
    """Exception thrown when an error is detected in the hardware."""


class UnknownArchiveType(HardwareError):
    """Exception thrown after reading an unrecognized archive type."""


class UnsupportedFeature(StandardError):
    """Exception thrown when attempting to access a feature that is not
    supported (yet)."""


# ===============================================================================
#                           Utility Functions
# ===============================================================================

# ===============================================================================
#                           Vantage CRC Data
# ===============================================================================
_vantageCrc = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,  # 0x00
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,  # 0x08
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,  # 0x10
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,  # 0x18
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,  # 0x20
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,  # 0x28
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,  # 0x30
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,  # 0x38
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,  # 0x40
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,  # 0x48
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,  # 0x50
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,  # 0x58
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,  # 0x60
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,  # 0x68
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,  # 0x70
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,  # 0x78
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,  # 0x80
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,  # 0x88
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,  # 0x90
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,  # 0x98
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,  # 0xA0
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,  # 0xA8
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,  # 0xB0
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,  # 0xB8
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,  # 0xC0
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,  # 0xC8
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,  # 0xD0
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,  # 0xD8
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,  # 0xE0
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,  # 0xE8
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,  # 0xF0
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0  # 0xF8
]


# ==============================================================================
#                        Conversion Routines
# ==============================================================================
def crc16(string, crc_start=0):
    """ Calculate CRC16 sum"""

    crc_sum = reduce(lambda crc, ch: (_vantageCrc[(crc >> 8) ^ ord(ch)] ^ (crc << 8)) & 0xffff, string, crc_start)

    return crc_sum


def to_int(x):
    if isinstance(x, basestring) and x.lower() == 'none':
        x = None

    return int(x) if x is not None else None


def CtoF(x):
    return x * 1.8 + 32.0


def FtoC(x):
    return (x - 32.0) * 5.0 / 9.0


def dewpointF(T, R):
    if T is None or R is None:
        return None

    TdC = dewpointC(FtoC(T), R)

    return CtoF(TdC) if TdC is not None else None


def dewpointC(T, R):
    if T is None or R is None:
        return None

    R = R / 100.0

    try:
        _gamma = 17.27 * T / (237.7 + T) + math.log(R)
        TdC = 237.7 * _gamma / (17.27 - _gamma)

    except (ValueError, OverflowError):
        TdC = None

    return TdC


def windchillF(T_F, V_mph):
    if T_F is None or V_mph is None:
        return None

    # only valid for temperatures below 50F and wind speeds over 3.0 mph
    if T_F >= 50.0 or V_mph <= 3.0:
        return T_F

    WcF = 35.74 + 0.6215 * T_F + (-35.75 + 0.4275 * T_F) * math.pow(V_mph, 0.16)

    return WcF


def heatindexF(T, R):
    if T is None or R is None:
        return None

    # Formula only valid for temperatures over 80F:
    if T < 80.0 or R < 40.0:
        return T

    hi_F = -42.379 + 2.04901523 * T + 10.14333127 * R - 0.22475541 * T * R - 6.83783e-3 * T ** 2 \
           - 5.481717e-2 * R ** 2 + 1.22874e-3 * T ** 2 * R + 8.5282e-4 * T * R ** 2 - 1.99e-6 * T ** 2 * R ** 2

    if hi_F < T:
        hi_F = T

    return hi_F


def startOfDay(time_ts):
    _time_tt = time.localtime(time_ts)
    _bod_ts = time.mktime((_time_tt.tm_year,
                           _time_tt.tm_mon,
                           _time_tt.tm_mday,
                           0, 0, 0, 0, 0, -1))
    return int(_bod_ts)


# ==============================================================================
#                        class ValueTuple
# ==============================================================================
""" A value, along with the unit it is in, can be represented by a 3-way tuple
    called a value tuple. All routines can accept a simple unadorned
    3-way tuple as a value tuple, but they return the type ValueTuple. It is
    useful because its contents can be accessed using named attributes.

    Item   attribute   Meaning
      0     value      The datum value (eg, 20.2)
      1     unit       The unit it is in ('degree_C")
      2     group      The unit group ("group_temperature")

    It is valid to have a datum value of None.

    It is also valid to have a unit type of None (meaning there is no information
    about the unit the value is in). In this case, you won't be able to convert
    it to another unit. """


class ValueTuple(tuple):
    def __new__(cls, *args):
        return tuple.__new__(cls, args)

    @property
    def value(self):
        return self[0]

    @property
    def unit(self):
        return self[1]

    @property
    def group(self):
        return self[2]

    # ValueTuples have some modest math abilities: subtraction and addition.
    def __sub__(self, other):
        if self[1] != other[1] or self[2] != other[2]:
            raise TypeError("unsupported operand error for subtraction: %s and %s" % (self[1], other[1]))
        return ValueTuple(self[0] - other[0], self[1], self[2])

    def __add__(self, other):
        if self[1] != other[1] or self[2] != other[2]:
            raise TypeError("unsupported operand error for addition: %s and %s" % (self[1], other[1]))
        return ValueTuple(self[0] + other[0], self[1], self[2])


# ===============================================================================
#                           class BaseWrapper
# ===============================================================================

class CommunicationBase(object):
    """Base class for (Serial|Ethernet)Wrapper"""

    def __init__(self, wait_before_retry, command_delay):

        self.wait_before_retry = wait_before_retry
        self.command_delay = command_delay

    def wakeup_console(self, max_tries=MAX_RETRIES):
        """Wake up a Davis Vantage console.

        This call has three purposes:
        1. Wake up a sleeping console;
        2. Cancel pending LOOP data (if any);
        3. Flush the input buffer
           Note: a flushed buffer is important before sending a command; we want to make sure
           the next received character is the expected ACK.

        If unsuccessful, an exception of type WakeupError is thrown"""

        for count in xrange(max_tries):
            try:
                # Wake up console and cancel pending LOOP data.
                # First try a gentle wake up
                self.write('\n')
                _resp = self.read(2)
                if _resp == '\n\r':  # LF, CR = 0x0a, 0x0d
                    # We're done; the console accepted our cancel LOOP command; nothing to flush
                    return
                # That didn't work. Try a rude wake up.
                # Flush any pending LOOP packets
                self.flush_input()
                # Look for the acknowledgment of the sent '\n'
                _resp = self.read(2)
                if _resp == '\n\r':
                    return
                # print "Unable to wake up console... sleeping"
                time.sleep(self.wait_before_retry)
                # print "Unable to wake up console... retrying"
            except DeviceIOError:
                pass

        raise WakeupError("Unable to wake up Vantage console")

    def send_data(self, data):
        """Send data to the Davis console, waiting for an acknowledging <ACK>

        If the <ACK> is not received, no retry is attempted. Instead, an exception
        of type DeviceIOError is raised

        data: The data to send, as a string"""

        self.write(data)

        # Look for the acknowledging ACK character
        _resp = self.read()
        if _resp != _ack:
            raise DeviceIOError("No <ACK> received from Vantage console")

    def send_data_with_crc16(self, data, max_tries=MAX_RETRIES):
        """Send data to the Davis console along with a CRC check, waiting for an acknowledging <ack>.
        If none received, resend up to max_tries times.

        data: The data to send, as a string"""

        # Calculate the crc for the data:
        _crc = crc16(data)

        # ...and pack that on to the end of the data in big-endian order:
        _data_with_crc = data + struct.pack(">H", _crc)

        # Retry up to max_tries times:
        for count in xrange(max_tries):
            try:
                self.write(_data_with_crc)
                # Look for the acknowledgment.
                _resp = self.read()
                if _resp == _ack:
                    return
            except DeviceIOError:
                pass

        raise CRCError("Unable to pass CRC16 check while sending data to Vantage console")

    def send_command(self, command, max_tries=MAX_RETRIES):
        """Send a command to the console, then look for the string 'OK' in the response.

        Any response from the console is split on \n\r characters and returned as a list."""

        for count in xrange(max_tries):
            try:
                self.wakeup_console(max_tries=max_tries)

                self.write(command)
                # Takes some time for the Vantage to react and fill up the buffer. Sleep for a bit:
                time.sleep(self.command_delay)
                # Can't use function serial.readline() because the VP responds with \n\r, not just \n.
                # So, instead find how many bytes are waiting and fetch them all
                nc = self.queued_bytes()
                _buffer = self.read(nc)
                # Split the buffer on the newlines
                _buffer_list = _buffer.strip().split('\n\r')
                # The first member should be the 'OK' in the VP response
                if _buffer_list[0] == 'OK':
                    # Return the rest:
                    return _buffer_list[1:]

            except DeviceIOError:
                # Caught an error. Keep trying...
                pass

        raise RetriesExceeded("Max retries exceeded while sending command %s" % command)

    def get_data_with_crc16(self, nbytes, prompt=None, max_tries=MAX_RETRIES):
        """Get a packet of data and do a CRC16 check on it, asking for retransmit if necessary.

        It is guaranteed that the length of the returned data will be of the requested length.
        An exception of type CRCError will be thrown if the data cannot pass the CRC test
        in the requested number of retries.

        nbytes: The number of bytes (including the 2 byte CRC) to get.

        prompt: Any string to be sent before requesting the data. Default=None

        max_tries: Number of tries before giving up. Default=3

        returns: the packet data as a string. The last 2 bytes will be the CRC"""
        if prompt:
            self.write(prompt)

        first_time = True
        _buffer = ''

        for count in xrange(max_tries):
            try:
                if not first_time:
                    self.write(_resend)
                _buffer = self.read(nbytes)
                if crc16(_buffer) == 0:
                    return _buffer
            except DeviceIOError:
                pass
            first_time = False

        if _buffer:
            raise CRCError("Unable to pass CRC16 check while getting data")
        else:
            raise DeviceIOError("Time out in get_data_with_crc16")


# ===============================================================================
#                           class Serial Wrapper
# ===============================================================================
def guard_termios(fn):
    """Decorator function that converts termios exceptions into our exceptions."""
    # Some functions in the module 'serial' can raise undocumented termios
    # exceptions. This catches them and converts them to our exceptions.
    try:
        import termios
        def guarded_fn(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except termios.error, e:
                raise DeviceIOError(e)
    except ImportError:
        def guarded_fn(*args, **kwargs):
            return fn(*args, **kwargs)
    return guarded_fn


class SerialWrapper(CommunicationBase):
    """Wraps a serial connection returned from package serial"""

    def __init__(self, port, baudrate, timeout, wait_before_retry, command_delay):

        super(SerialWrapper, self).__init__(wait_before_retry=wait_before_retry, command_delay=command_delay)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    @guard_termios
    def flush_input(self):
        self.serial_port.flushInput()

    @guard_termios
    def flush_output(self):
        self.serial_port.flushOutput()

    @guard_termios
    def queued_bytes(self):
        return self.serial_port.inWaiting()

    def read(self, chars=1):
        import serial
        try:
            _buffer = self.serial_port.read(chars)
        except serial.serialutil.SerialException, e:
            # Reraise as an error I/O error:
            raise DeviceIOError(e)
        N = len(_buffer)
        if N != chars:
            raise DeviceIOError("Expected to read %d chars; got %d instead" % (chars, N))
        return _buffer

    def write(self, data):
        import serial
        try:
            N = self.serial_port.write(data)
        except serial.serialutil.SerialException, e:
            # Reraise as an error I/O error:
            raise DeviceIOError(e)
        # Python version 2.5 and earlier returns 'None', so it cannot be used to test for completion.
        if N is not None and N != len(data):
            raise DeviceIOError("Expected to write %d chars; sent %d instead" % (len(data), N))

    def openPort(self):
        import serial
        # Open up the port and store it
        self.serial_port = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def closePort(self):
        try:
            # This will cancel any pending loop:
            self.write('\n')
        except:
            pass
        self.serial_port.close()


# ===============================================================================
#                           class EthernetWrapper
# ===============================================================================

class EthernetWrapper(CommunicationBase):
    """Wrap a socket"""

    def __init__(self, host, port, timeout, tcp_send_delay, wait_before_retry, command_delay):

        super(EthernetWrapper, self).__init__(wait_before_retry=wait_before_retry, command_delay=command_delay)

        self.host = host
        self.port = port
        self.timeout = timeout
        self.tcp_send_delay = tcp_send_delay

    def openPort(self):
        import socket
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
        except (socket.error, socket.timeout, socket.herror), ex:
            # Reraise as an I/O error:
            raise DeviceIOError(ex)
        except:
            raise

    def closePort(self):
        import socket
        try:
            # This will cancel any pending loop:
            self.write('\n')
        except:
            pass
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def flush_input(self):
        """Flush the input buffer from WeatherLinkIP"""
        import socket
        try:
            # This is a bit of a hack, but there is no analogue to pyserial's flushInput()
            # Set socket timeout to 0 to get immediate result
            self.socket.settimeout(0)
            self.socket.recv(4096)
        except (socket.timeout, socket.error):
            pass
        finally:
            # set socket timeout back to original value
            self.socket.settimeout(self.timeout)

    def flush_output(self):
        """Flush the output buffer to WeatherLinkIP

        This function does nothing as there should never be anything left in
        the buffer when using socket.sendall()"""
        pass

    def queued_bytes(self):
        """Determine how many bytes are in the buffer"""
        import socket
        length = 0
        try:
            self.socket.settimeout(0)
            length = len(self.socket.recv(8192, socket.MSG_PEEK))
        except socket.error:
            pass
        finally:
            self.socket.settimeout(self.timeout)
        return length

    def read(self, chars=1):
        """Read bytes from WeatherLinkIP"""
        import socket
        _buffer = ''
        _remaining = chars
        while _remaining:
            _N = min(4096, _remaining)
            try:
                _recv = self.socket.recv(_N)
            except (socket.timeout, socket.error), ex:
                # Reraise as an I/O error:
                raise DeviceIOError(ex)
            _nread = len(_recv)
            if _nread == 0:
                raise DeviceIOError("vantage: Expected %d characters; got zero instead" % (_N,))
            _buffer += _recv
            _remaining -= _nread
        return _buffer

    def write(self, data):
        """Write to a WeatherLinkIP"""
        import socket
        try:
            self.socket.sendall(data)
            # A delay of 0.0 gives socket write error; 0.01 gives no ack error; 0.05 is OK for our program
            # Note: a delay of 0.5 s is required for wee_device --logger=logger_info
            time.sleep(self.tcp_send_delay)
        except (socket.timeout, socket.error), ex:
            # Reraise as an I/O error:
            raise DeviceIOError(ex)


# ===============================================================================
#                           class Vantage
# ===============================================================================
class Vantage():
    """Class that represents a connection to a Davis Vantage console.

    The connection to the console will be open after initialization"""

    # Various codes used internally by the VP2:
    barometer_unit_dict = {0: 'inHg', 1: 'mmHg', 2: 'hPa', 3: 'mbar'}
    temperature_unit_dict = {0: 'degree_F', 1: 'degree_10F', 2: 'degree_C', 3: 'degree_10C'}
    altitude_unit_dict = {0: 'foot', 1: 'meter'}
    rain_unit_dict = {0: 'inch', 1: 'mm'}
    wind_unit_dict = {0: 'mile_per_hour', 1: 'meter_per_second', 2: 'km_per_hour', 3: 'knot'}
    wind_cup_dict = {0: 'small', 1: 'large'}
    rain_bucket_dict = {0: "0.01 inches", 1: "0.2 MM", 2: "0.1 MM"}
    transmitter_type_dict = {0: 'iss', 1: 'temp', 2: 'hum', 3: 'temp_hum', 4: 'wind',
                             5: 'rain', 6: 'leaf', 7: 'soil', 8: 'leaf_soil',
                             9: 'sensorlink', 10: 'none'}

    def __init__(self, **vp_dict):
        """Initialize an object of type Vantage.

        NAMED ARGUMENTS:

        connection_type: The type of connection (serial|ethernet) [Required]
        port: The serial port of the VP. [Required if serial/USB communication]
        host: The Vantage network host [Required if Ethernet communication]
        baudrate: Baudrate of the port. [Optional. Default 19200]
        tcp_port: TCP port to connect to [Optional. Default 22222]
        tcp_send_delay: Block after sending data to WeatherLinkIP to allow it to process the command [Optional. Default is 0.5]
        timeout: How long to wait before giving up on a response from the serial port. [Optional. Default is 4]
        wait_before_retry: How long to wait before retrying. [Optional. Default is 1.2 seconds]
        command_delay: How long to wait after sending a command before looking for acknowledgement. [Optional. Default is 0.5 seconds]
        max_tries: How many times to try again before giving up. [Optional. Default is 4]
        iss_id: The station number of the ISS [Optional. Default is 1]
        """

        # TODO: These values should really be retrieved dynamically from the VP:
        self.model_type = 2  # = 1 for original VantagePro, = 2 for VP2

        # These come from the configuration dictionary:
        self.max_tries = int(vp_dict.get('max_tries', 4))
        self.iss_id = to_int(vp_dict.get('iss_id'))

        self.save_monthRain = None
        self.max_dst_jump = 7200

        # Get an appropriate port, depending on the connection type:
        self.port = Vantage._port_factory(vp_dict)

        # Open it up:
        self.port.openPort()

        # Read the EEPROM and fill in properties in this instance
        self._setup()

    def __del__(self):
        self.closePort()

    def openPort(self):
        """Open up the connection to the console"""
        self.port.openPort()

    def closePort(self):
        """Close the connection to the console. """
        self.port.closePort()

    def getWeatherLoop(self, numLoops=1):

        try:
            loop_gen = self.genDavisLoopPackets(numLoops)
            list_loop = []

            for loop_item in loop_gen:
                list_loop.append(loop_item)

        except:
            list_loop = None

        return list_loop

    def getLatestWeatherLoop(self):

        try:
            loop_gen = self.genDavisLoopPackets(1)
            loop_item = next(loop_gen)

        except:
            loop_item = None

        return loop_item

    def genLoopPackets(self):
        """Generator function that returns loop packets"""

        for count in range(self.max_tries):
            while True:
                try:
                    # Get LOOP packets in big batches This is necessary because there is
                    # an undocumented limit to how many LOOP records you can request
                    # on the VP (somewhere around 220).
                    for _loop_packet in self.genDavisLoopPackets(200):
                        yield _loop_packet
                except DeviceIOError, e:
                    break

        raise RetriesExceeded("Max tries exceeded while getting LOOP data.")

    def genDavisLoopPackets(self, N=1):
        """Generator function to return N loop packets from a Vantage console

        N: The number of packets to generate [default is 1]
        yields: up to N loop packets (could be less in the event of a read or CRC error).
        """

        self.port.wakeup_console(self.max_tries)

        # Request N packets:
        self.port.send_data("LOOP %d\n" % N)

        for loop in range(N):  # @UnusedVariable
            # Fetch a packet...
            _buffer = self.port.read(99)
            # ... see if it passes the CRC test ...
            if crc16(_buffer):
                raise CRCError("LOOP buffer failed CRC check")
            # ... decode it ...
            loop_packet = self._unpackLoopPacket(_buffer[:95])
            # .. then yield it
            yield loop_packet

    def genArchiveRecords(self, since_ts):
        """A generator function to return archive packets from a Davis Vantage station.

        since_ts: A timestamp. All data since (but not including) this time will be returned.
        Pass in None for all data
        yields: a sequence of dictionaries containing the data
        """

        count = 0
        while count < self.max_tries:
            try:
                for _record in self.genDavisArchiveRecords(since_ts):
                    # Successfully retrieved record. Set count back to zero.
                    count = 0
                    since_ts = _record['dateTime']
                    yield _record
                # The generator loop exited. We're done.
                return
            except DeviceIOError, e:
                # Problem. Increment retry count
                count += 1

        raise RetriesExceeded("Max tries exceeded while getting archive data.")

    def genDavisArchiveRecords(self, since_ts):
        """A generator function to return archive records from a Davis Vantage station.

        This version does not catch any exceptions."""

        if since_ts:
            since_tt = time.localtime(since_ts)
            # NB: note that some of the Davis documentation gives the year offset as 1900.
            # From experimentation, 2000 seems to be right, at least for the newer models:
            _vantageDateStamp = since_tt[2] + (since_tt[1] << 5) + ((since_tt[0] - 2000) << 9)
            _vantageTimeStamp = since_tt[3] * 100 + since_tt[4]

        else:
            _vantageDateStamp = _vantageTimeStamp = 0

        # Pack the date and time into a string, little-endian order
        _datestr = struct.pack("<HH", _vantageDateStamp, _vantageTimeStamp)

        # Save the last good time:
        _last_good_ts = since_ts if since_ts else 0

        # Get the starting page and index. First, wake up the console...
        self.port.wakeup_console(self.max_tries)
        # ... request a dump...
        self.port.send_data('DMPAFT\n')
        # ... from the designated date (allow only one try because that's all the console allows):
        self.port.send_data_with_crc16(_datestr, max_tries=1)

        # Get the response with how many pages and starting index and decode it. Again, allow only one try:
        _buffer = self.port.get_data_with_crc16(6, max_tries=1)

        (_npages, _start_index) = struct.unpack("<HH", _buffer[:4])

        # Cycle through the pages...
        for ipage in xrange(_npages):
            # ... get a page of archive data
            _page = self.port.get_data_with_crc16(267, prompt=_ack, max_tries=1)
            # Now extract each record from the page
            for _index in xrange(_start_index, 5):
                # Get the record string buffer for this index:
                _record_string = _page[1 + 52 * _index:53 + 52 * _index]
                # If the console has been recently initialized, there will
                # be unused records, which are filled with 0xff. Detect this
                # by looking at the first 4 bytes (the date and time):
                if _record_string[0:4] == 4 * chr(0xff) or _record_string[0:4] == 4 * chr(0x00):
                    # This record has never been used. We're done.
                    return

                # Unpack the archive packet from the string buffer:
                _record = self._unpackArchivePacket(_record_string)

                # Check to see if the time stamps are declining, which would
                # signal that we are done.
                if _record['dateTime'] is None or _record['dateTime'] <= _last_good_ts - self.max_dst_jump:
                    # The time stamp is declining. We're done.
                    return
                # Set the last time to the current time, and yield the packet
                _last_good_ts = _record['dateTime']
                yield _record

            # The starting index for pages other than the first is always zero
            _start_index = 0

    def genArchiveDump(self):
        """A generator function to return all archive packets in the memory of a Davis Vantage station.

        yields: a sequence of dictionaries containing the data
        """

        # Wake up the console...
        self.port.wakeup_console(self.max_tries)
        # ... request a dump...
        self.port.send_data('DMP\n')

        # Cycle through the pages...
        for ipage in xrange(512):
            # ... get a page of archive data
            _page = self.port.get_data_with_crc16(267, prompt=_ack, max_tries=self.max_tries)
            # Now extract each record from the page
            for _index in xrange(5):
                # Get the record string buffer for this index:
                _record_string = _page[1 + 52 * _index:53 + 52 * _index]
                # If the console has been recently initialized, there will
                # be unused records, which are filled with 0xff. Detect this
                # by looking at the first 4 bytes (the date and time):
                if _record_string[0:4] == 4 * chr(0xff) or _record_string[0:4] == 4 * chr(0x00):
                    # This record has never been used. Skip it
                    continue
                # Unpack the raw archive packet:
                _record = self._unpackArchivePacket(_record_string)

                # Because the dump command does not go through the normal
                # engine pipeline, we have to add these important software derived
                # variables here.
                try:
                    T = _record['outTemp']
                    R = _record['outHumidity']
                    W = _record['windSpeed']

                    _record['dewpoint'] = dewpointF(T, R)
                    _record['heatindex'] = heatindexF(T, R)
                    _record['windchill'] = windchillF(T, W)
                except KeyError:
                    pass

                yield _record

    def genLoggerSummary(self):
        """A generator function to return a summary of each page in the logger.

        yields: A 8-way tuple containing (page, index, year, month, day, hour, minute, timestamp)
        """

        # Wake up the console...
        self.port.wakeup_console(self.max_tries)
        # ... request a dump...
        self.port.send_data('DMP\n')

        # Cycle through the pages...
        for _ipage in xrange(512):
            # ... get a page of archive data
            _page = self.port.get_data_with_crc16(267, prompt=_ack, max_tries=self.max_tries)
            # Now extract each record from the page
            for _index in xrange(5):
                # Get the record string buffer for this index:
                _record_string = _page[1 + 52 * _index:53 + 52 * _index]
                # If the console has been recently initialized, there will
                # be unused records, which are filled with 0xff. Detect this
                # by looking at the first 4 bytes (the date and time):
                if _record_string[0:4] == 4 * chr(0xff) or _record_string[0:4] == 4 * chr(0x00):
                    # This record has never been used.
                    y = mo = d = h = mn = time_ts = None
                else:
                    # Extract the date and time from the raw buffer:
                    datestamp, timestamp = struct.unpack("<HH", _record_string[0:4])
                    time_ts = _archive_datetime(datestamp, timestamp)
                    y = (0xfe00 & datestamp) >> 9  # year
                    mo = (0x01e0 & datestamp) >> 5  # month
                    d = (0x001f & datestamp)  # day
                    h = timestamp // 100  # hour
                    mn = timestamp % 100  # minute
                yield (_ipage, _index, y, mo, d, h, mn, time_ts)

    def getTime(self):
        """Get the current time from the console, returning it as timestamp"""

        time_dt = self.getConsoleTime()
        return time.mktime(time_dt.timetuple())

    def getConsoleTime(self):
        """Return the raw time on the console, uncorrected for DST or timezone."""

        # Try up to max_tries times:
        for unused_count in xrange(self.max_tries):
            try:
                # Wake up the console...
                self.port.wakeup_console(max_tries=self.max_tries)
                # ... request the time...
                self.port.send_data('GETTIME\n')
                # ... get the binary data. No prompt, only one try:
                _buffer = self.port.get_data_with_crc16(8, max_tries=1)
                (sec, minute, hr, day, mon, yr, unused_crc) = struct.unpack("<bbbbbbH", _buffer)

                return datetime.datetime(yr + 1900, mon, day, hr, minute, sec)

            except DeviceIOError:
                # Caught an error. Keep retrying...
                continue
        raise RetriesExceeded("While getting console time")

    def getRX(self):
        """Returns reception statistics from the console.

        Returns a tuple with 5 values: (# of packets, # of missed packets,
        # of resynchronizations, the max # of packets received w/o an error,
        the # of CRC errors detected.)"""

        rx_list = self.port.send_command('RXCHECK\n')

        # The following is a list of the reception statistics, but the elements are strings
        rx_list_str = rx_list[0].split()
        # Convert to numbers and return as a tuple:
        rx_list = tuple(int(x) for x in rx_list_str)
        return rx_list

    def getBarData(self):
        """Gets barometer calibration data. Returns as a 9 element list."""
        _bardata = self.port.send_command("BARDATA\n")
        _barometer = float(_bardata[0].split()[1]) / 1000.0
        _altitude = float(_bardata[1].split()[1])
        _dewpoint = float(_bardata[2].split()[2])
        _virt_temp = float(_bardata[3].split()[2])
        _c = float(_bardata[4].split()[1])
        _r = float(_bardata[5].split()[1]) / 1000.0
        _barcal = float(_bardata[6].split()[1]) / 1000.0
        _gain = float(_bardata[7].split()[1])
        _offset = float(_bardata[8].split()[1])

        return (_barometer, _altitude, _dewpoint, _virt_temp, _c, _r, _barcal, _gain, _offset)

    def getFirmwareDate(self):
        """Return the firmware date as a string. """
        return self.port.send_command('VER\n')[0]

    def getFirmwareVersion(self):
        """Return the firmware version as a string."""
        return self.port.send_command('NVER\n')[0]

    def getStnInfo(self):
        """Return lat / lon, time zone, etc."""

        (stnlat, stnlon) = self._getEEPROM_value(0x0B, "<2h")
        stnlat /= 10.0
        stnlon /= 10.0
        man_or_auto = "MANUAL" if self._getEEPROM_value(0x12)[0] else "AUTO"
        dst = "ON" if self._getEEPROM_value(0x13)[0] else "OFF"
        gmt_or_zone = "GMT_OFFSET" if self._getEEPROM_value(0x16)[0] else "ZONE_CODE"
        zone_code = self._getEEPROM_value(0x11)[0]
        gmt_offset = self._getEEPROM_value(0x14, "<h")[0] / 100.0

        return (stnlat, stnlon, man_or_auto, dst, gmt_or_zone, zone_code, gmt_offset)

    def getStnTransmitters(self):
        """ Get the types of transmitters on the eight channels."""

        transmitters = []
        use_tx = self._getEEPROM_value(0x17)[0]
        transmitter_data = self._getEEPROM_value(0x19, "16B")

        for transmitter_id in range(8):
            transmitter_type = Vantage.transmitter_type_dict[transmitter_data[transmitter_id * 2] & 0x0F]
            transmitter = {"transmitter_type": transmitter_type, "listen": (use_tx >> transmitter_id) & 1}
            if transmitter_type in ['temp', 'temp_hum']:
                # Extra temperature is origin 0.
                transmitter['temp'] = (transmitter_data[transmitter_id * 2 + 1] & 0xF) + 1
            if transmitter_type in ['hum', 'temp_hum']:
                # Extra humidity is origin 1.
                transmitter['hum'] = transmitter_data[transmitter_id * 2 + 1] >> 4
            transmitters.append(transmitter)
        return transmitters

    def getStnCalibration(self):
        """ Get the temperature/humidity/wind calibrations built into the console. """
        (inTemp, inTempComp, outTemp,
         extraTemp1, extraTemp2, extraTemp3, extraTemp4, extraTemp5, extraTemp6, extraTemp7,
         soilTemp1, soilTemp2, soilTemp3, soilTemp4, leafTemp1, leafTemp2, leafTemp3, leafTemp4,
         inHumid,
         outHumid, extraHumid1, extraHumid2, extraHumid3, extraHumid4, extraHumid5, extraHumid6, extraHumid7,
         wind) = self._getEEPROM_value(0x32, "<27bh")
        # inTempComp is 1's complement of inTemp.
        if inTemp + inTempComp != -1:
            return None
        # Temperatures are in tenths of a degree F; Humidity in 1 percent.
        return {
            "inTemp": inTemp / 10,
            "outTemp": outTemp / 10,
            "extraTemp1": extraTemp1 / 10,
            "extraTemp2": extraTemp2 / 10,
            "extraTemp3": extraTemp3 / 10,
            "extraTemp4": extraTemp4 / 10,
            "extraTemp5": extraTemp5 / 10,
            "extraTemp6": extraTemp6 / 10,
            "extraTemp7": extraTemp7 / 10,
            "soilTemp1": soilTemp1 / 10,
            "soilTemp2": soilTemp2 / 10,
            "soilTemp3": soilTemp3 / 10,
            "soilTemp4": soilTemp4 / 10,
            "leafTemp1": leafTemp1 / 10,
            "leafTemp2": leafTemp2 / 10,
            "leafTemp3": leafTemp3 / 10,
            "leafTemp4": leafTemp4 / 10,
            "inHumid": inHumid,
            "outHumid": outHumid,
            "extraHumid1": extraHumid1,
            "extraHumid2": extraHumid2,
            "extraHumid3": extraHumid3,
            "extraHumid4": extraHumid4,
            "extraHumid5": extraHumid5,
            "extraHumid6": extraHumid6,
            "extraHumid7": extraHumid7,
            "wind": wind
        }

    def startLogger(self):
        self.port.send_command("START\n")

    def stopLogger(self):
        self.port.send_command('STOP\n')

    # ===========================================================================
    #              Davis Vantage utility functions
    # ===========================================================================

    @property
    def hardware_name(self):
        if self.hardware_type == 16:
            return "VantagePro2"
        elif self.hardware_type == 17:
            return "VantageVue"
        else:
            raise UnsupportedFeature("Unknown hardware type %d" % self.hardware_type)

    @property
    def archive_interval(self):
        return self.archive_interval_

    def determine_hardware(self):
        # Determine the type of hardware:
        for count in xrange(self.max_tries):
            try:
                self.port.send_data("WRD" + chr(0x12) + chr(0x4d) + "\n")
                self.hardware_type = ord(self.port.read())
                # 16 = Pro, Pro2, 17 = Vue
                return self.hardware_type
            except DeviceIOError:
                pass

        raise DeviceIOError("Unable to read hardware type")

    def _setup(self):
        """Retrieve the EEPROM data block from a VP2 and use it to set various properties"""

        self.port.wakeup_console(max_tries=self.max_tries)
        self.hardware_type = self.determine_hardware()

        """Retrieve the EEPROM data block from a VP2 and use it to set various properties"""
        unit_bits = self._getEEPROM_value(0x29)[0]
        setup_bits = self._getEEPROM_value(0x2B)[0]
        self.rain_year_start = self._getEEPROM_value(0x2C)[0]
        self.archive_interval_ = self._getEEPROM_value(0x2D)[0] * 60
        self.altitude = self._getEEPROM_value(0x0F, "<h")[0]
        self.altitude_vt = ValueTuple(self.altitude, "foot", "group_altitude")

        barometer_unit_code = unit_bits & 0x03
        temperature_unit_code = (unit_bits & 0x0C) >> 2
        altitude_unit_code = (unit_bits & 0x10) >> 4
        rain_unit_code = (unit_bits & 0x20) >> 5
        wind_unit_code = (unit_bits & 0xC0) >> 6

        self.wind_cup_type = (setup_bits & 0x08) >> 3
        self.rain_bucket_type = (setup_bits & 0x30) >> 4

        self.barometer_unit = Vantage.barometer_unit_dict[barometer_unit_code]
        self.temperature_unit = Vantage.temperature_unit_dict[temperature_unit_code]
        self.altitude_unit = Vantage.altitude_unit_dict[altitude_unit_code]
        self.rain_unit = Vantage.rain_unit_dict[rain_unit_code]
        self.wind_unit = Vantage.wind_unit_dict[wind_unit_code]
        self.wind_cup_size = Vantage.wind_cup_dict[self.wind_cup_type]
        self.rain_bucket_size = Vantage.rain_bucket_dict[self.rain_bucket_type]

        # Adjust the translation maps to reflect the rain bucket size:
        if self.rain_bucket_type == 1:
            _archive_map['rain'] = _archive_map['rainRate'] = _loop_map['stormRain'] = _loop_map['dayRain'] = \
                _loop_map['monthRain'] = _loop_map['yearRain'] = _bucket_1
            _loop_map['rainRate'] = _bucket_1_None
        elif self.rain_bucket_type == 2:
            _archive_map['rain'] = _archive_map['rainRate'] = _loop_map['stormRain'] = _loop_map['dayRain'] = \
                _loop_map['monthRain'] = _loop_map['yearRain'] = _bucket_2
            _loop_map['rainRate'] = _bucket_2_None
        else:
            _archive_map['rain'] = _archive_map['rainRate'] = _loop_map['stormRain'] = _loop_map['dayRain'] = \
                _loop_map['monthRain'] = _loop_map['yearRain'] = _val100
            _loop_map['rainRate'] = _big_val100

        # Try to guess the ISS ID for gauging reception strength.
        if self.iss_id is None:
            stations = self.getStnTransmitters()
            # Wind retransmitter is best candidate.
            for station_id in range(0, 8):
                if stations[station_id]['transmitter_type'] == 'wind':
                    self.iss_id = station_id + 1  # Origin 1.
                    break
            else:
                # ISS is next best candidate.
                for station_id in range(0, 8):
                    if stations[station_id]['transmitter_type'] == 'iss':
                        self.iss_id = station_id + 1  # Origin 1.
                        break
                else:
                    # On Vue, can use VP2 ISS, which reports as "rain"
                    for station_id in range(0, 8):
                        if stations[station_id]['transmitter_type'] == 'rain':
                            self.iss_id = station_id + 1  # Origin 1.
                            break
                    else:
                        self.iss_id = 1  # Pick a reasonable default.

    def _getEEPROM_value(self, offset, v_format="B"):
        """Return a list of values from the EEPROM starting at a specified offset, using a specified format"""

        nbytes = struct.calcsize(v_format)
        # Don't bother waking up the console for the first try. It's probably
        # already awake from opening the port. However, if we fail, then do a
        # wakeup.
        firsttime = True

        command = "EEBRD %X %X\n" % (offset, nbytes)
        for unused_count in xrange(self.max_tries):
            try:
                if not firsttime:
                    self.port.wakeup_console(max_tries=self.max_tries)
                firsttime = False
                self.port.send_data(command)
                _buffer = self.port.get_data_with_crc16(nbytes + 2, max_tries=1)
                _value = struct.unpack(v_format, _buffer[:-2])
                return _value
            except DeviceIOError:
                continue

        raise RetriesExceeded("While getting EEPROM data value at address 0x%X" % offset)

    @staticmethod
    def _port_factory(vp_dict):
        """Produce a serial or ethernet port object"""

        timeout = float(vp_dict.get('timeout', 4.0))
        wait_before_retry = float(vp_dict.get('wait_before_retry', 1.2))
        command_delay = float(vp_dict.get('command_delay', 0.5))

        # Get the connection type. If it is not specified, assume 'serial':
        connection_type = vp_dict.get('type', 'serial').lower()

        if connection_type == "serial":
            port = vp_dict['port']
            baudrate = int(vp_dict.get('baudrate', 19200))
            return SerialWrapper(port, baudrate, timeout, wait_before_retry, command_delay)
        elif connection_type == "ethernet":
            hostname = vp_dict['host']
            tcp_port = int(vp_dict.get('tcp_port', 22222))
            tcp_send_delay = float(vp_dict.get('tcp_send_delay', 0.5))
            return EthernetWrapper(hostname, tcp_port, timeout, tcp_send_delay, wait_before_retry, command_delay)
        raise UnsupportedFeature(vp_dict['type'])

    def _unpackLoopPacket(self, raw_loop_string):
        """Decode a raw Davis LOOP packet, returning the results as a dictionary in physical units.

        raw_loop_string: The loop packet data buffer, passed in as a string.

        returns:

        A dictionary. The key will be an observation type, the value will be
        the observation in physical units."""

        # Unpack the data, using the compiled stuct.Struct string 'loop_fmt'
        data_tuple = loop_fmt.unpack(raw_loop_string)

        # Put the results in a dictionary. The values will not be in physical units yet,
        # but rather using the raw values from the console.
        raw_loop_packet = dict(zip(loop_types, data_tuple))

        # Detect the kind of LOOP packet. Type 'A' has the character 'P' in this
        # position. Type 'B' contains the 3-hour barometer trend in this position.
        if raw_loop_packet['loop_type'] == ord('P'):
            raw_loop_packet['trend'] = None
            raw_loop_packet['loop_type'] = 'A'
        else:
            raw_loop_packet['trend'] = raw_loop_packet['loop_type']
            raw_loop_packet['loop_type'] = 'B'

        loop_packet = {'dateTime': int(time.time() + 0.5),
                       'usUnits': 'US'}

        for _type in raw_loop_packet:
            # Get the mapping function for this type:
            func = _loop_map.get(_type)
            # It it exists, apply it:
            if func:
                # Call the function, with the value as an argument, storing the result:
                loop_packet[_type] = func(raw_loop_packet[_type])

        # Adjust sunrise and sunset:
        start_of_day = startOfDay(loop_packet['dateTime'])
        loop_packet['sunrise'] += start_of_day
        loop_packet['sunset'] += start_of_day

        # Because the Davis stations do not offer bucket tips in LOOP data, we
        # must calculate it by looking for changes in rain totals. This won't
        # work for the very first rain packet.
        if self.save_monthRain is None:
            delta = None
        else:
            delta = loop_packet['monthRain'] - self.save_monthRain
            # If the difference is negative, we're at the beginning of a month.
            if delta < 0: delta = None
        loop_packet['rain'] = delta
        self.save_monthRain = loop_packet['monthRain']

        if not raw_loop_packet['trend'] is None:
            loop_packet['barometricTrend'] = raw_loop_packet['trend']

        return loop_packet

    def _unpackArchivePacket(self, raw_archive_string):
        """Decode a Davis archive packet, returning the results as a dictionary.

        raw_archive_string: The archive packet data buffer, passed in as a string. This will be unpacked and
        the results placed a dictionary"""

        # Figure out the packet type:
        packet_type = ord(raw_archive_string[42])

        if packet_type == 0xff:
            # Rev A packet type:
            archive_format = rec_fmt_A
            dataTypes = rec_types_A
        elif packet_type == 0x00:
            # Rev B packet type:
            archive_format = rec_fmt_B
            dataTypes = rec_types_B
        else:
            raise UnknownArchiveType("Unknown archive type = 0x%x" % (packet_type,))

        data_tuple = archive_format.unpack(raw_archive_string)

        raw_archive_packet = dict(zip(dataTypes, data_tuple))

        archive_packet = {
            'dateTime': _archive_datetime(raw_archive_packet['date_stamp'], raw_archive_packet['time_stamp']),
            'usUnits': 'US'}

        for _type in raw_archive_packet:
            # Get the mapping function for this type:
            func = _archive_map.get(_type)
            # It it exists, apply it:
            if func:
                # Call the function, with the value as an argument, storing the result:
                archive_packet[_type] = func(raw_archive_packet[_type])

        # Divide archive interval by 60 to keep consistent with wview
        archive_packet['interval'] = int(self.archive_interval / 60)
        archive_packet['rxCheckPercent'] = _rxcheck(self.model_type, archive_packet['interval'],
                                                    self.iss_id, raw_archive_packet['number_of_wind_samples'])
        return archive_packet


def _rxcheck(model_type, interval, iss_id, number_of_wind_samples):
    """Gives an estimate of the fraction of packets received.

    Ref: Vantage Serial Protocol doc, V2.1.0, released 25-Jan-05; p42"""
    # The formula for the expected # of packets varies with model number.
    if model_type == 1:
        _expected_packets = float(interval * 60) / (2.5 + (iss_id - 1) / 16.0) - \
                            float(interval * 60) / (50.0 + (iss_id - 1) * 1.25)
    elif model_type == 2:
        _expected_packets = 960.0 * interval / float(41 + iss_id - 1)
    else:
        return None
    _frac = number_of_wind_samples * 100.0 / _expected_packets
    if _frac > 100.0:
        _frac = 100.0
    return _frac


# ===============================================================================
#                      Decoding routines
# ===============================================================================
def _archive_datetime(datestamp, timestamp):
    """Returns the epoch time of the archive packet."""
    try:
        # Construct a time tuple from Davis time. Unfortunately, as timestamps come
        # off the Vantage logger, there is no way of telling whether or not DST is
        # in effect. So, have the operating system guess by using a '-1' in the last
        # position of the time tuple. It's the best we can do...
        time_tuple = ((0xfe00 & datestamp) >> 9,  # year
                      (0x01e0 & datestamp) >> 5,  # month
                      (0x001f & datestamp),  # day
                      timestamp // 100,  # hour
                      timestamp % 100,  # minute
                      0,  # second
                      0, 0, -1)  # have OS guess DST
        # Convert to epoch time:
        ts = int(time.mktime(time_tuple))
    except (OverflowError, ValueError, TypeError):
        ts = None
    return ts


def _loop_date(v):
    """Returns the epoch time stamp of a time encoded in the LOOP packet,
    which, for some reason, uses a different encoding scheme than the archive packet.
    Also, the Davis documentation isn't clear whether "bit 0" refers to the least-significant
    bit, or the most-significant bit. I'm assuming the former, which is the usual
    in little-endian machines."""
    if v == 0xffff:
        return None
    time_tuple = ((0x007f & v) + 2000,  # year
                  (0xf000 & v) >> 12,  # month
                  (0x0f80 & v) >> 7,  # day
                  0, 0, 0,  # h, m, s
                  0, 0, -1)
    # Convert to epoch time:
    try:
        ts = int(time.mktime(time_tuple))
    except (OverflowError, ValueError):
        ts = None
    return ts


def _stime(v):
    h = v / 100
    m = v % 100
    # Return seconds since midnight
    return 3600 * h + 60 * m


def _big_val(v):
    return float(v) if v != 0x7fff else None


def _big_val10(v):
    return float(v) / 10.0 if v != 0x7fff else None


def _big_val100(v):
    return float(v) / 100.0 if v != 0xffff else None


def _val100(v):
    return float(v) / 100.0


def _val1000(v):
    return float(v) / 1000.0


def _val1000Zero(v):
    return float(v) / 1000.0 if v != 0 else None


def _little_val(v):
    return float(v) if v != 0x00ff else None


def _little_val10(v):
    return float(v) / 10.0 if v != 0x00ff else None


def _little_temp(v):
    return float(v - 90) if v != 0x00ff else None


def _null(v):
    return v


def _null_float(v):
    return float(v)


def _null_int(v):
    return int(v)


def _windDir(v):
    return float(v) * 22.5 if v != 0x00ff else None


# Rain bucket type "1", a 0.2 mm bucket
def _bucket_1(v):
    return float(v) * 0.00787401575


def _bucket_1_None(v):
    return float(v) * 0.00787401575 if v != 0xffff else None


# Rain bucket type "2", a 0.1 mm bucket
def _bucket_2(v):
    return float(v) * 0.00393700787


def _bucket_2_None(v):
    return float(v) * 0.00393700787 if v != 0xffff else None


# ===============================================================================
#                                 LOOP packet
# ===============================================================================

# A list of all the types held in a Vantage LOOP packet in their native order.
loop_format = [('loop', '3s'), ('loop_type', 'b'), ('packet_type', 'B'),
               ('next_record', 'H'), ('barometer', 'H'), ('inTemp', 'h'),
               ('inHumidity', 'B'), ('outTemp', 'h'), ('windSpeed', 'B'),
               ('windSpeed10', 'B'), ('windDir', 'H'), ('extraTemp1', 'B'),
               ('extraTemp2', 'B'), ('extraTemp3', 'B'), ('extraTemp4', 'B'),
               ('extraTemp5', 'B'), ('extraTemp6', 'B'), ('extraTemp7', 'B'),
               ('soilTemp1', 'B'), ('soilTemp2', 'B'), ('soilTemp3', 'B'),
               ('soilTemp4', 'B'), ('leafTemp1', 'B'), ('leafTemp2', 'B'),
               ('leafTemp3', 'B'), ('leafTemp4', 'B'), ('outHumidity', 'B'),
               ('extraHumid1', 'B'), ('extraHumid2', 'B'), ('extraHumid3', 'B'),
               ('extraHumid4', 'B'), ('extraHumid5', 'B'), ('extraHumid6', 'B'),
               ('extraHumid7', 'B'), ('rainRate', 'H'), ('UV', 'B'),
               ('radiation', 'H'), ('stormRain', 'H'), ('stormStart', 'H'),
               ('dayRain', 'H'), ('monthRain', 'H'), ('yearRain', 'H'),
               ('dayET', 'H'), ('monthET', 'H'), ('yearET', 'H'),
               ('soilMoist1', 'B'), ('soilMoist2', 'B'), ('soilMoist3', 'B'),
               ('soilMoist4', 'B'), ('leafWet1', 'B'), ('leafWet2', 'B'),
               ('leafWet3', 'B'), ('leafWet4', 'B'), ('insideAlarm', 'B'),
               ('rainAlarm', 'B'), ('outsideAlarm1', 'B'), ('outsideAlarm2', 'B'),
               ('extraAlarm1', 'B'), ('extraAlarm2', 'B'), ('extraAlarm3', 'B'),
               ('extraAlarm4', 'B'), ('extraAlarm5', 'B'), ('extraAlarm6', 'B'),
               ('extraAlarm7', 'B'), ('extraAlarm8', 'B'), ('soilLeafAlarm1', 'B'),
               ('soilLeafAlarm2', 'B'), ('soilLeafAlarm3', 'B'), ('soilLeafAlarm4', 'B'),
               ('txBatteryStatus', 'B'), ('consBatteryVoltage', 'H'), ('forecastIcon', 'B'),
               ('forecastRule', 'B'), ('sunrise', 'H'), ('sunset', 'H')]

# Extract the types and struct.Struct formats for the LOOP packets:
loop_types, fmt = zip(*loop_format)
loop_fmt = struct.Struct('<' + ''.join(fmt))

# ===============================================================================
#                              ARCHIVE packets
# ===============================================================================

rec_format_A = [('date_stamp', 'H'), ('time_stamp', 'H'), ('outTemp', 'h'),
                ('highOutTemp', 'h'), ('lowOutTemp', 'h'), ('rain', 'H'),
                ('rainRate', 'H'), ('barometer', 'H'), ('radiation', 'H'),
                ('number_of_wind_samples', 'H'), ('inTemp', 'h'), ('inHumidity', 'B'),
                ('outHumidity', 'B'), ('windSpeed', 'B'), ('windGust', 'B'),
                ('windGustDir', 'B'), ('windDir', 'B'), ('UV', 'B'),
                ('ET', 'B'), ('invalid_data', 'B'), ('soilMoist1', 'B'),
                ('soilMoist2', 'B'), ('soilMoist3', 'B'), ('soilMoist4', 'B'),
                ('soilTemp1', 'B'), ('soilTemp2', 'B'), ('soilTemp3', 'B'),
                ('soilTemp4', 'B'), ('leafWet1', 'B'), ('leafWet2', 'B'),
                ('leafWet3', 'B'), ('leafWet4', 'B'), ('extraTemp1', 'B'),
                ('extraTemp2', 'B'), ('extraHumid1', 'B'), ('extraHumid2', 'B'),
                ('readClosed', 'H'), ('readOpened', 'H'), ('unused', 'B')]

rec_format_B = [('date_stamp', 'H'), ('time_stamp', 'H'), ('outTemp', 'h'),
                ('highOutTemp', 'h'), ('lowOutTemp', 'h'), ('rain', 'H'),
                ('rainRate', 'H'), ('barometer', 'H'), ('radiation', 'H'),
                ('number_of_wind_samples', 'H'), ('inTemp', 'h'), ('inHumidity', 'B'),
                ('outHumidity', 'B'), ('windSpeed', 'B'), ('windGust', 'B'),
                ('windGustDir', 'B'), ('windDir', 'B'), ('UV', 'B'),
                ('ET', 'B'), ('highRadiation', 'H'), ('highUV', 'B'),
                ('forecastRule', 'B'), ('leafTemp1', 'B'), ('leafTemp2', 'B'),
                ('leafWet1', 'B'), ('leafWet2', 'B'), ('soilTemp1', 'B'),
                ('soilTemp2', 'B'), ('soilTemp3', 'B'), ('soilTemp4', 'B'),
                ('download_record_type', 'B'), ('extraHumid1', 'B'), ('extraHumid2', 'B'),
                ('extraTemp1', 'B'), ('extraTemp2', 'B'), ('extraTemp3', 'B'),
                ('soilMoist1', 'B'), ('soilMoist2', 'B'), ('soilMoist3', 'B'),
                ('soilMoist4', 'B')]

# Extract the types and struct.Struct formats for the two types of archive packets:
rec_types_A, fmt_A = zip(*rec_format_A)
rec_types_B, fmt_B = zip(*rec_format_B)
rec_fmt_A = struct.Struct('<' + ''.join(fmt_A))
rec_fmt_B = struct.Struct('<' + ''.join(fmt_B))

# ===============================================================================
#                      LOOP Map
# ===============================================================================
# This dictionary maps a type key to a function. The function should be able to
# decode a sensor value held in the LOOP packet in the internal, Davis form into US
# units and return it.
_loop_map = {'barometricTrend': _null,
             'barometer': _val1000Zero,
             'inTemp': _big_val10,
             'inHumidity': _little_val,
             'outTemp': _big_val10,
             'windSpeed': _little_val,
             'windSpeed10': _little_val,
             'windDir': _big_val,
             'extraTemp1': _little_temp,
             'extraTemp2': _little_temp,
             'extraTemp3': _little_temp,
             'extraTemp4': _little_temp,
             'extraTemp5': _little_temp,
             'extraTemp6': _little_temp,
             'extraTemp7': _little_temp,
             'soilTemp1': _little_temp,
             'soilTemp2': _little_temp,
             'soilTemp3': _little_temp,
             'soilTemp4': _little_temp,
             'leafTemp1': _little_temp,
             'leafTemp2': _little_temp,
             'leafTemp3': _little_temp,
             'leafTemp4': _little_temp,
             'outHumidity': _little_val,
             'extraHumid1': _little_val,
             'extraHumid2': _little_val,
             'extraHumid3': _little_val,
             'extraHumid4': _little_val,
             'extraHumid5': _little_val,
             'extraHumid6': _little_val,
             'extraHumid7': _little_val,
             'rainRate': _big_val100,
             'UV': _little_val10,
             'radiation': _big_val,
             'stormRain': _val100,
             'stormStart': _loop_date,
             'dayRain': _val100,
             'monthRain': _val100,
             'yearRain': _val100,
             'dayET': _val1000,
             'monthET': _val100,
             'yearET': _val100,
             'soilMoist1': _little_val,
             'soilMoist2': _little_val,
             'soilMoist3': _little_val,
             'soilMoist4': _little_val,
             'leafWet1': _little_val,
             'leafWet2': _little_val,
             'leafWet3': _little_val,
             'leafWet4': _little_val,
             'insideAlarm': _null,
             'rainAlarm': _null,
             'outsideAlarm1': _null,
             'outsideAlarm2': _null,
             'extraAlarm1': _null,
             'extraAlarm2': _null,
             'extraAlarm3': _null,
             'extraAlarm4': _null,
             'extraAlarm5': _null,
             'extraAlarm6': _null,
             'extraAlarm7': _null,
             'extraAlarm8': _null,
             'soilLeafAlarm1': _null,
             'soilLeafAlarm2': _null,
             'soilLeafAlarm3': _null,
             'soilLeafAlarm4': _null,
             'txBatteryStatus': _null_int,
             'consBatteryVoltage': lambda v: float((v * 300) >> 9) / 100.0,
             'forecastIcon': _null,
             'forecastRule': _null,
             'sunrise': _stime,
             'sunset': _stime}

# ===============================================================================
#                      ARCHIVE Map
# ===============================================================================
# This dictionary maps a type key to a function. The function should be able to
# decode a sensor value held in the archive packet in the internal, Davis form into US
# units and return it.
_archive_map = {'barometer': _val1000Zero,
                'inTemp': _big_val10,
                'outTemp': _big_val10,
                'highOutTemp': lambda v: float(v / 10.0) if v != -32768 else None,
                'lowOutTemp': _big_val10,
                'inHumidity': _little_val,
                'outHumidity': _little_val,
                'windSpeed': _little_val,
                'windDir': _windDir,
                'windGust': _null_float,
                'windGustDir': _windDir,
                'rain': _val100,
                'rainRate': _val100,
                'ET': _val1000,
                'radiation': _big_val,
                'highRadiation': _big_val,
                'UV': _little_val10,
                'highUV': _little_val10,
                'extraTemp1': _little_temp,
                'extraTemp2': _little_temp,
                'extraTemp3': _little_temp,
                'soilTemp1': _little_temp,
                'soilTemp2': _little_temp,
                'soilTemp3': _little_temp,
                'soilTemp4': _little_temp,
                'leafTemp1': _little_temp,
                'leafTemp2': _little_temp,
                'extraHumid1': _little_val,
                'extraHumid2': _little_val,
                'soilMoist1': _little_val,
                'soilMoist2': _little_val,
                'soilMoist3': _little_val,
                'soilMoist4': _little_val,
                'leafWet1': _little_val,
                'leafWet2': _little_val,
                'leafWet3': _little_val,
                'leafWet4': _little_val,
                'forecastRule': _null,
                'readClosed': _null,
                'readOpened': _null}

# ===============================================================================
#                      Forecast Rules
# ===============================================================================
forecastRules = ["Mostly clear and cooler.",
                 "Mostly clear with little temperature change.",
                 "Mostly clear for 12 hours with little temperature change.",
                 "Mostly clear for 12 to 24 hours and cooler.",
                 "Mostly clear with little temperature change.",
                 "Partly cloudy and cooler.",
                 "Partly cloudy with little temperature change.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear and warmer.",
                 "Partly cloudy with little temperature change.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 24 to 48 hours.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds with little temperature change. Precipitation possible within 24 hours.",
                 "Mostly clear with little temperature change.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds with little temperature change. Precipitation possible within 12 hours.",
                 "Mostly clear with little temperature change.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 24 hours.",
                 "Mostly clear and warmer. Increasing winds.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 hours. Increasing winds.",
                 "Mostly clear and warmer. Increasing winds.",
                 "Increasing clouds and warmer.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 hours. Increasing winds.",
                 "Mostly clear and warmer. Increasing winds.",
                 "Increasing clouds and warmer.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 hours. Increasing winds.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly clear and warmer. Precipitation possible within 48 hours.",
                 "Mostly clear and warmer.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds with little temperature change. Precipitation possible within 24 to 48 hours.",
                 "Increasing clouds with little temperature change.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 to 24 hours.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 to 24 hours. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 to 24 hours. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 6 to 12 hours.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 6 to 12 hours. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 to 24 hours. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation possible within 12 hours.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and warmer. Precipitation likley.",
                 "Clearing and cooler. Precipitation ending within 6 hours.",
                 "Partly cloudy with little temperature change.",
                 "Clearing and cooler. Precipitation ending within 6 hours.",
                 "Mostly clear with little temperature change.",
                 "Clearing and cooler. Precipitation ending within 6 hours.",
                 "Partly cloudy and cooler.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear and cooler.",
                 "Clearing and cooler. Precipitation ending within 6 hours.",
                 "Mostly clear with little temperature change.",
                 "Clearing and cooler. Precipitation ending within 6 hours.",
                 "Mostly clear and cooler.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds with little temperature change. Precipitation possible within 24 hours.",
                 "Mostly cloudy and cooler. Precipitation continuing.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation likely.",
                 "Mostly cloudy with little temperature change. Precipitation continuing.",
                 "Mostly cloudy with little temperature change. Precipitation likely.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible and windy within 6 hours.",
                 "Increasing clouds with little temperature change. Precipitation possible and windy within 6 hours.",
                 "Mostly cloudy and cooler. Precipitation continuing. Increasing winds.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation likely. Increasing winds.",
                 "Mostly cloudy with little temperature change. Precipitation continuing. Increasing winds.",
                 "Mostly cloudy with little temperature change. Precipitation likely. Increasing winds.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible within 12 to 24 hours possible wind shift to "
                 "the W NW or N.",
                 "Increasing clouds with little temperature change. Precipitation possible within 12 to 24 hours "
                 "possible wind shift to the W NW or N.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible within 6 hours possible wind shift to the W NW "
                 "or N.",
                 "Increasing clouds with little temperature change. Precipitation possible within 6 hours possible "
                 "wind shift to the W NW or N.",
                 "Mostly cloudy and cooler. Precipitation ending within 12 hours possible wind shift to the W NW or N.",
                 "Mostly cloudy and cooler. Possible wind shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Precipitation ending within 12 hours possible wind "
                 "shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Possible wind shift to the W NW or N.",
                 "Mostly cloudy and cooler. Precipitation ending within 12 hours possible wind shift to the W NW or N.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation possible within 24 hours possible wind shift to the W NW or "
                 "N.",
                 "Mostly cloudy with little temperature change. Precipitation ending within 12 hours possible wind "
                 "shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Precipitation possible within 24 hours possible wind "
                 "shift to the W NW or N.",
                 "Clearing cooler and windy. Precipitation ending within 6 hours.",
                 "Clearing cooler and windy.",
                 "Mostly cloudy and cooler. Precipitation ending within 6 hours. Windy with possible wind shift to the "
                 "W NW or N.",
                 "Mostly cloudy and cooler. Windy with possible wind shift to the W NW or N.",
                 "Clearing cooler and windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy with little temperature change. Precipitation possible within 12 hours. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible within 12 hours possibly heavy at times. Windy.",
                 "Mostly cloudy and cooler. Precipitation ending within 6 hours. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation possible within 12 hours. Windy.",
                 "Mostly cloudy and cooler. Precipitation ending in 12 to 24 hours.",
                 "Mostly cloudy and cooler.",
                 "Mostly cloudy and cooler. Precipitation continuing possible heavy at times. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation possible within 6 to 12 hours. Windy.",
                 "Mostly cloudy with little temperature change. Precipitation continuing possibly heavy at times. "
                 "Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy with little temperature change. Precipitation possible within 6 to 12 hours. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds with little temperature change. Precipitation possible within 12 hours possibly "
                 "heavy at times. Windy.",
                 "Mostly cloudy and cooler. Windy.",
                 "Mostly cloudy and cooler. Precipitation continuing possibly heavy at times. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation likely possibly heavy at times. Windy.",
                 "Mostly cloudy with little temperature change. Precipitation continuing possibly heavy at times. "
                 "Windy.",
                 "Mostly cloudy with little temperature change. Precipitation likely possibly heavy at times. Windy.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible within 6 hours. Windy.",
                 "Increasing clouds with little temperature change. Precipitation possible within 6 hours. Windy",
                 "Increasing clouds and cooler. Precipitation continuing. Windy with possible wind shift to the W NW "
                 "or N.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation likely. Windy with possible wind shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Precipitation continuing. Windy with possible wind "
                 "shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Precipitation likely. Windy with possible wind shift "
                 "to the W NW or N.",
                 "Increasing clouds and cooler. Precipitation possible within 6 hours. Windy with possible wind shift "
                 "to the W NW or N.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible within 6 hours possible wind shift to the W NW "
                 "or N.",
                 "Increasing clouds with little temperature change. Precipitation possible within 6 hours. Windy with "
                 "possible wind shift to the W NW or N.",
                 "Increasing clouds with little temperature change. Precipitation possible within 6 hours possible "
                 "wind shift to the W NW or N.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible within 6 hours. Windy with possible wind shift "
                 "to the W NW or N.",
                 "Increasing clouds with little temperature change. Precipitation possible within 6 hours. Windy with "
                 "possible wind shift to the W NW or N.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Increasing clouds and cooler. Precipitation possible within 12 to 24 hours. Windy with possible wind "
                 "shift to the W NW or N.",
                 "Increasing clouds with little temperature change. Precipitation possible within 12 to 24 hours. "
                 "Windy with possible wind shift to the W NW or N.",
                 "Mostly cloudy and cooler. Precipitation possibly heavy at times and ending within 12 hours. Windy "
                 "with possible wind shift to the W NW or N.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation possible within 6 to 12 hours possibly heavy at times. Windy "
                 "with possible wind shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Precipitation ending within 12 hours. Windy with "
                 "possible wind shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Precipitation possible within 6 to 12 hours possibly "
                 "heavy at times. Windy with possible wind shift to the W NW or N.",
                 "Mostly cloudy and cooler. Precipitation continuing.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation likely. Windy with possible wind shift to the W NW or N.",
                 "Mostly cloudy with little temperature change. Precipitation continuing.",
                 "Mostly cloudy with little temperature change. Precipitation likely.",
                 "Partly cloudy with little temperature change.",
                 "Mostly clear with little temperature change.",
                 "Mostly cloudy and cooler. Precipitation possible within 12 hours possibly heavy at times. Windy.",
                 "Not enough data for forecast.",
                 "Mostly clear and cooler.",
                 "Mostly clear and cooler.",
                 "Mostly clear and cooler.",
                 "Forecast unknown."]
