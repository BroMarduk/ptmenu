#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
import fcntl
import sys

import pygame.display
import pygame.freetype
from pygame.locals import *

import tfttemplates
from tftbuttons import *
from tftutility import *

START_X_FILE = "/usr/bin/startx"

# Make sure application is running as root.
if not is_root():
    logger.critical("Application must be run as root (with sudo)")
    sys.exit()
# Write out file with lock to ensure only one instance of application can run
lock_file = 'tftmenu.lock'
file_open = open(lock_file, 'w')
try:
    fcntl.lockf(file_open, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    logger.critical("Only one instance of the application can run at a time.")
    sys.exit()


##################################################################################
# TFTMENUS DISPLAYS CLASS
##################################################################################
# Displays class responsible for the menu initialization and keeping track of
# current and last menus and states
##################################################################################
class Displays:
    menus = {}
    current = None
    initial = None
    last = None
    shelled = None
    started = False
    screen = None
    loop = True
    loop_mode_shelled = False
    display_type = None
    initialized = False
    splash_mute_level = None
    libsdl_version = None
    libsdl_build = None

    ##################################################################################
    # DISPLAYS SHOW METHOD
    ##################################################################################
    # Classmethod that shows any type of display by name or by object.
    ##################################################################################
    @classmethod
    def show(cls, item, data=None):
        # If item to show is already a menu, then just render and set.
        display = None
        if isinstance(item, Display):
            display = item
        else:
            if item in cls.menus:
                display = cls.menus[item]
        if display is not None:
            if cls.current is None or display is not cls.current.last:
                display.last = cls.current
                if display.is_core:
                    Displays.last = display
            display.render(data)
            cls.current = display
        else:
            logger.warning("Unable to get valid display to show.  Item: {0}, Data: {1}".format(item, data))

    ##################################################################################
    # DISPLAYS SHOW METHOD
    ##################################################################################
    # Classmethod that Shows a Splash screen enforcing any suppression flags that
    # may be set.
    ##################################################################################
    @classmethod
    def show_splash(cls, splash_type, data=None):
        if splash_type == SplashBuiltIn.Exit:
            if not cls.splash_mute_level & SplashMuteLevel.Exit:
                cls.show(SplashBuiltIn.Exit, data)
                return True
        elif splash_type == SplashBuiltIn.Info:
            if not cls.splash_mute_level & SplashMuteLevel.Info:
                cls.show(SplashBuiltIn.Info, data)
                return True
        elif splash_type == SplashBuiltIn.Warning:
            if not cls.splash_mute_level & SplashMuteLevel.Warning:
                cls.show(SplashBuiltIn.Warning, data)
                return True
        elif splash_type == SplashBuiltIn.Error:
            if not cls.splash_mute_level & SplashMuteLevel.Error:
                cls.show(SplashBuiltIn.Error, data)
                return True
        elif splash_type == SplashBuiltIn.Battery:
            if not cls.splash_mute_level & SplashMuteLevel.Battery:
                cls.show(SplashBuiltIn.Battery, data)
                return True
        else:
            logger.warning("Splash type not found in built-in types.  Splash Type: {0}".format(splash_type))
            return False
        logger.info("Item not shown due to splash mute level.  Splash Type: {0}, Splash Mute Level: {1}".format(
            splash_type, cls.splash_mute_level))
        return False

    ##################################################################################
    # DISPLAYS TIMEOUT_SLEEP METHOD
    ##################################################################################
    # Callback method that occurs when the timeout is met on a non-Splash display.
    # The screen is put to sleep when the timeout occurs.
    ##################################################################################
    @classmethod
    def timeout_sleep(cls):
        # Turn out the backlight after timer expires
        if Backlight.method != BacklightMethod.NoBacklight and not Backlight.is_screen_sleeping():
            logger.debug("Timeout initiating Backlight Screen Sleep")
            Backlight.screen_sleep()

    ##################################################################################
    # DISPLAYS TIMEOUT_CLOSE METHOD
    ##################################################################################
    # Callback method that occurs when the timeout on a Splash display occurs.  The
    # last core display is shown on timeout.
    ##################################################################################
    @classmethod
    def timeout_close(cls):
        logger.debug("Timeout initiating Display Close")
        cls.show(cls.get_last_core_display(cls.current))

    ##################################################################################
    # DISPLAYS SHUTDOWN METHOD
    ##################################################################################
    # Classmethod to shutdown the application.  The method parameter indicates the
    # type of shutdown.  Normal indicates a standard exit from the program.  Error
    # indicates an unrecoverable error shutting down the program.  Terminate when
    # the OS or system indicates the application should shut down.  Reboot and
    # Shutdown are user initiated exits with a request to reboot or shutdown the
    # system as well.
    ##################################################################################
    @classmethod
    def shutdown(cls, method, exit_splash=None, splash_data=None):
        # method to shutdown application
        logger.debug("Shutdown requested.  Method: {0}, Exit Splash: {1}, Splash Data:{2}".
                     format(method, exit_splash, splash_data))
        if cls.loop_mode_shelled:
            logger.debug("Shutting down while in shelled mode.")
            if Defaults.tft_type is not DISP22NT:
                pygame.mouse.set_visible(False)
            Displays.screen = pygame.display.set_mode(Defaults.tft_size)
        if method == Shutdown.Terminate:
            draw_true_rect(Displays.screen, Color.Black, 0, 0, Defaults.tft_width, Defaults.tft_height, 0)
            pygame.display.flip()
            if Backlight.method is not BacklightMethod.NoBacklight:
                Backlight.screen_sleep()
        else:
            if exit_splash is not None:
                not_muted = Displays.show_splash(exit_splash, splash_data)
            else:
                not_muted = Displays.show_splash(SplashBuiltIn.Exit)
            if not not_muted:
                Displays.show(SplashBuiltIn.Blank)
            pygame.display.flip()
        pygame.quit()
        cls.started = False
        if method is Shutdown.Shutdown:
            subprocess.call(Command.Shutdown.split())
        elif method is Shutdown.Reboot:
            subprocess.call(Command.Reboot.split())
        logger.debug("Exiting application.")
        sys.exit()

    ##################################################################################
    # DISPLAYS SHELL METHOD
    ##################################################################################
    # Classmethod to show the TTY command line instead of the displays.  This puts the
    # tftmenu program into a state where it monitors only for the return from the
    # shell indication (which is a long press on the screen.
    ##################################################################################
    @classmethod
    def shell(cls):
        if Defaults.tft_type is DISP22NT:
            logger.warning("Attempting shell on a non-touch display.  Ignoring request.")
            render_data = [SplashLine("WARNING", Defaults.default_splash_font_size_title),
                           SplashLine("Shell not permitted on non-touch display", wrap_text=True)]
            cls.show_splash(SplashBuiltIn.Warning, render_data)
        else:
            logger.debug("Shelling to {0}".format(Screen.Tty))
            cls.shelled = Displays.current
            pygame.display.quit()
            pygame.init()
            # Set loop_mode_shelled which puts our event loop in shelled mode where
            # only a long touch is detected
            cls.loop_mode_shelled = True

    ##################################################################################
    # DISPLAYS SHELL METHOD
    ##################################################################################
    # Classmethod to start X on an HDMI or TFT display if X is installed on the system
    ##################################################################################
    @classmethod
    def start_x(cls, hdmi=False):
        # Check if x is already running
        if run_cmd(["pidof", "x"]) <= 0:
            # if so, don't start it again and show warning
            logger.warning("Attempting to start X, but x is already running.")
            render_data = [SplashLine("WARNING", Defaults.default_splash_font_size_title),
                           SplashLine("X is already running.", wrap_text=True)]
            cls.show_splash(SplashBuiltIn.Warning, render_data)
        # Make sure StartX exists.  It will not on Lite versions of Raspian
        if os.path.isfile(START_X_FILE):
            # Determine which FRAMEBUFFER to start it on.
            if hdmi:
                subprocess.call(Command.StartXHdmi)
            else:
                subprocess.call(Command.StartXTft)
            return
        else:
            logger.warning("Attempting to start X but it could not be detected in default location: {0}"
                           .format(START_X_FILE))
            render_data = [SplashLine("WARNING", Defaults.default_splash_font_size_title),
                           SplashLine("GUI is not installed on in expected location.", wrap_text=True)]
            cls.show_splash(SplashBuiltIn.Warning, render_data)

    ##################################################################################
    # DISPLAYS RESTORE METHOD
    ##################################################################################
    # Classmethod used to restore the menu back from a shell.
    ##################################################################################
    @classmethod
    def restore(cls):
        logger.debug("Restoring back from shell.")
        send_wake_command()
        if Defaults.tft_type is not DISP22NT:
            pygame.mouse.set_visible(False)
        Displays.screen = pygame.display.set_mode(Defaults.tft_size)
        return_display = cls.get_last_core_display(Displays.shelled)
        return_display.force_refresh = True
        Displays.show(return_display)
        cls.loop_mode_shelled = False

    ##################################################################################
    # DISPLAYS SHELL METHOD
    ##################################################################################
    # Callback method from a signal to shutdown the menu.
    ##################################################################################
    @classmethod
    def on_shutdown(cls, signum, frame):
        logger.debug("Shutdown Signal Received.  Signum:{0}, Frame:{1}".format(signum, frame))
        cls.shutdown(Shutdown.Normal if signum is signal.SIGINT else Shutdown.Terminate)

    ##################################################################################
    # GET_LAST_CORE_DISPLAY
    ##################################################################################
    # This method iterates backwards from the current display to find the last display
    # up the chain that is of class Display or Menu.   This is used when closing a
    # display or splash to ensure the close happens back to a core display type (not
    # another splash or dialog) so that dialogs and splashes could be chained together
    # and still "closed' back to a core display.
    ##################################################################################
    @classmethod
    def get_last_core_display(cls, start=None):
        previous = cls.current.last if start is None else start
        while previous is not None:
            if previous.is_core:
                logger.debug("Last Core Display detected normally.  Display: {0}".format(previous))
                return previous
            # Avoid case where we get stuck in a loop
            if previous.last == previous:
                logger.debug("Last Core Display detected via loop prevention.  Display: {0}".format(Displays.last))
                return Displays.last
            else:
                previous = previous.last
        return cls.initial

    ##################################################################################
    # CHECK_LIB_SDL_VERSION
    ##################################################################################
    # This method checks to see if libsdl1.2debian is installed and if the version is
    # correct to enable touch on the Raspberry Pi.
    ##################################################################################
    @classmethod
    def check_lib_sdl_version(cls):
        full_version = get_package_version(Package.PkgLibSdl)
        if full_version is None:
            return False
        version_info = full_version.split("-")
        lib_version = version_info[0].lstrip()
        if len(version_info) > 1:
            lib_build = version_info[1]
        else:
            lib_build = None
        if lib_version == Package.LibSdlVersion and lib_build == Package.LibSdlBuild:
            return True
        cls.libsdl_build = lib_build
        cls.libsdl_version = lib_version
        return False

    ##################################################################################
    # DISPLAYS INITIALIZE METHOD
    ##################################################################################
    # Classmethod to initialize Displays class.  Sets any defaults, the mute level of
    # Splash displays and then the splash displays.  Also initializes pygame and the
    # touchscreen drivers.
    @classmethod
    def initialize(cls, tft_type, global_background_color=None, global_border_width=None, global_border_color=None,
                   global_font=None, global_font_size=None, global_font_color=None, global_font_h_padding=None,
                   global_font_v_padding=None, global_font_h_align=None, global_font_v_align=None,
                   splash_mute_level=SplashMuteLevel.NoMute, splash_timeout=Defaults.DEFAULT_SPLASH_TIMEOUT_MEDIUM):

        # If a touch device is specified, make sure the LibSdl version is correct.  If
        # not, display a warning unless suppressed.
        if tft_type is not DISP22NT:
            cls.check_lib_sdl_version()

        cls.splash_mute_level = splash_mute_level
        # Set the defaults based on the resolution of the display.  Fonts are scaled
        # using the font resolutions setting which provides similar sized fonts for
        # both the small and large displays.
        logger.debug("Initializing Defaults")
        Defaults.set_defaults(tft_type, global_background_color=global_background_color,
                              global_border_width=global_border_width, global_border_color=global_border_color,
                              global_font=global_font, global_font_size=global_font_size,
                              global_font_color=global_font_color, global_font_h_padding=global_font_h_padding,
                              global_font_v_padding=global_font_v_padding, global_font_h_align=global_font_h_align,
                              global_font_v_align=global_font_v_align)
        cls.menus[SplashBuiltIn.Blank] = Splash(None, Color.Black, timeout=1)
        logger.debug("Creating built-in Splash Displays.  Splash Mule Level: {0}".format(cls.splash_mute_level))
        if not cls.splash_mute_level & SplashMuteLevel.Exit:
            # Create the internally used splash screens.  First one is the exit screen splash
            cls.menus[SplashBuiltIn.Exit] = Splash([
                SplashLine("MENU CLOSING", Defaults.default_splash_font_size_title),
                SplashLine("Please wait for a few seconds.", Defaults.default_splash_font_size)], Color.Green,
                timeout=Defaults.DEFAULT_SPLASH_TIMEOUT_SHORT)
        if not cls.splash_mute_level & SplashMuteLevel.Info:
            # This creates the information screen splash used to pass non-critical information
            cls.menus[SplashBuiltIn.Info] = Splash([
                SplashLine("ATTENTION", Defaults.default_splash_font_size_title),
                SplashLine("Unspecified Information", Defaults.default_splash_font_size)], Color.Blue,
                timeout=splash_timeout)
        if not cls.splash_mute_level & SplashMuteLevel.Warning:
            # This creates the error screen splash used to indicate an warning
            cls.menus[SplashBuiltIn.Warning] = Splash([
                SplashLine("WARNING", Defaults.default_splash_font_size_title),
                SplashLine("Unspecified Warning.", Defaults.default_splash_font_size)], Color.Orange,
                timeout=splash_timeout)
        if not cls.splash_mute_level & SplashMuteLevel.Warning and\
                (cls.libsdl_version is not None or cls.libsdl_build is not None):
            # This creates the error screen splash used to indicate a touch version dll warning
            cls.menus[SplashBuiltIn.Touch] = Splash([
                SplashLine("WARNING", Defaults.default_splash_font_size_title),
                SplashLine("Touch may not work due to incompatible version {0}-{1} of libsdl1.2debian package.".format(
                        cls.libsdl_version, cls.libsdl_build),
                            Defaults.default_splash_font_size, wrap_text=True),
                SplashLine("Run downgrade-sdl.sh to repair.", Defaults.default_splash_font_size,
                           font_color=Color.Black),
                ], Color.Orange,
                timeout=10)
        if not cls.splash_mute_level & SplashMuteLevel.Error:
            # This creates the error screen splash used to indicate an error.
            cls.menus[SplashBuiltIn.Error] = Splash([
                SplashLine("ERROR", Defaults.default_splash_font_size_title),
                SplashLine("Unspecified Error", Defaults.default_splash_font_size)], Color.Red,
                timeout=splash_timeout)
        if not cls.splash_mute_level & SplashMuteLevel.Battery:
            # This creates the error screen splash used to indicate an low battery shutdown
            cls.menus[SplashBuiltIn.Battery] = Splash([
                SplashLine("LOW BATTERY", Defaults.default_splash_font_size_title, Color.Black),
                SplashLine("System will shut down shortly.", Defaults.default_splash_font_size, Color.Black)],
                Color.Yellow, timeout=Defaults.DEFAULT_SPLASH_TIMEOUT_LONG)
        # Initialize touchscreen drivers
        if Defaults.tft_type is not DISP22NT:
            logger.debug("Initializing Touchscreen Drivers")
            os.environ["SDL_FBDEV"] = "/dev/fb1"
            os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
            os.environ["SDL_MOUSEDRV"] = "TSLIB"
        # Initialize pygame and hide mouse if not using a non-touch display
        logger.debug("Initializing pygame")
        pygame.init()
        if Defaults.tft_type is not DISP22NT:
            pygame.mouse.set_visible(False)
        logger.info("Initialization complete")
        cls.initialized = True

    ##################################################################################
    # DISPLAYS START METHOD
    ##################################################################################
    # Classmethod called to start the menu Displays.   The initial menu needs to be
    # passed it, along with any settings for the backlight.  The main execution loop
    # then follows.
    @classmethod
    def start(cls, initial_menu, backlight_method=None, backlight_steps=None, backlight_default=None,
              backlight_restore_last=False, backlight_state_sleep=False, backlight_auto=False, button_callback=None,
              power_gpio=None, use_old_pwm=False, battery_gpio=None):
        # Make sure start process has not already started.
        if cls.started:
            return
        cls.started = True
        button_down = 0
        down_time = None
        # Make sure initialization has been run
        if not cls.initialized or Defaults.tft_type is None:
            logger.error("Displays class not initialized.")
            cls.started = False
            raise NotInitializedException("Displays not initialized.  Use initialize() method before start().")
        # Add signals for shutdown from OS
        signal.signal(signal.SIG_IGN, cls.on_shutdown)
        signal.signal(signal.SIGINT, cls.on_shutdown)
        signal.signal(signal.SIGTERM, cls.on_shutdown)
        # Set display mode in pygame and set
        cls.screen = pygame.display.set_mode(Defaults.tft_size)
        try:
            # Create TFTButtons
            tft_buttons = GpioButtons(Defaults.tft_type, backlight_method=backlight_method,
                                      backlight_steps=backlight_steps, backlight_default=backlight_default,
                                      backlight_restore_last=backlight_restore_last, backlight_auto=backlight_auto,
                                      backlight_state_sleep=backlight_state_sleep, use_old_pwm=use_old_pwm,
                                      button_callback=button_callback, power_gpio=power_gpio,  battery_gpio=battery_gpio)
            # Show and set initial menu
            Displays.initial = initial_menu
            Displays.show(initial_menu)

            if cls.libsdl_build is not None or cls.libsdl_version is not None:
                Displays.show(cls.menus[SplashBuiltIn.Touch])
            ##################################################################################
            # Execution Wait Loop
            ##################################################################################
            while cls.loop:
                if not cls.loop_mode_shelled:
                    # Scan touchscreen and keyboard events
                    for event in pygame.event.get():
                        # Mouse down or touch on screen
                        if event.type == MOUSEBUTTONDOWN:
                            Timer.reset()
                            if Backlight.method != BacklightMethod.NoBacklight and Backlight.is_screen_sleeping():
                                logger.debug("Button Down Ignored while screen is sleeping")
                            else:
                                pos = pygame.mouse.get_pos()
                                button_down = cls.current.process_down_button(cls.current.process_location(pos))
                                logger.debug("Button Down Event occurred in Button: {0}".format(button_down))
                                down_time = time.time()
                        # Mouse up or release on screen
                        elif event.type == MOUSEBUTTONUP:
                            Timer.reset()
                            if Backlight.method != BacklightMethod.NoBacklight and Backlight.is_screen_sleeping():
                                Backlight.screen_wake()
                            else:
                                # Need to send the screen wake on any mouse up or button press
                                # when Backlight.method == BacklightMethod.NoBacklight
                                if Backlight.method == BacklightMethod.NoBacklight:
                                    logger.debug("Button Up waking screen while screen is sleeping")
                                    Backlight.screen_wake()
                                pos = pygame.mouse.get_pos()
                                cls.current.process_up_button(button_down)
                                button_up = cls.current.process_location(pos)
                                logger.debug("Button Up Event occurred in Button: {0}".format(button_up))
                                # if the up button was the same as the down button, then process
                                # the button.
                                if button_up == button_down:
                                    logger.debug("Button press occurred.  Down Button: {0}, Up Button: {1}"
                                                 .format(button_down, button_up))
                                    # Get the next menu and any associated data from the
                                    # process_button method, then call Displays.show.  If the
                                    # menu is the same, it will not be re-rendered unless the
                                    # force_render flag is set - this allows for the Splash and
                                    # Dialog items to have changeable text
                                    if time.time() - down_time > Times.RightClick or event.button == MouseButton.Right:
                                        button_type = MouseButton.Right
                                    else:
                                        button_type = MouseButton.Left
                                    next_menu, next_data = cls.current.process_button(button_up, button_type)
                                    Displays.show(next_menu, next_data)
                                else:
                                    logger.debug("Button press ignored.  Down Button: {0}, Up Button: {1}"
                                                 .format(button_down, button_up))
                                # Reset the down button.
                                button_down = 0
                        elif event.type == KEYDOWN:
                            Timer.reset()
                        elif event.type == KEYUP:
                            Timer.reset()
                            if Backlight.method == BacklightMethod.NoBacklight or Backlight.is_screen_sleeping():
                                Backlight.screen_wake()
                            # Allow escape key to exit menu application
                            if event.key == K_ESCAPE:
                                logger.debug("Escape Key pressed")
                                cls.loop = False
                        else:
                            logger.debug("Ignored pygame event.  Event: {0}".format(event.type))
                    # Check for expired timer.  If so, execute all functions in the display's
                    # timeout_function.
                    if Timer.is_expired():
                        if cls.current.timeout_function is not None:
                            for timeout_function in cls.current.timeout_function:
                                timeout_function()
                    # If the display has a header attribute, call header update which will take
                    # care of refreshing the header if necessary
                    if hasattr(cls.current, Attributes.Header) and cls.current.header is not None:
                        cls.current.header.update(cls.current)
                    if hasattr(cls.current, Attributes.Footer) and cls.current.footer is not None:
                        cls.current.footer.update(cls.current)
                    cls.current.draw()
                else:
                    for event in pygame.event.get():
                        # Mouse up or release on screen
                        if event.type == MOUSEBUTTONDOWN:
                            down_time = time.time()
                        if event.type == MOUSEBUTTONUP:
                            if time.time() - down_time > Times.RightClick or event.button == MouseButton.Right:
                                Displays.restore()
                if tft_buttons.is_low_battery():
                    exit_splash = SplashBuiltIn.Battery
                    cls.shutdown(Shutdown.Shutdown, exit_splash)
                # Sleep for a bit
                time.sleep(Times.SleepLoop)
            cls.shutdown(Shutdown.Normal)
        # Catch Ctl-C Exit so error is not displayed
        except KeyboardInterrupt:
            # Keeps error from displaying when CTL-C is pressed
            print(""),
        # Catch other Error
        except Exception, ex:
            # If we have an error,
            exit_splash = SplashBuiltIn.Error
            error_message = unicode(ex)
            splash_data = [SplashLine("ERROR", Defaults.default_splash_font_size_title),
                           SplashLine(error_message, Defaults.default_splash_font_size, wrap_text=True)]
            logger.error(error_message, exc_info=True)
            cls.shutdown(Shutdown.Error, exit_splash, splash_data)


##################################################################################
# BASELINE LINE CLASS
##################################################################################
# Base class of all rendered text on the displays
##################################################################################
class BaseLine(object):
    text = None
    font_size = None
    font_color = None
    font = None
    font_h_align = None
    font_h_padding = None
    font_style = None
    font_v_align = None
    font_v_padding = None
    font_pad = None

    ##################################################################################
    # BASELINE INIT METHOD
    ##################################################################################
    # Initialize method of the BaseLine class.  Unlike the other line classes, this
    # one does not set any defaults.
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=False,
                 wrap_text=False):
        self.text = text
        self.font_size = font_size
        self.font_color = font_color
        self.font = font
        self.font_style = font_style
        self.font_h_align = font_h_align
        self.font_h_padding = font_h_padding
        self.font_v_align = font_v_align
        self.font_v_padding = font_v_padding
        self.font_pad = font_pad
        self.wrap_text = wrap_text

    ##################################################################################
    # BASELINE RENDER METHOD
    ##################################################################################
    # Method to render the text of a BaseLine or derived object.
    ##################################################################################
    def render(self, background_color=None):
        if self.font is None:
            self.font = pygame.freetype.Font(None, self.font_size, resolution=Defaults.default_font_resolution)
        elif isinstance(self.font, pygame.freetype.Font):
            self.font = pygame.freetype.Font(self.font.path, self.font_size,
                                             resolution=Defaults.default_font_resolution)
        else:
            self.font = pygame.freetype.Font(self.font, self.font_size, resolution=Defaults.default_font_resolution)
        self.font.style = self.font_style
        self.font.pad = self.font_pad
        if not self.wrap_text:
            return self.font.render(self.text if self.text is not None else "", fgcolor=self.font_color)
        else:
            wrapped_text = ""
            try:
                wrapped_text = wrap_text_line(self.font, self.text if self.text is not None else "",
                                              Defaults.tft_width - (self.font_h_padding * 2)
                                              if not hasattr(Displays.current, "border_width")
                                              else Defaults.tft_width - ((Displays.current.border_width +
                                                                          self.font_h_padding) * 2))
            except Exception, ex:
                logger.error("Error occurred while attempting to wrap text.  {0}".format(ex))
                Displays.shutdown(Shutdown.Error, SplashBuiltIn.Error)
            if len(wrapped_text[0]) is 1:
                return self.font.render(wrapped_text[0][0] if wrapped_text[0][0] is not None else "",
                                        fgcolor=self.font_color)
            else:
                surface_width = max(wrapped_text[2])
                surface_height = sum(wrapped_text[1]) + (self.font_v_padding * (len(wrapped_text[0]) - 1))
                text_surface = pygame.Surface((surface_width, surface_height))
                if background_color is not None:
                    text_surface.fill(background_color)
                text_top = 0
                for index in range(0, len(wrapped_text[0])):
                    top = text_top
                    if self.font_h_align == TextHAlign.Left:
                        left = 0
                    elif self.font_h_align == TextHAlign.Right:
                        left = surface_width - 1 - int(wrapped_text[2][index])
                    else:
                        left = (surface_width / 2) - (int(wrapped_text[2][index]) / 2)
                    try:
                        self.font.render_to(text_surface, (left, top), wrapped_text[0][index], fgcolor=self.font_color)
                    except Exception, ex:
                        logger.error("Error occurred while attempting to render wrapped text.  {0}".format(ex))
                    text_top += wrapped_text[1][index] + self.font_v_padding
                return text_surface, text_surface.get_rect()


##################################################################################
# TFTMENU TEXT LINE CLASS
##################################################################################
# Text line class designed to be used for Display and Menu classes
##################################################################################
class TextLine(BaseLine):

    ##################################################################################
    # TEXT LINE INIT METHOD
    ##################################################################################
    # Initializes a Text Line item with the Text Line defaults
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(TextLine, self).__init__(text=text, font_size=font_size, font_color=font_color, font=font,
                                       font_style=font_style, font_h_align=font_h_align, font_h_padding=font_h_padding,
                                       font_v_align=font_v_align, font_v_padding=font_v_padding, font_pad=font_pad,
                                       wrap_text=wrap_text)
        if self.font is None:
            self.font = Defaults.default_text_line_font
        if self.font_color is None:
            self.font_color = Defaults.default_text_line_font_color
        if self.font_size is None:
            self.font_size = Defaults.default_text_line_font_size
        if self.font_style is None:
            self.font_style = pygame.freetype.STYLE_NORMAL
        if self.font_h_align is None:
            self.font_h_align = Defaults.default_text_line_font_h_align
        if self.font_v_align is None:
            self.font_v_align = Defaults.default_text_line_font_v_align
        if self.font_h_padding is None:
            self.font_h_padding = Defaults.default_text_line_font_h_padding
        if self.font_v_padding is None:
            self.font_v_padding = Defaults.default_text_line_font_v_padding


##################################################################################
# TFTMENU SPLASH LINE CLASS
##################################################################################
# Splash line class designed to be used for Splash classes
##################################################################################
class SplashLine(BaseLine):

    ##################################################################################
    # SPLASH LINE INIT METHOD
    ##################################################################################
    # Initializes a Splash Line item with the Splash defaults
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(SplashLine, self).__init__(text=text, font_size=font_size, font_color=font_color, font=font,
                                         font_style=font_style, font_h_align=font_h_align,
                                         font_h_padding=font_h_padding, font_v_align=font_v_align,
                                         font_v_padding=font_v_padding, font_pad=font_pad, wrap_text=wrap_text)
        if self.font is None:
            self.font = Defaults.default_splash_font
        if self.font_color is None:
            self.font_color = Defaults.default_splash_font_color
        if self.font_size is None:
            self.font_size = Defaults.default_splash_font_size
        if self.font_style is None:
            self.font_style = pygame.freetype.STYLE_NORMAL
        if self.font_h_align is None:
            self.font_h_align = Defaults.default_splash_font_h_align
        if self.font_v_align is None:
            self.font_v_align = Defaults.default_splash_font_v_align
        if self.font_h_padding is None:
            self.font_h_padding = Defaults.default_splash_font_h_padding
        if self.font_v_padding is None:
            self.font_v_padding = Defaults.default_splash_font_v_padding


##################################################################################
# TFTMENU DIALOG LINE CLASS
##################################################################################
# Dialog line class designed to be used for Dialog classes
##################################################################################
class DialogLine(BaseLine):

    ##################################################################################
    # DIALOG LINE INIT METHOD
    ##################################################################################
    # Initializes a Dialog Line item with the Dialog defaults
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(DialogLine, self).__init__(text=text, font_size=font_size, font_color=font_color, font=font,
                                         font_style=font_style, font_h_align=font_h_align,
                                         font_h_padding=font_h_padding, font_v_align=font_v_align,
                                         font_v_padding=font_v_padding, font_pad=font_pad, wrap_text=wrap_text)
        if self.font is None:
            self.font = Defaults.default_dialog_font
        if self.font_color is None:
            self.font_color = Defaults.default_dialog_font_color
        if self.font_size is None:
            self.font_size = Defaults.default_dialog_font_size
        if self.font_style is None:
            self.font_style = pygame.freetype.STYLE_NORMAL
        if self.font_h_align is None:
            self.font_h_align = Defaults.default_dialog_font_h_align
        if self.font_v_align is None:
            self.font_v_align = Defaults.default_dialog_font_v_align
        if self.font_h_padding is None:
            self.font_h_padding = Defaults.default_dialog_font_h_padding
        if self.font_v_padding is None:
            self.font_v_padding = Defaults.default_dialog_font_v_padding


##################################################################################
# TFTMENU HEAD/FOOT LINE CLASS
##################################################################################
# Head/Foot line class designed to be used for Header and Footer classes within
# other displays.
##################################################################################
class HeadFootLine(BaseLine):

    ##################################################################################
    # HEAD/FOOT LINE INIT METHOD
    ##################################################################################
    # Initializes a Head/Foot Line item with the Head/Foot defaults
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(HeadFootLine, self).__init__(text=text, font_size=font_size, font_color=font_color, font=font,
                                           font_style=font_style, font_h_align=font_h_align,
                                           font_h_padding=font_h_padding, font_v_align=font_v_align,
                                           font_v_padding=font_v_padding, font_pad=font_pad, wrap_text=wrap_text)
        if self.font is None:
            self.font = Defaults.default_headfoot_font
        if self.font_color is None:
            self.font_color = Defaults.default_headfoot_font_color
        if self.font_size is None:
            self.font_size = Defaults.default_headfoot_font_size
        if self.font_style is None:
            self.font_style = pygame.freetype.STYLE_NORMAL
        if self.font_h_align is None:
            self.font_h_align = Defaults.default_headfoot_font_h_align
        if self.font_v_align is None:
            self.font_v_align = Defaults.default_headfoot_font_v_align
        if self.font_h_padding is None:
            self.font_h_padding = Defaults.default_headfoot_font_h_padding
        if self.font_v_padding is None:
            self.font_v_padding = Defaults.default_headfoot_font_v_padding


##################################################################################
# TFTMENU BUTTON LINE CLASS
##################################################################################
# Button line class designed to be used for Button classes
##################################################################################
class ButtonLine(BaseLine):

    ##################################################################################
    # BUTTON LINE INIT METHOD
    ##################################################################################
    # Initializes a Button Line item with the Button defaults
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(ButtonLine, self).__init__(text=text, font_size=font_size, font_color=font_color, font=font,
                                         font_style=font_style, font_h_align=font_h_align,
                                         font_h_padding=font_h_padding, font_v_align=font_v_align,
                                         font_v_padding=font_v_padding, font_pad=font_pad, wrap_text=wrap_text)
        if self.font is None:
            self.font = Defaults.default_button_font
        if self.font_color is None:
            self.font_color = Defaults.default_button_font_color
        if self.font_size is None:
            self.font_size = Defaults.default_button_font_size
        if self.font_style is None:
            self.font_style = pygame.freetype.STYLE_NORMAL
        if self.font_h_align is None:
            self.font_h_align = Defaults.default_button_font_h_align
        if self.font_v_align is None:
            self.font_v_align = Defaults.default_button_font_v_align
        if self.font_h_padding is None:
            self.font_h_padding = Defaults.default_button_font_h_padding
        if self.font_v_padding is None:
            self.font_v_padding = Defaults.default_button_font_v_padding


##################################################################################
# TFTMENU ACTION CLASS
##################################################################################
# Class to hold the information about a soft button action
##################################################################################
class Action(object):
    action = None
    data = None
    render_data = None

    ##################################################################################
    # ACTION INIT METHOD
    ##################################################################################
    # Sets soft-Button Action properties to defaults.
    ##################################################################################
    def __init__(self, action=DisplayAction.NoAction, data=None, render_data=None):
        self.action = action
        self.data = data
        self.render_data = render_data


##################################################################################
# TFTMENU DISPLAY CLASS
##################################################################################
# Base Class for all displays in the menu system.  The Display class is the base
# menu item that can be used for menus without a header and/or footer.  It's main
# purpose is to display buttons.  It is a core display.
##################################################################################
class Display(object):
    background_color = None
    border_color = None
    border_width = 0
    buttons = []
    actions = []
    timeout = 0
    timeout_function = None
    draw_callback = []
    last = None
    force_refresh = False
    is_core = False

    ##################################################################################
    # DISPLAY INIT METHOD
    ##################################################################################
    # Initialize the Display class with defaults
    ##################################################################################
    def __init__(self, background_color=Defaults.default_background_color,
                 border_color=Defaults.default_border_color, border_width=None,
                 buttons=None, actions=None, timeout=Defaults.default_timeout, timeout_function=None,
                 draw_callback=None):
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
        self.buttons = array_single_none(buttons)
        self.actions = array_single_none(actions)
        self.timeout = timeout
        self.timeout_function = merge(Displays.timeout_sleep, timeout_function)
        if self.border_width is None:
            self.border_width = Defaults.default_border_width
        self.draw_callback = array_single_none(draw_callback)
        self.is_core = True

    ##################################################################################
    # DISPLAY RENDER METHOD
    ##################################################################################
    # Method for rendering Display and Menu items.  Set the screen to the background
    # color, draws the border, renders any header of footer and finally renders the
    # buttons and sets any screen timeout.
    ##################################################################################
    def render(self, data=None):
        # No need to render unless current display
        if Displays.current == self and not self.force_refresh:
            return
        self.force_refresh = False
        # Fill with background color
        Displays.screen.fill(self.background_color)
        # Draw Border
        draw_true_rect(Displays.screen, self.border_color, 0, 0, Defaults.tft_width - 1, Defaults.tft_height - 1,
                       self.border_width)
        # Draw Header
        if hasattr(self, 'header'):
            if self.header is not None:
                self.header.render(self)
        if hasattr(self, 'footer'):
            if self.footer is not None:
                self.footer.render(self)
        # Draw Buttons
        self.render_buttons()
        # Update Screen
        pygame.display.flip()
        # Set Timeout
        Timer.timeout(self.timeout)
        Backlight.screen_wake()

    ##################################################################################
    # DISPLAYS RENDER_BUTTONS METHOD
    ##################################################################################
    # Method that loops through the buttons in class to be rendered and calls the
    # Button render function for each.
    ##################################################################################
    def render_buttons(self):
        for button in self.buttons:
            if button is not None:
                button.render()

    ##################################################################################
    # DISPLAYS PROCESS_LOCATION METHOD
    ##################################################################################
    # Method that takes a pygame touch event and returns the button id that contained
    # the touch hit.
    ##################################################################################
    def process_location(self, position):
        x = position[0]
        y = position[1]
        hit = 0
        count = 0
        for menuButton in self.buttons:
            count += 1
            if menuButton.x <= x <= menuButton.x + menuButton.width and\
                    (y >= menuButton.y and (y <= menuButton.y + menuButton.height)):
                hit = count
                break
        return hit

    ##################################################################################
    # DISPLAYS PROCESS_DOWN_BUTTON METHOD
    ##################################################################################
    # Method that processes a button press by displaying the button in the button
    # down state (filled in background).
    ##################################################################################
    def process_down_button(self, button_index):
        if button_index == 0:
            return button_index
        button = self.buttons[button_index - 1]
        if button is not None:
            if not (isinstance(Displays.current, Dialog) and Displays.current.dialog_type is DialogStyle.FullScreenOk):
                button_rect = button.render(True)
                if button_rect:
                    pygame.display.update(button_rect)
            return button_index
        else:
            return 0

    ##################################################################################
    # DISPLAYS PROCESS_UP_BUTTON METHOD
    ##################################################################################
    # Method the processes a button up release by rendering the button back to the
    # outline only state.
    ##################################################################################
    def process_up_button(self, button_index):
        if button_index == 0:
            return
        button = self.buttons[button_index - 1]
        if button is not None:
            button_rect = button.render()
            if button_rect:
                pygame.display.update(button_rect)

    ##################################################################################
    # DISPLAYS PROCESS_BUTTON METHOD
    ##################################################################################
    # Method that takes a button press (a consecutive button up and button down event
    # in the same button) and calls the appropriate action depending if a normal click
    # or a right click (long press).  The action is then performed based on the action
    # type of the action.
    ##################################################################################
    def process_button(self, button_index, button_type):
        if button_index == 0:
            return self, None
        button = self.buttons[button_index - 1]
        # See if the button is a normal button or a right button click and use the
        # appropriate action.
        if button.action_right is None or button_type == MouseButton.Left:
            action = button.action.action
            action_data = button.action.data
            action_render_data = button.action.render_data
        else:
            action = button.action_right.action
            action_data = button.action_right.data
            action_render_data = button.action_right.render_data
        new_menu = self
        if action == DisplayAction.NoAction:
            return new_menu, None
        elif action == DisplayAction.Display:
            if action_data is not None and action_data and action_data in Displays.menus:
                new_menu = Displays.menus[action_data]
            else:
                return Displays.get_last_core_display(), None
        elif action == DisplayAction.Back:
            new_menu = Displays.get_last_core_display()
            if new_menu is None:
                if Displays.initial is not None:
                    new_menu = Displays.initial
                else:
                    Displays.shutdown(Shutdown.Error)
        elif action == DisplayAction.Exit:
            Displays.loop = False
        elif action == DisplayAction.Function:
            if action_data is not None and action_data:
                return_val = action_data(self, button)
                if return_val is not None:
                    if isinstance(return_val, Display):
                        new_menu = return_val
        elif action == DisplayAction.ScreenSleep:
            Backlight.screen_sleep()
        elif action == DisplayAction.BacklightUp:
            Backlight.backlight_up()
        elif action == DisplayAction.BacklightDown:
            Backlight.backlight_down()
        elif action == DisplayAction.Shell:
            Displays.shell()
        elif action == DisplayAction.Reboot:
            Displays.shutdown(Shutdown.Reboot)
        elif action == DisplayAction.Shutdown:
            Displays.shutdown(Shutdown.Shutdown)
        elif action == DisplayAction.StartX:
            Displays.start_x(action_data)
        elif action == DisplayAction.Execute:
            run_cmd(action_data)
        else:
            logger.warning("Unknown soft button action ({0}).  Nothing done.".format(action))
        return new_menu, action_render_data

    ##################################################################################
    # DISPLAYS DRAW METHOD
    ##################################################################################
    # Method that loops through a list of call back functions that can be used to
    # manually draw text or images or graphics on a menu.
    ##################################################################################
    def draw(self):
        if self.draw_callback is not None:
            for draw_function in self.draw_callback:
                logger.debug("Calling draw function {0}".format(draw_function))
                draw_function(Displays.screen, self)


##################################################################################
# TFTMENU MENU CLASS
##################################################################################
# Display Class for a Menu item, which is a base Display plus a Header or Footer.
# It's main purpose is to display buttons along with a header or footer for some
# additional information.  It is a core display.
##################################################################################
class Menu(Display):
    header = None
    footer = None

    ##################################################################################
    # MENU INIT METHOD
    ##################################################################################
    # Initialize the Menu class with defaults
    ##################################################################################
    def __init__(self, background_color=Defaults.default_background_color,
                 border_color=Defaults.default_border_color, border_width=None, buttons=None, actions=None,
                 timeout=Defaults.default_timeout, timeout_function=None, header=None, footer=None, draw_callback=None):
        super(Menu, self).__init__(background_color=background_color, border_color=border_color,
                                   border_width=border_width, buttons=buttons, actions=actions, timeout=timeout,
                                   timeout_function=timeout_function, draw_callback=draw_callback)
        if self.border_width is None:
            self.border_width = Defaults.default_border_width
        if header is None:
            self.header = Header(HeadFootType.NoDisplay)
        else:
            self.header = header
        if footer is None:
            self.footer = Header(HeadFootType.NoDisplay)
        else:
            self.footer = footer
        self.is_core = True


##################################################################################
# TFTMENU SPLASH CLASS
##################################################################################
# Display class that shows a message on the screen for an amount of time that is
# determined from the timeout property.  The display will then disappear and then
# return to the last core display.  The Splash item is used do display a message
# that does not require any user action.   A Splash item is NOT a core display.
##################################################################################
class Splash(Display):
    
    ##################################################################################
    # SPLASH INIT METHOD
    ##################################################################################
    # Initialize the Splash class with defaults.  Changes the default timeout callback
    # to use the timeout_close function instead of the timeout_sleep function.
    ##################################################################################
    def __init__(self, text=None, background_color=Defaults.default_splash_background_color,
                 timeout=Defaults.default_splash_timeout, timeout_function=None, draw_callback=None):
        super(Splash, self).__init__(background_color=background_color, border_color=None, border_width=None,
                                     buttons=None, actions=None, timeout=timeout, timeout_function=None,
                                     draw_callback=draw_callback)
        self.text = array_single_none(text)
        self.timeout_function = merge([Displays.timeout_close], timeout_function)
        self.is_core = False

    ##################################################################################
    # SPLASH RENDER METHOD
    ##################################################################################
    # Render the Splash display by showing the Splash Lines text and then setting the
    # timeout.
    ##################################################################################
    def render(self, data=None):
        # No need to render unless current display
        if Displays.current == self:
            return
        # Paint screen with background color.
        Displays.screen.fill(self.background_color)
        if data is not None:
            render_text = array_single_none(data)
        else:
            render_text = array_single_none(self.text)
        if render_text:
            splash_text_tuples = []
            splash_text_height = 0
            text_v_align = None
            last_item = None
            for text_item in render_text:
                if not isinstance(text_item, BaseLine):
                    text_item = SplashLine(text_item)
                if text_item.text is None:
                    text_item.text = ""
                if text_v_align is None:
                    text_v_align = text_item.font_v_align
                text_surface, text_font_rect = text_item.render(self.background_color)
                text_width = text_font_rect.width
                text_height = text_font_rect.height
                tuple_text = (text_surface, text_width, text_height, text_item.font_h_align, text_item.font_h_padding,
                              text_item.font_v_padding)
                last_text_height = text_height + text_item.font_v_padding
                splash_text_height += last_text_height
                splash_text_tuples.append(tuple_text)
                last_item = text_item
            splash_text_offset = 0
            if text_v_align is not TextVAlign.Top:
                splash_text_height -= last_item.font_v_padding
            for text_line in splash_text_tuples:
                # Handle horizontal alignment
                if text_line[TextTuple.HAlign] == TextHAlign.Left:
                    text_left = text_line[TextTuple.HPadding]
                elif text_line[TextTuple.HAlign] == TextHAlign.Right:
                    text_left = Defaults.tft_width - text_line[TextTuple.Width] - text_line[TextTuple.HPadding]
                else:
                    text_left = (Defaults.tft_width - text_line[TextTuple.Width]) / 2
                # Handle vertical alignment
                if text_v_align == TextVAlign.Top:
                    text_top = text_line[TextTuple.VPadding] + splash_text_offset
                elif text_v_align == TextVAlign.Bottom:
                    text_top = (Defaults.tft_height - 1) - splash_text_height - text_line[TextTuple.VPadding] +\
                               splash_text_offset
                else:
                    text_top = ((Defaults.tft_height - splash_text_height) / 2) + splash_text_offset
                splash_top_rect = text_line[TextTuple.Surface].get_rect(left=text_left, top=text_top)
                Displays.screen.blit(text_line[TextTuple.Surface], splash_top_rect)
                splash_text_offset += text_line[TextTuple.Height] + text_line[TextTuple.VPadding]
        pygame.display.flip()
        if self.timeout > 0:
            Timer.timeout(self.timeout, ignore_reset=True)
        Backlight.screen_wake()


##################################################################################
# TFTMENU DIALOG CLASS
##################################################################################
# Display Class for a Dialog item, which is a message along with pre-defined
# action buttons.  It's main purpose is to display a message and wait for user
# interaction to specify what to do next.  It is NOT a core display.
##################################################################################
class Dialog(Display):
    dialog_type = DialogStyle.Ok
    use_menu_timeout = False
    use_menu_colors = False

    ##################################################################################
    # DIALOG INIT METHOD
    ##################################################################################
    # Initialize the Dialog class with defaults
    ##################################################################################
    def __init__(self, text=None, dialog_type=DialogStyle.Ok, background_color=Defaults.default_dialog_background_color,
                 border_color=Defaults.default_dialog_border_color, border_width=None, actions=None, buttons=None,
                 timeout=Defaults.default_dialog_timeout, timeout_function=None, draw_callback=None,
                 use_menu_timeout=False, use_menu_colors=False):

        super(Dialog, self).__init__(background_color=background_color, border_color=border_color,
                                     border_width=border_width, buttons=buttons, actions=actions, timeout=timeout,
                                     timeout_function=merge(Displays.timeout_sleep, timeout_function),
                                     draw_callback=draw_callback)

        self.text = array_single_none(text)
        self.dialog_type = dialog_type
        self.use_menu_timeout = use_menu_timeout
        self.use_menu_colors = use_menu_colors
        self.is_core = False

    ##################################################################################
    # DIALOG RENDER METHOD
    ##################################################################################
    # Method to render a Dialog display Dialog Text, background, buttons and borders.
    # The dialog type can be a predefined template or can be custom.
    ##################################################################################
    def render(self, data=None):
        # No need to render unless current display
        if Displays.current == self:
            return
        button_border_color = self.border_color
        button_background_color = self.background_color
        display_background_color = self.background_color
        display_border_color = self.border_color
        display_border_width = self.border_width
        # Draw Borders and Background
        core_display = Displays.get_last_core_display(self)
        if core_display is not None and self.use_menu_colors:
            button_border_color = core_display.border_color
            button_background_color = core_display.background_color
            display_background_color = core_display.background_color
            display_border_color = core_display.border_color
            display_border_width = core_display.border_width
        # Create Buttons if there are none already created and no custom buttons
        if self.dialog_type != DialogStyle.Custom and not self.buttons:
            self.buttons = []
            if self.dialog_type == DialogStyle.YesNoCancel:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.Bottom3x1,
                                                        names=[DialogButtonText.Yes, DialogButtonText.No,
                                                               DialogButtonText.Cancel],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_border_color)
            elif self.dialog_type == DialogStyle.YesNo:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.Bottom2x1,
                                                        names=[DialogButtonText.Yes, DialogButtonText.No],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_border_color)
            elif self.dialog_type == DialogStyle.OkCancel:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.Bottom2x1,
                                                        names=[DialogButtonText.OK, DialogButtonText.Cancel],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_border_color)
            elif self.dialog_type == DialogStyle.FullScreenOk:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.FullScreenButton, names=[""],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            elif self.dialog_type == DialogStyle.Ok:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.Bottom1x1, names=[DialogButtonText.OK],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            elif self.dialog_type == DialogStyle.OkLeft:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.BottomLeft1x1, names=[DialogButtonText.OK],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            elif self.dialog_type == DialogStyle.OkRight:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.BottomRight1x1, names=[DialogButtonText.OK],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            elif self.dialog_type == DialogStyle.OkFullScreen:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.BottomFullWidth1x1, names=[DialogButtonText.OK],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            else:
                logger.warning("Unknown dialog type ({0}).  Using DialogButtonText.OK.".format(self.dialog_type))
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.Bottom1x1, names=[DialogButtonText.OK],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
        # Draw Borders and Background
        Displays.screen.fill(display_background_color)
        draw_true_rect(Displays.screen, display_border_color, 0, 0, Defaults.tft_width - 1, Defaults.tft_height - 1,
                       display_border_width)
        if not self.buttons or self.dialog_type == DialogStyle.FullScreenOk:
            dialog_text_area_height = Defaults.tft_height - display_border_width
        else:
            button_pos = get_buttons_start_height(self.buttons)
            if button_pos > Defaults.tft_height - (display_border_width * 2):
                dialog_text_area_height = Defaults.tft_height - (display_border_width * 2)
            else:
                dialog_text_area_height = button_pos - display_border_width
            # dialog_text_area_height = get_buttons_start_height(self.buttons)
        if data is not None:
            render_text = array_single_none(data)
        else:
            render_text = array_single_none(self.text)
        if render_text:
            dialog_text_tuples = []
            dialog_text_height = 0
            text_v_align = None
            last_item = None
            for text_item in render_text:
                if not isinstance(text_item, BaseLine):
                    text_item = DialogLine(text_item)
                if text_item.text is None:
                    text_item.text = ""
                elif text_v_align is None:
                    text_v_align = text_item.font_v_align
                text_surface, text_font_rect = text_item.render(display_background_color)
                text_width = text_font_rect.width
                text_height = text_font_rect.height
                tuple_text = (text_surface, text_width, text_height, text_item.font_h_align, text_item.font_h_padding,
                              text_item.font_v_padding)
                last_text_height = text_height + text_item.font_v_padding
                dialog_text_height += last_text_height
                dialog_text_tuples.append(tuple_text)
                last_item = text_item
            dialog_text_offset = 0
            if text_v_align is not TextVAlign.Top:
                dialog_text_height -= last_item.font_v_padding
            for text_line in dialog_text_tuples:
                # Handle horizontal alignment
                if text_line[TextTuple.HAlign] == TextHAlign.Left:
                    text_left = display_border_width + text_line[TextTuple.HPadding]
                elif text_line[TextTuple.HAlign] == TextHAlign.Right:
                    text_left = Defaults.tft_width - text_line[TextTuple.Width] - \
                               text_line[TextTuple.HPadding] - display_border_width
                else:
                    text_left = (Defaults.tft_width - text_line[TextTuple.Width]) / 2
                # Handle vertical alignment
                if text_v_align == TextVAlign.Top:
                    text_top = display_border_width + text_line[TextTuple.VPadding] + dialog_text_offset
                elif text_v_align == TextVAlign.Bottom:
                    text_top = dialog_text_area_height - dialog_text_height - text_line[TextTuple.VPadding] +\
                               dialog_text_offset
                else:
                    text_top = ((dialog_text_area_height - dialog_text_height) / 2) +\
                               dialog_text_offset + display_border_width
                dialog_top_rect = text_line[TextTuple.Surface].get_rect(left=text_left, top=text_top)
                Displays.screen.blit(text_line[TextTuple.Surface], dialog_top_rect)
                dialog_text_offset += text_line[TextTuple.Height] + text_line[TextTuple.VPadding]
        # Draw buttons unless we are using full screen button
        if self.dialog_type != DialogStyle.FullScreenOk:
            self.render_buttons()
        pygame.display.flip()
        Backlight.screen_wake()
        # Set the Screen Timeout if using the previous display's timeout
        if core_display is not None and self.use_menu_timeout:
            timeout = core_display.timeout
        else:
            timeout = self.timeout
        Timer.timeout(timeout)
        Backlight.screen_wake()


##################################################################################
# TFTMENU HEADER CLASS
##################################################################################
# Class for a Header item.
##################################################################################
class Header(object):
    text = None
    data = None
    mode = 0
    height = 0
    refresh = None
    last_update = None
    location = None

    ##################################################################################
    # HEADER INIT METHOD
    ##################################################################################
    # Header initialize method.
    ##################################################################################
    def __init__(self, text=None, data=None, mode=HeadFootType.NoDisplay, height=None, refresh=None):
        if text is None:
            self.text = HeadFootLine(None)
        elif not isinstance(text, HeadFootLine):
            self.text = HeadFootLine(unicode(text))
        else:
            self.text = text
        self.mode = mode
        self.data = data
        self.height = height
        self.refresh = refresh
        self.location = HeadFootLocation.Top
        if self.refresh is None:
            if self.mode == HeadFootType.Date:
                self.refresh = DisplayHeaderRefresh.Day
            elif self.mode == HeadFootType.Time12 or self.mode == HeadFootType.Time24 \
                or self.mode == HeadFootType.DateTime12 \
                    or self.mode == HeadFootType.DateTime24:
                self.refresh = DisplayHeaderRefresh.Minute
            else:
                self.refresh = DisplayHeaderRefresh.NoRefresh

    ##################################################################################
    # HEADER (AND FOOTER) RENDER METHOD
    ##################################################################################
    # Method to render the text for a header or footer using the predefined types.  A
    # header or footer can contain a refresh property that determines how often the
    # header or footer is redrawn.  This can be used to provide dynamic headers and
    # footers on a Menu display.
    ##################################################################################
    def render(self, display, clear=False):
        # Get Header Text based on mode.  If HeadFootType.UserText, nothing changes
        if self.mode == HeadFootType.NoDisplay:
            return
        elif self.mode == HeadFootType.Date:
            self.text.text = time.strftime("%B %d, %Y")
        elif self.mode == HeadFootType.Time12:
            self.text.text = time.strftime("%-I:%M %p")
        elif self.mode == HeadFootType.Time24:
            self.text.text = time.strftime("%R")
        elif self.mode == HeadFootType.DateTime12:
            self.text.text = time.strftime("%x %-I:%M %p")
        elif self.mode == HeadFootType.DateTime24:
            self.text.text = time.strftime("%x %R")
        elif self.mode == HeadFootType.DateTimeCustom:
            if self.data is not None:
                self.text.text = time.strftime(self.data)
        elif self.mode == HeadFootType.HostName:
            host_name = run_cmd("hostname")
            if self.text.text:
                self.text.text = self.text.text.format(host_name[:-1])
            else:
                self.text.text = host_name[:-1]
        elif self.mode == HeadFootType.IpAddress:
            ip_address = get_ip_address()
            if self.text.text:
                self.text.text = self.text.text.format(ip_address)
            else:
                self.text.text = ip_address
        elif self.mode == HeadFootType.UserFunction:
            if self.data is not None:
                self.text.text = unicode(self.data(self))
        elif self.mode is not HeadFootType.UserText:
            logger.warning("Unknown header mode ({0}).  No Header will be displayed.".format(self.mode))
            return
        if self.text.text is None:
            self.text.text = ""
        # Draw Header
        headfoot_surface, headfoot_font_rect = self.text.render(display.background_color)
        headfoot_text_width = headfoot_font_rect.width
        headfoot_text_height = headfoot_font_rect.height
        if self.height is None:
            if self.location is HeadFootLocation.Bottom:
                button_pos = get_buttons_end_height(display.buttons)
                if button_pos < display.border_width:
                    true_headfoot_height = Defaults.tft_height - (display.border_width * 2)
                else:
                    true_headfoot_height = Defaults.tft_height - (button_pos + 1) - display.border_width
            else:
                button_pos = get_buttons_start_height(display.buttons)
                if button_pos > Defaults.tft_height - (display.border_width * 2):
                    true_headfoot_height = Defaults.tft_height - (display.border_width * 2)
                else:
                    true_headfoot_height = button_pos - display.border_width
        else:
            true_headfoot_height = self.height
            button_pos = 0
        if self.location is HeadFootLocation.Top:
            headfoot_offset = display.border_width
        else:
            headfoot_offset = button_pos
        # Handle horizontal alignment
        if self.text.font_h_align == TextHAlign.Left:
            headfoot_text_left = display.border_width + self.text.font_h_padding
        elif self.text.font_h_align == TextHAlign.Right:
            headfoot_text_left = Defaults.tft_width - headfoot_text_width - display.border_width - \
                               self.text.font_h_padding
        else:
            headfoot_text_left = (Defaults.tft_width - headfoot_text_width) / 2
        # Handle vertical alignment
        if self.text.font_v_align == TextVAlign.Top:
            headfoot_text_top = headfoot_offset + self.text.font_v_padding
        elif self.text.font_v_align == TextVAlign.Bottom:
            headfoot_text_top = (true_headfoot_height + headfoot_offset) - headfoot_text_height -\
                              self.text.font_v_padding
        else:
            headfoot_text_top = (((true_headfoot_height / 2) - (headfoot_text_height / 2)) + headfoot_offset)

        headfoot_text_rect = headfoot_surface.get_rect(left=headfoot_text_left, top=headfoot_text_top)
        headfoot_background_rect = None
        if clear:
            headfoot_background_rect = Rect(display.border_width, headfoot_offset,
                                            Defaults.tft_width - (display.border_width * 2) - 1,
                                            true_headfoot_height)
            draw_true_with_rect(Displays.screen, display.background_color, headfoot_background_rect, 0)
        Displays.screen.blit(headfoot_surface, headfoot_text_rect)
        if clear:
            pygame.display.update(headfoot_background_rect)

    ##################################################################################
    # HEADER UPDATE METHOD
    ##################################################################################
    # Method that updates (refreshes) a Header (or Footer) item.  Uses the
    # DisplayHeaderRefresh parameter to decide what to update.  The use_two_second_-
    # range allows for an update to occur in either the first or second second after
    # an event occurs.  This allows slower systems to still process an event should
    # a process delay the initial notification.
    ##################################################################################
    def update(self, display):
        if self.refresh == DisplayHeaderRefresh.NoRefresh:
            return
        cur_time = int(time.time())
        local_time = time.localtime(cur_time)
        # Set Header Refresh if Date/Time is used
        if self.refresh == DisplayHeaderRefresh.Day:
            if local_time[TimeStruct.Hour] != 0 or local_time[TimeStruct.Minute] != 0 or\
                            local_time[TimeStruct.Second] != 0:
                return
            use_two_second_range = True
        elif self.refresh == DisplayHeaderRefresh.Hour:
            if local_time[TimeStruct.Minute] != 0 or local_time[TimeStruct.Second] != 0:
                return
            use_two_second_range = True
        elif self.refresh == DisplayHeaderRefresh.Minute:
            if local_time[TimeStruct.Second] != 0:
                return
            use_two_second_range = True
        elif self.refresh == DisplayHeaderRefresh.Second:
            use_two_second_range = False
        elif self.refresh == DisplayHeaderRefresh.All:
            use_two_second_range = None
        else:
            logger.warning("Unknown header refresh value ({0}).  Unable to set header refresh.".format(self.refresh))
            return
        # TODO fix issue with wrap around on seconds
        if use_two_second_range is not None:
            if use_two_second_range:
                if self.last_update == cur_time or self.last_update == cur_time - 1:
                    return
            else:
                if self.last_update == cur_time:
                    return
        self.render(display, True)
        self.last_update = cur_time


##################################################################################
# TFTMENU FOOTER CLASS
##################################################################################
# Class for a Footer item.  Subclass of Header
##################################################################################
class Footer(Header):

    ##################################################################################
    # FOOTER INIT METHOD
    ##################################################################################
    # Init method that calls the Header class to initialize.
    ##################################################################################
    def __init__(self, text=None, data=None, mode=HeadFootType.NoDisplay, height=None, refresh=None):
        super(Footer, self).__init__(text=text, data=data, mode=mode, height=height, refresh=refresh)
        self.location = HeadFootLocation.Bottom
                     
                     
##################################################################################
# TFTMENU BUTTON CLASS
##################################################################################
# Class for a button on a display.
##################################################################################
class Button(object):
    background_color = None
    border_color = None
    border_width = 0
    font = None
    font_color = None
    font_size = 0
    height = 0
    text = None
    x = 0
    y = 0
    width = 0
    action = None
    action_right = None

    ##################################################################################
    # BUTTON INIT METHOD
    ##################################################################################
    # Init method for Button class.  Sets defaults to button defaults
    ##################################################################################
    def __init__(self, text=None, x=0, y=0, width=None, height=Defaults.default_button_height,
                 background_color=Defaults.default_background_color, border_color=Defaults.default_button_border_color,
                 border_width=None, action=Action(DisplayAction.NoAction), action_right=None):
        if text is None:
            self.text = ButtonLine(None)
        elif not isinstance(text, BaseLine):
            self.text = ButtonLine(unicode(text))
        else:
            self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
        self.action = action
        self.action_right = action_right
        if self.width is None:
            self.width = Defaults.default_button_width
        if self.height is None:
            self.width = Defaults.default_button_height
        if self.border_width is None:
            self.border_width = Defaults.default_button_border_width

    ##################################################################################
    # BUTTON RENDER METHOD
    ##################################################################################
    # Method to render the a button including text.  The solid parameter indicates if
    # the button is an outline only (when False) or a solid rectangle (when True)
    ##################################################################################
    def render(self, solid=False):
        # No text means we don't render a button.
        if isinstance(self.text, BaseLine) and self.text.text is None:
            return None
        if not isinstance(self.text, BaseLine):
            self.text = ButtonLine(unicode(self.text))
        # Draw background color of button to reset the screen
        draw_true_rect(Displays.screen, self.background_color, self.x, self.y, self.width, self.height, 0)
        # If solid is true, make the entire button colored in, otherwise, just draw border
        if solid:
            button_rect = draw_true_rect(Displays.screen, self.border_color,
                                         self.x, self.y, self.width, self.height, 0)
        else:
            button_rect = draw_true_rect(Displays.screen, self.border_color,
                                         self.x, self.y, self.width, self.height, self.border_width)
        # Render text to get its size
        button_surface, button_font_rect = self.text.render(self.background_color)
        button_text_width = button_font_rect.width
        button_text_height = button_font_rect.height
        # Handle horizontal alignment
        if self.text.font_h_align == TextHAlign.Left:
            button_text_left = self.x + self.border_width + self.text.font_h_padding
        elif self.text.font_h_align == TextHAlign.Right:
            button_text_left = (self.x + self.width) - self.border_width - button_text_width - self.text.font_h_padding
        else:
            button_text_left = (self.x + (self.width / 2)) - (button_text_width / 2)
        # Handle vertical alignment
        if self.text.font_v_align == TextVAlign.Top:
            button_text_top = self.y + self.border_width + self.text.font_v_padding
        elif self.text.font_v_align == TextVAlign.Bottom:
            button_text_top = (self.y + self.height) - self.border_width - button_text_height - self.text.font_v_padding
        else:
            button_text_top = (self.y + (self.height / 2)) - (button_text_height / 2)
        button_text_rect = button_surface.get_rect(left=button_text_left, top=button_text_top)
        # Block transfer the text on the screen
        Displays.screen.blit(button_surface, button_text_rect)
        return button_rect
