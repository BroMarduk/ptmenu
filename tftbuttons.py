#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
import signal
import time
from functools import partial

import RPi.GPIO as GPIO

import tftmenu
from tftutility import *

logger.debug("Loading Buttons Module")


##################################################################################
# GPIO ECHO PORT CONSTANTS
##################################################################################
GPIO_ECHO_BACKLIGHT     = 508
GPIO_ECHO_BACKLIGHT_ALT = 252


##################################################################################
# ADAFRUIT CONFIGURATION CONSTANTS
##################################################################################
ADAFRUIT_CONF_FILE = "/etc/modprobe.d/adafruit.conf"
ADAFRUIT_CONF_GPIO = "options rpi_power_switch gpio_pin="


##################################################################################
# DEFAULT CONSTANTS
##################################################################################
DEFAULT_BACKLIGHT_STEPS = 4
DEFAULT_POWER_GPIO      = 0
DEFAULT_PI_BATTERY_GPIO = 0

##################################################################################
# GPIO PORT CONSTANTS
##################################################################################
GPIO_PWM_BACKLIGHT      = 18


##################################################################################
# BACKLIGHT STATE CONSTANTS
##################################################################################
GPIO_BACKLIGHT_OFF      = 0
GPIO_BACKLIGHT_ON       = 1
GPIO_BACKLIGHT_HIGH     = 1023


##################################################################################
# GPIO COMMAND CONSTANTS
##################################################################################
GPIO_SUDO_SHELL = ['sudo', 'sh', '-c']


##################################################################################
# GPIO BACKLIGHT COMMAND CONSTANTS
##################################################################################
GPIO_BACKLIGHT_ECHO_PATH = "/sys/class/gpio/"
GPIO_BACKLIGHT_ECHO_OUTPUT = "echo 'out' > {0}gpio$pin/direction".format(GPIO_BACKLIGHT_ECHO_PATH)
GPIO_BACKLIGHT_ECHO_LINK = "echo {{0}} > {0}export".format(GPIO_BACKLIGHT_ECHO_PATH)
GPIO_BACKLIGHT_ECHO_SET = "echo '{{0}}' > {0}gpio{{1}}/value".format(GPIO_BACKLIGHT_ECHO_PATH)
GPIO_BACKLIGHT_STMPE_PATH = "/sys/class/backlight/soc:backlight"
GPIO_BACKLIGHT_STMPE_COMMAND = "echo '{0}' > /sys/class/backlight/soc\:backlight/brightness"
GPIO_BACKLIGHT_PWM_MODE        = "pwm"
GPIO_BACKLIGHT_PWM_BINARY_MODE = "out"
GPIO_BACKLIGHT_PWM_FREQUENCY   = "1000"
GPIO_BACKLIGHT_PWM_MODE_SET    = "gpio -g mode {0} {1}"
GPIO_BACKLIGHT_PWM_SET         = "gpio -g pwm {0} {1}"
GPIO_BACKLIGHT_PWM_BINARY_SET  = "gpio -g write {0} {1}"
GPIO_BACKLIGHT_PWMC_SET        = "gpio pwmc {0}"
GPIO_BACKLIGHT_CHANGE_STEPS_MIN = 2
GPIO_BACKLIGHT_CHANGE_STEPS_MAX = GPIO_BACKLIGHT_HIGH


##################################################################################
# TIMER CLASS
##################################################################################
class Timer:
    __timeout      = 0
    __alarmed      = False
    __triggered    = False
    __abort        = False
    __ignore_reset = False

    ##################################################################################
    # TIMER ALARM METHOD
    ##################################################################################
    # Method called from a system Alarm signal.  When an alarm occurs, the __triggered
    # variable is set to True and can be detected in the is_expired method.
    ##################################################################################
    @classmethod
    def alarm(cls, signum, frame):
        logger.debug("Alarm Signal Received.  Signum: {0}, Frame: {1}".format(signum, frame))
        cls.__triggered = True
        cls.__ignore_reset = False
        signal.alarm(0)

    ##################################################################################
    # TIMER RESET METHOD
    ##################################################################################
    # Method to reset the Alarm signal timer
    ##################################################################################
    @classmethod
    def reset(cls):
        if not cls.__ignore_reset:
            logger.debug("Timer reset")
            cls.__triggered = False
            signal.alarm(0)
            signal.alarm(cls.__timeout)
        else:
            logger.debug("Timer reset ignored.")

    ##################################################################################
    # TIMER TIMEOUT METHOD
    ##################################################################################
    # Method that initially sets the Alarm signal callback.  The ignore_reset
    # parameter can be set to True to ignore reset signals.
    ##################################################################################
    @classmethod
    def timeout(cls, timeout, ignore_reset=False):
        logger.debug("Timeout set.  Timeout: {0}, Ignore Reset: {1}".format(timeout, ignore_reset))
        cls.__timeout = timeout
        if not cls.__alarmed:
            signal.signal(signal.SIGALRM, Timer.alarm)
            cls.__alarmed = True
            logger.debug("Alarm Signal Initialized")
        cls.reset()
        cls.__ignore_reset = ignore_reset

    ##################################################################################
    # TIMER IS_EXPIRED METHOD
    ##################################################################################
    # Method to detect if a timer alarm has occurred.
    ##################################################################################
    @classmethod
    def is_expired(cls):
        if cls.__timeout == 0 or not cls.__triggered:
            return False
        else:
            cls.reset()
            return True


##################################################################################
# BACKLIGHT CLASS
##################################################################################
# Class to manage the backlight of the PiTft.  Handles dimming, brightening,
# sleeping and waking of the device.
##################################################################################
class Backlight:
    method       = 0
    steps        = None
    restore_last = False
    default      = None
    callback     = None
    state       = 0
    last_state  = 0
    change      = 0.0
    initialized = False

    ##################################################################################
    # BACKLIGHT INITIALIZE METHOD
    ##################################################################################
    # Method for initializing the Backlight class.  Checks if already initialized and
    # set to initialized if not.  Set the backlight options that are passed in then
    # set the backlight method and tweak options based on the backlight method.
    ##################################################################################
    @classmethod
    def initialize(cls, method=None, steps=None, restore_last=False, default=None, callback=None):
        if cls.initialized:
            logger.error("Backlight Class has already been initialized.")
            raise AlreadyInitializedException("Backlight Class has already been initialized.")
        cls.initialized = True
        # Set Class Variables
        cls.method    = method
        cls.restore_last  = restore_last
        cls.steps     = steps
        cls.default   = default
        cls.callback  = merge(Timer.reset, callback)
        if cls.method is None:
            cls.method = BacklightMethod.NoBacklight
        if cls.steps is None:
            cls.steps = DEFAULT_BACKLIGHT_STEPS
        if cls.default is None:
            cls.default = DEFAULT_BACKLIGHT_STEPS
        if cls.default > cls.steps:
            cls.default = cls.steps
        subprocess.call(GPIO_BACKLIGHT_PWMC_SET.format(GPIO_BACKLIGHT_PWM_FREQUENCY).split())
        if cls.method != BacklightMethod.NoBacklight:
            # If using PWM non-binary method, we need to get exact backlight values
            if cls.method == BacklightMethod.Pwm:
                # Determine the number of steps for the backlight_up/BacklightDown buttons
                if cls.steps < GPIO_BACKLIGHT_CHANGE_STEPS_MIN:
                    # Always need at least two steps (on and off)
                    cls.steps = GPIO_BACKLIGHT_CHANGE_STEPS_MIN
                if cls.steps > GPIO_BACKLIGHT_CHANGE_STEPS_MAX:
                    # Maximum amount of steps is the maximum number of backlight settings
                    cls.steps = GPIO_BACKLIGHT_CHANGE_STEPS_MAX
                    # Determine the amount to change the backlight at each step
                cls.change = GPIO_BACKLIGHT_CHANGE_STEPS_MAX / (float(cls.steps) - 1.0)
                cls.default = int((float(cls.default) - 1) * cls.change)
                # Make sure default is in the proper range, if not set to off (too low) or (too) high
                if cls.default < GPIO_BACKLIGHT_OFF:
                    cls.default = GPIO_BACKLIGHT_OFF
                if cls.default > GPIO_BACKLIGHT_HIGH:
                    cls.default = GPIO_BACKLIGHT_HIGH
                initial_value = cls.default
            # All other methods are binary and are either on or off
            else:
                cls.steps = GPIO_BACKLIGHT_CHANGE_STEPS_MIN
                cls.change = GPIO_BACKLIGHT_HIGH
                # The default backlight can be set to either off or high when binary.
                if cls.default == GPIO_BACKLIGHT_OFF:
                    initial_value = GPIO_BACKLIGHT_OFF
                else:
                    cls.default   = GPIO_BACKLIGHT_HIGH
                    initial_value = GPIO_BACKLIGHT_ON
            # Set backlight current and last states
            cls.state = cls.default
            if cls.default == GPIO_BACKLIGHT_OFF:
                cls.last_state = GPIO_BACKLIGHT_HIGH
            else:
                cls.last_state = cls.default
            # Depending on whether the screen uses echo to set backlight.  Note on the GPIO
            # screens, the jumper enabling GPIO 18 to control the backlight must be soldered to
            # control the backlight.
            if cls.method == BacklightMethod.Pwm:
                # If STMPE path exists, make sure backlight is on.
                if os.path.isdir(GPIO_BACKLIGHT_STMPE_PATH):
                    subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_STMPE_COMMAND.format(GPIO_BACKLIGHT_OFF)])
                # Set PWM Mode on GPIO 18, which controls the backlight and set the brightness
                # to default if present, or maximum brightness if no default
                subprocess.call(GPIO_BACKLIGHT_PWM_MODE_SET.format(GPIO_PWM_BACKLIGHT, GPIO_BACKLIGHT_PWM_MODE).split())
                subprocess.call(GPIO_BACKLIGHT_PWMC_SET.format(GPIO_BACKLIGHT_PWM_FREQUENCY).split())
                subprocess.call(GPIO_BACKLIGHT_PWM_SET.format(GPIO_PWM_BACKLIGHT, initial_value).split())
            elif cls.method == BacklightMethod.PwmBinary:
                # If STMPE path exists, make sure backlight is on.
                if os.path.isdir(GPIO_BACKLIGHT_STMPE_PATH):
                    subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_STMPE_COMMAND.format(GPIO_BACKLIGHT_OFF)])
                subprocess.call(GPIO_BACKLIGHT_PWM_MODE_SET.format(GPIO_PWM_BACKLIGHT,
                                                                   GPIO_BACKLIGHT_PWM_BINARY_MODE).split())
                # Set PWM Mode on GPIO 18, which controls the backlight and set the brightness
                # to default if present, or maximum brightness if no default
                subprocess.call(GPIO_BACKLIGHT_PWM_BINARY_SET.format(GPIO_PWM_BACKLIGHT, initial_value).split())
            elif cls.method == BacklightMethod.Stmpe:
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_STMPE_COMMAND.format(initial_value)])
            elif (cls.method == BacklightMethod.Echo) or (cls.method == BacklightMethod.Echo252):
                # Create the device link to the GPIO 508 pin.  On real old kernels, this is 252 (in case
                # someone is still running a pre-2014 kernel) and can be changed by setting the
                # method to BacklightMethod.Echo252
                backlight_pin = GPIO_ECHO_BACKLIGHT
                if cls.method == BacklightMethod.Echo252:
                    backlight_pin = GPIO_ECHO_BACKLIGHT_ALT
                # ECHO GPIO is binary (ON/OFF) so change is always the maximum brightness
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_ECHO_LINK.format(backlight_pin)])
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_ECHO_OUTPUT.format(backlight_pin)])
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_ECHO_SET.format(initial_value, backlight_pin)])
            else:
                logger.warning("Unknown Backlight Method.  Setting backlight method to No Backlight.  Method: {0}"
                               .format(cls.method))
                cls.method = BacklightMethod.NoBacklight
        send_wake_command()
        return True

    ##################################################################################
    # BACKLIGHT IS_SCREEN_SLEEPING METHOD
    ##################################################################################
    # Determines if the backlight is in a sleeping state that is maintained by the
    # class.
    ##################################################################################
    @classmethod
    def is_screen_sleeping(cls):
        if cls.method == BacklightMethod.NoBacklight:
            logger.error("Attempt to detect sleep with a Backlight method of BacklightMethod.NoBacklight.")
            raise BacklightNotEnabled("Backlight method set to BacklightMethod.NoBacklight.  "
                                      "Unable to determine sleep state.")
        return cls.state == GPIO_BACKLIGHT_OFF

    ##################################################################################
    # BACKLIGHT SET_BACKLIGHT METHOD
    ##################################################################################
    # Method that sets the backlight using the code required by the backlight method.
    ##################################################################################
    @classmethod
    def set_backlight(cls, state):
        if not cls.initialized:
            return
        if cls.method == BacklightMethod.NoBacklight:
            logger.error("Attempt to set backlight with a Backlight method of BacklightMethod.NoBacklight.")
            raise BacklightNotEnabled("Backlight method set to BacklightMethod.NoBacklight.  Unable to set backlight.")
        if state == cls.state:
            return
        time.sleep(Times.SleepShort)
        if cls.method == BacklightMethod.Pwm:
            logger.debug("Setting backlight to state {0} from {1} using PWM".format(state, cls.state))
            if state == GPIO_BACKLIGHT_OFF:
                subprocess.call(GPIO_BACKLIGHT_PWM_SET.format(GPIO_PWM_BACKLIGHT, GPIO_BACKLIGHT_OFF).split())
                cls.state = GPIO_BACKLIGHT_OFF
            else:
                subprocess.call(GPIO_BACKLIGHT_PWM_SET.format(GPIO_PWM_BACKLIGHT, state).split())
                cls.state = state
                cls.last_state = state
        elif cls.method == BacklightMethod.PwmBinary:
            logger.debug("Setting backlight to state {0} using PWM Binary Mode".format(state, cls.state))
            if state == GPIO_BACKLIGHT_OFF:
                subprocess.call(GPIO_BACKLIGHT_PWM_BINARY_SET.format(GPIO_PWM_BACKLIGHT, GPIO_BACKLIGHT_OFF).split())
                cls.state = GPIO_BACKLIGHT_OFF
            else:
                subprocess.call(GPIO_BACKLIGHT_PWM_BINARY_SET.format(GPIO_PWM_BACKLIGHT, GPIO_BACKLIGHT_ON).split())
                cls.state = GPIO_BACKLIGHT_HIGH
                cls.last_state = GPIO_BACKLIGHT_HIGH
        elif cls.method == BacklightMethod.Stmpe:
            logger.debug("Setting backlight to state {0} using STMPE".format(state, cls.state))
            if state == GPIO_BACKLIGHT_OFF:
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_STMPE_COMMAND.format(GPIO_BACKLIGHT_OFF)])
                cls.state = GPIO_BACKLIGHT_OFF
            else:
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_STMPE_COMMAND.format(GPIO_BACKLIGHT_ON)])
                cls.state = GPIO_BACKLIGHT_HIGH
                cls.last_state = GPIO_BACKLIGHT_HIGH
        elif (cls.method == BacklightMethod.Echo) or (cls.method == BacklightMethod.Echo252):
            logger.debug("Setting backlight to state {0} using Echo".format(state, cls.state))
            backlight_pin = GPIO_ECHO_BACKLIGHT
            if cls.method == BacklightMethod.Echo252:
                backlight_pin = GPIO_ECHO_BACKLIGHT_ALT
            if state == GPIO_BACKLIGHT_OFF:
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_ECHO_SET.format(backlight_pin, GPIO_BACKLIGHT_OFF)])
                cls.state = GPIO_BACKLIGHT_OFF
            else:
                subprocess.call(GPIO_SUDO_SHELL + [GPIO_BACKLIGHT_ECHO_SET.format(backlight_pin, GPIO_BACKLIGHT_ON)])
                cls.state = GPIO_BACKLIGHT_HIGH
                cls.last_state = GPIO_BACKLIGHT_HIGH
        else:
            logger.warning("Unable to set backlight.  Unknown Backlight Method: {0}".format(cls.method))

    ##################################################################################
    # BACKLIGHT BACKLIGHT_UP METHOD
    ##################################################################################
    # Method to increase the brightness of the backlight by the amount in the
    # backlight steps
    ##################################################################################
    @classmethod
    def backlight_up(cls, button=None):
        logger.debug("Method backlight_up executed with button: {0} ".format(button if button is not None else "0"))
        if cls.method == BacklightMethod.NoBacklight:
            logger.error("Attempt to set backlight up with a Backlight method of BacklightMethod.NoBacklight.")
            raise BacklightNotEnabled("Backlight method set to BacklightMethod.NoBacklight.  "
                                      "Unable to adjust backlight up.")
        if Backlight.is_screen_sleeping():
            send_wake_command()
        if cls.state == GPIO_BACKLIGHT_HIGH:
            new_state = GPIO_BACKLIGHT_OFF
        else:
            new_state = int(cls.state + cls.change)
            if new_state > GPIO_BACKLIGHT_HIGH:
                new_state = GPIO_BACKLIGHT_HIGH
        Backlight.set_backlight(new_state)
        cls.call_button_press()

    ##################################################################################
    # BACKLIGHT BACKLIGHT_DOWN METHOD
    ##################################################################################
    # Method to decrease the brightness of the backlight by the amount in the
    # backlight steps
    ##################################################################################
    @classmethod
    def backlight_down(cls, button=None):
        logger.debug("Method backlight_down executed with button: {0} ".format(button if button is not None else "0"))
        if cls.method == BacklightMethod.NoBacklight:
            logger.error("Attempt to set backlight down with a Backlight method of BacklightMethod.NoBacklight.")
            raise BacklightNotEnabled("Backlight method set to BacklightMethod.NoBacklight.  "
                                      "Unable to adjust backlight down.")
        if Backlight.is_screen_sleeping():
            send_wake_command()
        if cls.state == GPIO_BACKLIGHT_OFF:
            new_state = GPIO_BACKLIGHT_HIGH
        else:
            new_state = int(cls.state - cls.change)
            if new_state < GPIO_BACKLIGHT_OFF:
                new_state = GPIO_BACKLIGHT_OFF
        Backlight.set_backlight(new_state)
        cls.call_button_press()

    ##################################################################################
    # BACKLIGHT SCREEN_WAKE METHOD
    ##################################################################################
    # Send the screen wake command as it has nothing to do with the backlight but
    # allows the menu to wake up from the system screen sleep if enabled.  This is
    # done regardless of any backlight manipulation.
    ##################################################################################
    @classmethod
    def screen_wake(cls, button=None):
        logger.debug("Method screen_wake executed with button: {0} ".format(button if button is not None else "0"))
        send_wake_command()
        if cls.method != BacklightMethod.NoBacklight:
            # Check if we should restore the backlight to the setting it was set to
            # before it sleeping.  If that setting was Off, then go back to full
            # brightness.
            if cls.restore_last:
                if cls.last_state == GPIO_BACKLIGHT_OFF:
                    cls.set_backlight(GPIO_BACKLIGHT_HIGH)
                else:
                    cls.set_backlight(cls.last_state)
            else:
                if cls.state != cls.default:
                    # Set backlight to high/on if it is not already
                    cls.set_backlight(cls.default)
        cls.call_button_press()

    ##################################################################################
    # BACKLIGHT SCREEN_SLEEP METHOD
    ##################################################################################
    # Sends the command to the screen to sleep the screen
    ##################################################################################
    @classmethod
    def screen_sleep(cls, button=None):
        logger.debug("Method screen_sleep executed with button: {0} ".format(button if button is not None else "0"))
        if cls.method == BacklightMethod.NoBacklight:
            logger.error("Attempt to sleep screen up with a Backlight method of BacklightMethod.NoBacklight.")
            raise BacklightNotEnabled("Backlight method set to BacklightMethod.NoBacklight.  Unable to sleep screen.")
        # Set backlight to off if it is not already
        if not cls.is_screen_sleeping():
            cls.set_backlight(GPIO_BACKLIGHT_OFF)
        cls.call_button_press()

    ##################################################################################
    # BACKLIGHT SCREEN_TOGGLE METHOD
    ##################################################################################
    # Sends the command to the screen to sleep the screen if it awake or wake the
    # screen if it is sleeping.
    ##################################################################################
    @classmethod
    def screen_toggle(cls, button=None):
        logger.debug("Method screen_toggle executed with button: {0} ".format(button if button is not None else "0"))
        if cls.method == BacklightMethod.NoBacklight:
            logger.error("Attempt to toggle screen up with a Backlight method of BacklightMethod.NoBacklight.")
            raise BacklightNotEnabled("Backlight method set to BacklightMethod.NoBacklight.  Unable to toggle screen.")
        # Set backlight to off if it is not already
        if cls.is_screen_sleeping():
            cls.screen_wake(None)
        else:
            cls.screen_sleep(None)
        cls.call_button_press()

    ##################################################################################
    # BACKLIGHT CALL_BUTTON_PRESS METHOD
    ##################################################################################
    # Classmethod that calls any callbacks in the list of callbacks when a button is
    # pressed.  Timer.reset is added by default when creating the Button class and is
    # used internally.  Additional handlers can be implemented by adding custom
    # callback functions.
    ##################################################################################
    @classmethod
    def call_button_press(cls):
        if cls.callback is not None:
            for function in cls.callback:
                logger.debug("Calling button press function {0}".format(function))
                function()


##################################################################################
# GPIO ACTION CLASS
##################################################################################
# Class that holds the actions for a GPIO button press, including and additional
# data or data for drawing a new display (render_data).
##################################################################################
class GpioAction(object):
    action = None
    data = None
    render_data = None

    ##################################################################################
    # GPIO ACTION INIT METHOD
    ##################################################################################
    # Sets the GPIO Action properties to defaults.
    ##################################################################################
    def __init__(self, action=GpioButtonAction.NoAction, data=None, render_data=None):
        self.action = action
        self.data = data
        self.render_data = render_data


##################################################################################
#  GPIO BUTTONS CLASS
##################################################################################
# Class to hold the state, methods and creation of the gpio buttons.  These
# buttons can be virtual, physical (on the tft) or external (such as on a bread-
# board.
##################################################################################
class GpioButtons(object):
    tft_type         = None
    buttons          = []
    actions          = []
    power_gpio       = 0
    battery_gpio     = 0
    gpio_initialized = False
    initialized      = False

    ##################################################################################
    # BUTTONS GPIO_BUTTON METHOD
    ##################################################################################
    # Method called by the GPIO.add_event_detect.   The button contains the sequential
    # id of the button, starting at 0, the actions parameter contains the list of
    # actions to be executed by the button press and channel contains the GPIO id of
    # the pressed button.
    ##################################################################################
    @classmethod
    def gpio_button(cls, button, actions, channel):
        if actions is not None:
            logger.debug(actions)
            if not isinstance(actions, list):
                actions = [actions]
            for function in actions:
                if function is not None and isinstance(function, GpioAction):
                    if function.action == GpioButtonAction.NoAction:
                        continue
                    elif function.action == GpioButtonAction.Display:
                        tftmenu.Displays.show(function.data, function.render_data)
                    elif function.action == GpioButtonAction.Exit:
                        tftmenu.Displays.shutdown(Shutdown.Normal)
                    elif function.action == GpioButtonAction.Reboot:
                        tftmenu.Displays.shutdown(Shutdown.Reboot)
                    elif function.action == GpioButtonAction.Shutdown:
                        tftmenu.Displays.shutdown(Shutdown.Shutdown)
                    elif function.action == GpioButtonAction.Function:
                        if function.data is not None and function.data:
                            return_val = function.data(tftmenu.Displays.current, channel)
                            if return_val is not None:
                                if isinstance(return_val, tftmenu.Display):
                                    tftmenu.Displays.show(return_val, function.render_data)
                        function.data(button, channel)
                    elif function.action == GpioButtonAction.ScreenSleep:
                        Backlight.screen_sleep(channel)
                    elif function.action == GpioButtonAction.ScreenWake:
                        Backlight.screen_wake(channel)
                    elif function.action == GpioButtonAction.ScreenToggle:
                        Backlight.screen_toggle(channel)
                    elif function.action == GpioButtonAction.BacklightDown:
                        Backlight.backlight_down(channel)
                    elif function.action == GpioButtonAction.BacklightUp:
                        Backlight.backlight_up(channel)
                    elif function.action == GpioButtonAction.Shell:
                        tftmenu.Displays.shell()
                    elif function.action == GpioButtonAction.StartX:
                        tftmenu.Displays.start_x(function.data)
                    elif function.action == GpioButtonAction.Execute:
                        run_cmd(function.data)

    ##################################################################################
    # BUTTONS INIT METHOD
    ##################################################################################
    # Method that sets the initial properties of the GpioButtons class.  These
    # properties include the GPIOs for power on/of, battery monitoring and buttons as
    # well as the associated actions.
    ##################################################################################
    def __init__(self, tft_type, buttons=None, actions=None,  backlight_method=BacklightMethod.NoBacklight,
                 backlight_steps=None, backlight_default=None, backlight_restore_last=False, backlight_auto=False,
                 button_callback=None, power_gpio=None, battery_gpio=None):
        if GpioButtons.gpio_initialized:
            logger.error("TftButtons Class has already been initialized.")
            raise AlreadyInitializedException("TftButtons Class has already been initialized.")
        GpioButtons.initialized = True
        self.tft_type     = tft_type
        self.buttons = array_single_none(buttons, no_coerce_none=True)
        self.actions = array_single_none(actions, no_coerce_none=True)
        if power_gpio is None:
            self.power_gpio = DEFAULT_POWER_GPIO
        else:
            self.power_gpio = power_gpio
        if battery_gpio is None:
            self.battery_gpio = DEFAULT_PI_BATTERY_GPIO
        else:
            self.battery_gpio = battery_gpio
        # if using a capacitive TFT, only PWM is supported for backlight control.  If another method is
        # set, default to BacklightMethod.PwmBinary which is similar to the other ones.
        if (tft_type == DISP28C or tft_type == DISP28CP) and \
                (backlight_method != BacklightMethod.Pwm and backlight_method != BacklightMethod.PwmBinary and
                 backlight_method != BacklightMethod.NoBacklight and backlight_method is not None):
            backlight_method = BacklightMethod.PwmBinary
        Backlight.initialize(backlight_method, backlight_steps, backlight_restore_last, backlight_default,
                             button_callback)
        # Set GPIO if not passed in based on device
        if self.buttons is None and backlight_auto:
            if tft_type == DISP22NT:
                self.buttons = [17, 22, 23, 27]
            elif tft_type == DISP24R:
                self.buttons = [16, 13, 12, 6, 5]
            elif tft_type == DISP28R:
                self.buttons = [23, 22, 21, 18]
            elif tft_type == DISP28C:
                self.buttons = [23, 22, 21, 17]
            elif tft_type == DISP28RP:
                self.buttons = [17, 22, 23, 27]
            elif tft_type == DISP28CP:
                self.buttons = [17, 22, 23, 27]
            elif tft_type == DISP32RP:
                self.buttons = [22, 23, 17, 27]
            else:  # No buttons PiTft buttons for 3.5" Displays (yet)
                self.buttons = []
        else:
            self.buttons = []
        # Get GPIO used as shutdown button in Adafruit kernels, if set in the config, we can
        # get it and set it automatically.  This only works for one or two digit GPIOs and
        # setting the GPIO manually will negate any checking.
        if (self.power_gpio == DEFAULT_PI_BATTERY_GPIO) and (os.path.isfile(ADAFRUIT_CONF_FILE)):
            file_config = open(ADAFRUIT_CONF_FILE, "r").read()
            start_pos = file_config.find(ADAFRUIT_CONF_GPIO)
            if start_pos != -1:
                value_pos = start_pos + len(ADAFRUIT_CONF_GPIO)
                try:
                    value = int(file_config[value_pos:value_pos + 2].strip())
                except ValueError:
                    value = 0
                if value > 0:
                    self.power_gpio = value
        # Remove any duplicates in the GPIO list
        if self.buttons:
            self.buttons = remove_duplicates(self.buttons)
        # Remove the power_gpio button
        if self.power_gpio in self.buttons:
            self.buttons.remove(self.power_gpio)
        # Remove any bad GPIOs (those 0 or below).
        for button in self.buttons:
            if button <= 0:
                self.buttons.remove(button)
        if backlight_auto and Backlight.method != BacklightMethod.NoBacklight and not self.actions:
            # Set default actions based on the number of buttons if we are using a backlight mode and actions are not
            # passed in specifically.
            if len(self.buttons) >= 5:
                self.actions = [GpioAction(GpioButtonAction.BacklightDown),
                                GpioAction(GpioButtonAction.BacklightUp),
                                GpioAction(GpioButtonAction.ScreenWake),
                                GpioAction(GpioButtonAction.ScreenSleep),
                                GpioAction(GpioButtonAction.ScreenToggle)]
            elif len(self.buttons) == 4:
                self.actions = [GpioAction(GpioButtonAction.BacklightDown),
                                GpioAction(GpioButtonAction.BacklightUp),
                                GpioAction(GpioButtonAction.ScreenWake),
                                GpioAction(GpioButtonAction.ScreenSleep)]
            elif len(self.buttons) == 3:
                self.actions = [GpioAction(GpioButtonAction.BacklightDown),
                                GpioAction(GpioButtonAction.ScreenWake),
                                GpioAction(GpioButtonAction.ScreenSleep)]
            elif len(self.buttons) == 2:
                self.actions = [GpioAction(GpioButtonAction.BacklightDown),
                                GpioAction(GpioButtonAction.ScreenToggle)]
            elif len(self.buttons) == 1:
                self.actions = [GpioAction(GpioButtonAction.ScreenToggle)]
            else:
                self.actions = []
        # Setup GPIO for low battery indication which is useful if using a LiPo battery with a board that can
        # control a GPIO pin.
        GPIO.setmode(GPIO.BCM)
        if self.battery_gpio is not DEFAULT_PI_BATTERY_GPIO:
            GPIO.setup(self.battery_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if self.actions:
            for button in self.buttons:
                GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # Bind actions to GPIO Buttons if they exist
            action_count = 0
            for button in self.buttons:
                if action_count < len(self.actions):
                    button_actions = self.actions[action_count]
                    GPIO.add_event_detect(button, GPIO.RISING,
                                          callback=partial(GpioButtons.gpio_button, action_count, button_actions),
                                          bouncetime=Times.SwitchBounce)
                action_count += 1
            GpioButtons.gpio_initialized = True

    ##################################################################################
    # BUTTONS DEL METHOD
    ##################################################################################
    # Method to clean up upon deletion of the class.
    ##################################################################################
    def __del__(self):
        # Set the backlight back to its highest setting if any backlight manipulation
        # could have been done
        if Backlight.method != BacklightMethod.NoBacklight:
            Backlight.set_backlight(GPIO_BACKLIGHT_HIGH)
        # If any GPIO event detection was done, clean up.
        if GpioButtons.gpio_initialized:
            GPIO.cleanup()
            GpioButtons.gpio_initialized = False
        GpioButtons.initialized = False

    ##################################################################################
    # BUTTONS IS_LOW_BATTERY METHOD
    ##################################################################################
    # Method to check to see if the GPIO input used to monitor the battery is
    # indicating a low battery.
    ##################################################################################
    def is_low_battery(self):
        # No need to check if we are set to default (no battery GPIO).
        if self.battery_gpio is DEFAULT_PI_BATTERY_GPIO:
            return False
        else:
            return GPIO.input(self.battery_gpio) == GPIO.LOW
