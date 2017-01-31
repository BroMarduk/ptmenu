#!/usr/bin/python
##################################################################################
# TO DO
##################################################################################

# [20%] - Comment Functions
# [15%] - Add Warning and Exit dialogs in code
# [20%] - Add Logging
# [ 0%] - Code to standards
# [ 0%] - Move GPIO button templates to sepearate modules
# [90%] - Add StartX functionality - subprocess.call("FRAMEBUFFER=/dev/fb1 startx", shell=True)

# [OOS] - Make Tokens for Header Functions
# [OOS] - Move Text to Resources and use gettext
# [OOS] - Create Error, Warning and Info functions to make passing in text easier.
# [OOS] - Add Icons/Images to buttons

# DONE! - Make "Enums" out of Constant
# DONE! - Add footers to Menu
# DONE! - Add Right-Click button event
# DONE! - Fix Dialog & Splash Text Position
# DONE! - Fix Splash Timeout on Close
# DONE! - Add Text Alignment
# DONE! - Handle Internal Splash Screens
# DONE! - Check Splash Heights
# DONE! - Add Start function Support for Backlight options
# DONE! - Check Alternate Backlight Methods
# DONE! - Add Button Generator and Templates
# DONE! - Add Support for 480x320 Screens
# DONE! - Add support for 2x4 ScreenButtons
# DONE! - Add Timer for Date/Time Headers
# DONE! - Add Custom Button Functions
# DONE! - Add Backlight Functions for Buttons
# DONE! - Pass back header objcet to custom header function and see if we can change
# DONE! - Add button to custom button callback
# DONE! - Create Examples
# DONE! - Have Splash Screens take an optional text parameter to customize
# DONE! - Screen Timeout timer Resets on Splash touch
# DONE! - List properties that can take an array or singleton and make consistent
# DONE! - Clean up Debug procedure and statements
# DONE! - Multiline Text
# DONE! - Run Command Function
# DONE! - Create additional templates for dialogs and footers
# DONE! - Ensure that only one instance of the applicaiton is running.
# DONE! - Ensure Application runs as root.
# DONE! - When waking up the screen by touch, if you hold in a button it will press
# DONE! - When loading menu with timeout = 0, the initial splash does not work


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
file = open(lock_file, 'w')
try:
    fcntl.lockf(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    logger.critical("Only one instance of the applicaiton can run at a time.")
    sys.exit()

##################################################################################
# TFTMENUS DISPLAYS CLASS
##################################################################################
# Displays class responsible for the menu initialization and keeping track of
# current and last menus and states
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


    ##################################################################################
    # DISPLAYS SHOW METHOD
    ##################################################################################
    @classmethod
    def show(cls, item, data=None):
        # If item to show is already a menu, then just render and set.
        if isinstance(item, Display):
            display = item
        # If not a menu, attempt to find a menu with the same name
        elif item in cls.menus:
            display = cls.menus[item]
        if cls.current is None or display is not cls.current.last:
            display.last = cls.current
            if display.is_core:
                Displays.last = display
        display.render(data)
        cls.current = display


    ##################################################################################
    # DISPLAYS TIMEOUT_SLEEP METHOD
    ##################################################################################
    @classmethod
    def timeout_sleep(cls):
        # Turn out the backlight after timer expires
        if Backlight.method != BacklightMethod.NoBacklight and not Backlight.is_screen_sleeping():
            Backlight.screen_sleep()


    ##################################################################################
    # DISPLAYS TIMEOUT_CLOSE METHOD
    ##################################################################################
    @classmethod
    def timeout_close(cls):
        cls.show(cls.get_last_core_display(cls.current))

    ##################################################################################
    # DISPLAYS SHUTDOWN METHOD
    ##################################################################################
    @classmethod
    def shutdown(cls, method, exit_splash=None, splash_data=None):
        # method to shutdown application
        if cls.loop_mode_shelled:
            if Defaults.tft_type is not DISP22NT:
                pygame.mouse.set_visible(False)
            Displays.screen = pygame.display.set_mode(Defaults.tft_size)
        if  method == Shutdown.Terminate:
            draw_true_rect(Displays.screen, Color.Black, 0, 0, Defaults.tft_width, Defaults.tft_height, 0)
            pygame.display.flip()
            if Backlight.method is not BacklightMethod.NoBacklight:
                Backlight.screen_sleep()
        else:
            if exit_splash is not None:
                Displays.show(exit_splash, splash_data)
            else:
                Displays.show(SplashBuiltIn.Exit)
            pygame.display.flip()
        pygame.quit()
        Timer.abort()
        #del tft_buttons
        cls.started = False
        if method is Shutdown.Shutdown:
            subprocess.call(Command.Shutdown.split())
        elif method is Shutdown.Reboot:
            subprocess.call(Command.Reboot.split())
        sys.exit()


    @classmethod
    def shell(cls):
        pygame.display.quit()
        pygame.init()
        cls.loop_mode_shelled = True


    @classmethod
    def start_x(cls, hdmi=False):
        if os.path.isfile(START_X_FILE):
            if hdmi:
                subprocess.call(Command.StartXHdmi)
            else:
                subprocess.call(Command.StartXTft)
            return True
        return False

    @classmethod
    def restore(cls):
        send_wake_command()
        if Defaults.tft_type is not DISP22NT:
            pygame.mouse.set_visible(False)
        Displays.screen = pygame.display.set_mode(Defaults.tft_size)
        return_display = cls.get_last_core_display(Displays.shelled)
        return_display.force_refresh = True
        Displays.show(return_display)
        cls.loop_mode_shelled = False


    @classmethod
    def on_shutdown(cls, signum, frame):
        cls.shutdown(Shutdown.Normal if signum is signal.SIGINT else Shutdown.Terminate)


    ##################################################################################
    # GET_LAST_CORE_DISPLAY
    ##################################################################################
    # This method iterates backwards from the current display to find the last display
    # up the chain that is of class Display or Menu.   This is used when closing a
    # display or splash to esure the close happens back to a core display type (not
    # another splash or dialog) so that dialogs and splashes could be chained together
    # and still "closed' back to a core display.
    @classmethod
    def get_last_core_display(cls, start=None):
        previous = cls.current.last if start is None else start
        while previous is not None:
            if previous.is_core:
                return previous
            previous = previous.last
        return cls.initial


    ##################################################################################
    # DISPLAYS INITIALIZE METHOD
    ##################################################################################
    @classmethod
    def initialize(cls, tft_type, global_background_color=None, global_border_width=None, global_border_color=None,
                   global_font=None, global_font_size=None, global_font_color=None, global_font_h_padding=None,
                   global_font_v_padding=None, global_font_h_align=None, global_font_v_align=None):

        # Set the defaults based on the resolution of the display.  Fonts are scaled
        # using the font resolutions setting which provides similar sized fonts for
        # both the small and large displays.
        Defaults.set_defaults(tft_type, global_background_color=global_background_color,
                              global_border_width=global_border_width, global_border_color=global_border_color,
                              global_font=global_font, global_font_size=global_font_size,
                              global_font_color=global_font_color, global_font_h_padding=global_font_h_padding,
                              global_font_v_padding=global_font_v_padding, global_font_h_align=global_font_h_align,
                              global_font_v_align=global_font_v_align)
        # Create the internally used splash screens.  First one is the exit screen splash
        cls.menus[SplashBuiltIn.Exit] = Splash([
            SplashLine("MENU CLOSING", Defaults.default_splash_font_size_title),
            SplashLine("Please wait for a few seconds.", Defaults.default_splash_font_size)], Color.Green,
            timeout=Defaults.DEFAULT_SPLASH_TIMEOUT_SHORT)
        # This creates the information screen splash used to pass non-critical information
        cls.menus[SplashBuiltIn.Info] = Splash([
            SplashLine("ATTENTION", Defaults.default_splash_font_size_title),
            SplashLine("Unspecifed Information", Defaults.default_splash_font_size)], Color.Blue)
        # This creates the error screen splash used to indicate an error.
        cls.menus[SplashBuiltIn.Error] = Splash([
            SplashLine("ERROR", Defaults.default_splash_font_size_title),
            SplashLine("Closing down menu.  Please Wait...", Defaults.default_splash_font_size)], Color.Red)
        # This creates the error screen splash used to indicate an warning
        cls.menus[SplashBuiltIn.Warning] = Splash([
            SplashLine("WARNING", Defaults.default_splash_font_size_title),
            SplashLine("Unspecified Warning.", Defaults.default_splash_font_size)], Color.Orange,
            timeout=Defaults.DEFAULT_SPLASH_TIMEOUT_MEDIUM)
        # This creates the error screen splash used to indicate an low battery shutdown
        cls.menus[SplashBuiltIn.Battery] = Splash([
            SplashLine("LOW BATTERY", Defaults.default_splash_font_size_title, Color.Black),
            SplashLine("System will shut down shortly.", Defaults.default_splash_font_size, Color.Black)],
            Color.Yellow, timeout=Defaults.DEFAULT_SPLASH_TIMEOUT_LONG)
        # Initialize touchscreen drivers
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
        os.environ["SDL_MOUSEDRV"] = "TSLIB"
        # Initialize pygame and hide mouse if not using a non-touch display
        pygame.init()
        if Defaults.tft_type is not DISP22NT:
            pygame.mouse.set_visible(False)
        logger.info("Intitialized - %s", "Dan")
        cls.initialized = True


    ##################################################################################
    # DISPLAYS START METHOD
    ##################################################################################
    @classmethod
    def start(cls, initial_menu, backlight_method=None, backlight_steps=None, backlight_default=None,
              backlight_restore_last=False, button_callback=None, confirm_exit=False,
              power_gpio=None, battery_gpio=None):
        # Make sure start process has not already started.
        if cls.started:
            return
        cls.started = True
        shutdown = False
        down_button = 0
        down_time = None
        exit_splash = None
        error_message = "No Errors"
        # Make sure initialization has been run
        if not cls.initialized or Defaults.tft_type is None:
            cls.started = False
            raise NotInitializedException("Displays not initialized.  Use initiazlie() method before start().")
        # Add signals for shutdown from OS
        signal.signal(signal.SIG_IGN, cls.on_shutdown)
        signal.signal(signal.SIGINT, cls.on_shutdown)
        signal.signal(signal.SIGTERM, cls.on_shutdown)
        # Set display mode in pygame and set
        cls.screen = pygame.display.set_mode(Defaults.tft_size)
        try:
            # Create TFTButtons
            tft_buttons = Buttons(Defaults.tft_type, backlight_method=backlight_method, backlight_steps=backlight_steps,
                                  backlight_default=backlight_default, backlight_restore_last=backlight_restore_last,
                                  button_callback=button_callback, power_gpio=power_gpio, battery_gpio=battery_gpio)
            # Show and set initial menu
            Displays.initial = initial_menu
            Displays.show(initial_menu)
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
                                pass
                            else:
                                pos = pygame.mouse.get_pos()
                                down_button = cls.current.process_down_button(cls.current.process_location(pos))
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
                                    Backlight.screen_wake()
                                pos = pygame.mouse.get_pos()
                                cls.current.process_up_button(down_button)
                                button_id = cls.current.process_location(pos)
                                # if the up button was the same as the down button, then process
                                # the button.
                                if button_id == down_button:
                                    # Get the next menu and any associated data from the
                                    # process_button methond, then call Displays.show.  If the
                                    # menu is the same, it will not be re-rendered unless the
                                    # force_render flag is set - this allows for the Splash and
                                    # Dialog items to have changable text
                                    if time.time() - down_time > Times.RightClick or event.button == MouseButton.Right:
                                        button_type = MouseButton.Right
                                    else:
                                        button_type = MouseButton.Left
                                    next_menu, next_data = cls.current.process_button(button_id, button_type)
                                    Displays.show(next_menu, next_data)
                                # Reset the down button.
                                down_button = 0
                        elif event.type == KEYDOWN:
                            Timer.reset()
                        elif event.type == KEYUP:
                            Timer.reset()
                            if Backlight.method == BacklightMethod.NoBacklight or Backlight.is_screen_sleeping():
                                Backlight.screen_wake()
                            # Allow escape key to exit menu application
                            if event.key == K_ESCAPE:
                                cls.loop = False
                    # Check for expired timer.  If so, execute all functions in the display's
                    # timeout_function.
                    if Timer.is_expired():
                        if cls.current.timeout_function is not None:
                            for function in cls.current.timeout_function:
                                function()
                    # If the display has a headder attribute, call header update which will take
                    # care of refreshing the header if necessary
                    if hasattr(cls.current, Attributes.Header) and cls.current.header is not None:
                        cls.current.header.update(cls.current)
                    if hasattr(cls.current, Attributes.Footer) and cls.current.footer is not None:
                        cls.current.footer.update(cls.current)
                else:
                    for event in pygame.event.get():
                        # Mouse up or release on screen
                        if event.type == MOUSEBUTTONDOWN:
                            down_time = time.time()
                        if event.type == MOUSEBUTTONUP:
                            if time.time() - down_time > Times.RightClick:
                                Displays.restore()
                if tft_buttons.is_low_battery():
                    exit_splash = SplashBuiltIn.Battery
                    cls.shutdown(Shutdown.Shutdown)
                # Sleep for a bit
                time.sleep(Times.SleepLoop)
            cls.shutdown(Shutdown.Normal)
        # Catch Ctl-C Exit so error is not displayed
        except KeyboardInterrupt:
            # Keeps error from displaying when CTL-C is pressed
            print(""),
        # Catch other Error
        except Exception, e:
            # If we have an error,
            exit_splash = SplashBuiltIn.Error
            error_message = unicode(e)
            splash_data = [SplashLine("ERROR", Defaults.default_splash_font_size_title),
                           SplashLine(error_message, Defaults.default_splash_font_size, wrap_text=True)]
            cls.shutdown(Shutdown.Normal, exit_splash, splash_data)


##################################################################################
# BASELINE LINE CLASS
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
    def render(self, background_color = None):
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
            try:
                wrapped_text = wrap_text(self.font, self.text if self.text is not None else "",
                                        Defaults.tft_width - (self.font_h_padding * 2)
                                        if not hasattr(Displays.current, "border_width")
                                        else Defaults.tft_width - ((Displays.current.border_width +
                                                                    self.font_h_padding)* 2) )
            except Exception, e:
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
                        left = surface_width - 1 - wrapped_text[2][index]
                    else:
                        left = (surface_width / 2) - (wrapped_text[2][index] / 2)
                    try:
                        self.font.render_to(text_surface, (left, top), wrapped_text[0][index], fgcolor=self.font_color)
                    except Exception, e:
                        pass
                    text_top += wrapped_text[1][index] + self.font_v_padding
                return text_surface, text_surface.get_rect()


##################################################################################
# TFTMENU TEXTLINE CLASS
##################################################################################
class TextLine(BaseLine):

    ##################################################################################
    # TEXTLINE INIT METHOD
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(TextLine, self).__init__(text, font_size, font_color, font, font_style,
                                       font_h_align, font_h_padding, font_v_align, font_v_padding, font_pad, wrap_text)
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
# TFTMENU SPLASHLINE CLASS
##################################################################################
class SplashLine(BaseLine):

    ##################################################################################
    # SPLASHLINE INIT METHOD
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(SplashLine, self).__init__(text, font_size, font_color, font, font_style,
                                       font_h_align, font_h_padding, font_v_align, font_v_padding, font_pad, wrap_text)
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
# TFTMENU DIALOGLINE CLASS
##################################################################################
class DialogLine(BaseLine):

    ##################################################################################
    # DIALOGLINE INIT METHOD
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(DialogLine, self).__init__(text, font_size, font_color, font, font_style,
                                       font_h_align, font_h_padding, font_v_align, font_v_padding, font_pad, wrap_text)
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
# TFTMENU HEADERLINE CLASS
##################################################################################
class HeadFootLine(BaseLine):

    ##################################################################################
    # HEADERLINE INIT METHOD
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(HeadFootLine, self).__init__(text, font_size, font_color, font, font_style,
                                           font_h_align, font_h_padding, font_v_align, font_v_padding, font_pad, wrap_text)
        if self.font is None:
            self.font = Defaults.default_header_font
        if self.font_color is None:
            self.font_color = Defaults.default_header_font_color
        if self.font_size is None:
            self.font_size = Defaults.default_header_font_size
        if self.font_style is None:
            self.font_style = pygame.freetype.STYLE_NORMAL
        if self.font_h_align is None:
            self.font_h_align = Defaults.default_header_font_h_align
        if self.font_v_align is None:
            self.font_v_align = Defaults.default_header_font_v_align
        if self.font_h_padding is None:
            self.font_h_padding = Defaults.default_header_font_h_padding
        if self.font_v_padding is None:
            self.font_v_padding = Defaults.default_header_font_v_padding


##################################################################################
# TFTMENU BUTTONLINE CLASS
##################################################################################
class ButtonLine(BaseLine):

    ##################################################################################
    # BUTTONLINE INIT METHOD
    ##################################################################################
    def __init__(self, text=None, font_size=None, font_color=None, font=None, font_style=None,
                 font_h_align=None, font_h_padding=None, font_v_align=None, font_v_padding=None, font_pad=True,
                 wrap_text=False):
        super(ButtonLine, self).__init__(text, font_size, font_color, font, font_style,
                                       font_h_align, font_h_padding, font_v_align, font_v_padding, font_pad, wrap_text)
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
class Action(object):
    action = None
    data = None
    render_data = None

    ##################################################################################
    # ACTION INIT METHOD
    ##################################################################################
    def __init__(self, action=DisplayAction.NoAction, data=None, render_data=None):
        self.action = action
        self.data = data
        self.render_data = render_data


##################################################################################
# TFTMENU DISPLAY CLASS
##################################################################################
# Base Class for all displays in the menu system.
class Display(object):
    background_color = None
    border_color = None
    border_width = 0
    buttons = []
    actions = []
    timeout = 0
    timeout_function = None
    last = None
    force_refresh = False
    is_core = False


    ##################################################################################
    # DISPLAY INIT METHOD
    ##################################################################################
    def __init__(self, background_color=Defaults.default_background_color,
                 border_color=Defaults.default_border_color, border_width=None,
                 buttons=None, actions=None, timeout=Defaults.default_timeout, timeout_function=None):
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
        self.buttons = array_single_none(buttons)
        self.actions = array_single_none(actions)
        self.timeout = timeout
        self.timeout_function = merge(Displays.timeout_sleep, timeout_function)
        if self.border_width is None:
            self.border_width = Defaults.default_border_width
        self.is_core = True


    ##################################################################################
    # DISPLAY RENDER METHOD
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
    def render_buttons(self):
        for button in self.buttons:
            if button is not None:
                button.render()


    ##################################################################################
    # DISPLAYS PROCESS_LOCATION METHOD
    ##################################################################################
    def process_location(self, position):
        x = position[0]
        y = position[1]
        hit = 0
        count = 0
        for menuButton in self.buttons:
            count += 1
            if x >= menuButton.x and x <= menuButton.x + menuButton.width and\
                    (y >= menuButton.y and (y <= menuButton.y + menuButton.height)):
                hit = count
                break
        return hit


    ##################################################################################
    # DISPLAYS PROCESS_DOWN_BUTTON METHOD
    ##################################################################################
    def process_down_button(self, button_index):
        if button_index == 0:
            return button_index
        button = self.buttons[button_index - 1]
        if button is not None:
            if not (isinstance(Displays.current, Dialog) and Displays.current.dialog_type is DialogStyle.FullScreenOk):
                buttonRect = button.render(True)
                if buttonRect:
                    pygame.display.update(buttonRect)
            return button_index
        else:
            return 0


    ##################################################################################
    # DISPLAYS PROCESS_UP_BUTTON METHOD
    ##################################################################################
    def process_up_button(self, button_index):
        if button_index == 0:
            return
        button = self.buttons[button_index - 1]
        if button is not None:
            buttonRect = button.render()
        if buttonRect:
            pygame.display.update(buttonRect)


    ##################################################################################
    # DISPLAYS PROCESS_BUTTON METHOD
    ##################################################################################
    def process_button(self, button_index, button_type):
        if button_index == 0:
            return self, None
        button = self.buttons[button_index - 1]
        if (button.action_right is None or button_type == MouseButton.Left):
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
            if action_data is not None and len(action_data) > 0 and Displays.menus.has_key(action_data):
                new_menu = Displays.menus[action_data]
        elif action == DisplayAction.Back:
            new_menu = Displays.get_last_core_display()
            if new_menu is None:
                if Displays.initial is not None:
                    new_menu = Displays.initial
                else:
                    Displays.shutdown(Shutdown.Normal)
        elif action == DisplayAction.Exit:
            Displays.loop = False
        elif action == DisplayAction.Function:
            if action_data is not None and action_data:
                return_val = action_data(self, button)
                if return_val is not None:
                    if isinstance(return_val, Display):
                        new_menu = return_val
        elif action == DisplayAction.Sleep:
            Backlight.screen_sleep()
        elif action == DisplayAction.LightUp:
            Backlight.backlight_up()
        elif action == DisplayAction.LightDown:
            Backlight.backlight_down()
        elif action == DisplayAction.Shell:
            if Defaults.tft_type is DISP22NT:
                new_menu = Displays.menus[SplashBuiltIn.Warning]
                action_render_data = [SplashLine("WARNING", Defaults.default_splash_font_size_title),
                                      SplashLine("Shell not permitted on non-touch display", wrap_text=True)]
            else:
                Displays.shelled = self
                Displays.shell()
        elif action == DisplayAction.Reboot:
            Displays.shutdown(Shutdown.Reboot)
        elif action == DisplayAction.Shutdown:
            Displays.shutdown(Shutdown.Shutdown)
        elif action == DisplayAction.StartX:
            result = Displays.start_x(action_data)
            if result is True:
                pass
            else:
                new_menu = Displays.menus[SplashBuiltIn.Warning]
                action_render_data = [SplashLine("WARNING", Defaults.default_splash_font_size_title),
                                      SplashLine("GUI is not installed on in expected location.", wrap_text=True)]
        elif action == DisplayAction.Execute:
            run_cmd(action_data)
        return new_menu, action_render_data


##################################################################################
# TFTMENU MENU CLASS
##################################################################################
class Menu(Display):
    header = None
    footer = None

    ##################################################################################
    # MENU INIT METHOD
    ##################################################################################
    def __init__(self, background_color=Defaults.default_background_color,
                 border_color=Defaults.default_border_color, border_width=None, buttons=None, actions= None,
                 timeout=Defaults.default_timeout, timeout_function=None, header=None, footer=None):
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
        self.buttons = array_single_none(buttons)
        self.actions = array_single_none(actions)
        self.timeout = timeout
        self.timeout_function = merge(Displays.timeout_sleep, timeout_function)
        self.buttons = array_single_none(buttons)
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
class Splash(Display):
    
    ##################################################################################
    # SPLASH INIT METHOD
    ##################################################################################
    def __init__(self, text=None, background_color=Defaults.default_splash_background_color,
                 timeout=Defaults.default_splash_timeout):
        self.text = array_single_none(text)
        self.background_color = background_color
        self.timeout = timeout
        self.timeout_function = [Displays.timeout_close]


    ##################################################################################
    # SPLASH RENDER METHOD
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
            render_text = self.text
        if render_text:
            splash_text_tuples = []
            splash_text_height = 0
            last_text_height = 0
            text_v_align = None
            for text_item in render_text:
                if (text_item.text is None):
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
            splash_text_offset = 0
            if text_v_align is not TextVAlign.Top:
                splash_text_height -= render_text[-1].font_v_padding
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
class Dialog(Display):
    dialog_type = DialogStyle.Ok
    use_menu_timeout = False
    use_menu_colors = False


    ##################################################################################
    # DIALOG INIT METHOD
    ##################################################################################
    def __init__(self, text=None, dialog_type=DialogStyle.Ok, background_color=Defaults.default_dialog_background_color,
                 border_color=Defaults.default_dialog_border_color, border_width=None,
                 actions=None, buttons=None, timeout=Defaults.default_dialog_timeout, timeout_function=None,
                 use_menu_timeout=False, use_menu_colors=False):
        self.text = array_single_none(text)
        self.dialog_type = dialog_type
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
        self.buttons = array_single_none(buttons)
        self.actions = array_single_none(actions)
        self.timeout = timeout
        self.timeout_function = merge(Displays.timeout_sleep, timeout_function)
        self.use_menu_timeout = use_menu_timeout
        self.use_menu_colors = use_menu_colors
        if self.border_width is None:
            self.border_width = Defaults.default_border_width


    ##################################################################################
    # DIALOG RENDER METHOD
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
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.Bottom1x1, names=[""],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            elif self.dialog_type == DialogStyle.OkLeft:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.BottomLeft1x1, names=[""],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            elif self.dialog_type == DialogStyle.OkRight:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.BottomRight1x1, names=[""],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            elif self.dialog_type == DialogStyle.OkFullScreen:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.BottomFullWidth1x1, names=[""],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_background_color)
            else:
                self.buttons = tfttemplates.get_buttons(ButtonTemplate.Bottom2x1, names=[DialogButtonText.OK, None],
                                                        actions=self.actions, background_color=button_background_color,
                                                        border_color=button_border_color)
        # Draw Borders and Background
        Displays.screen.fill(display_background_color)
        draw_true_rect(Displays.screen, display_border_color, 0, 0, Defaults.tft_width - 1, Defaults.tft_height - 1,
                       display_border_width)
        if not self.buttons or self.dialog_type == DialogStyle.FullScreenOk:
            dialog_text_area_height = (Defaults.tft_height) - display_border_width
        else:
            button_pos = get_buttons_start_height(self.buttons)
            if button_pos > Defaults.tft_height - (display_border_width * 2):
                dialog_text_area_height = Defaults.tft_height - (display.border_width * 2)
            else:
                dialog_text_area_height = button_pos - display_border_width
            #dialog_text_area_height = get_buttons_start_height(self.buttons)
        if data is not None:
            render_text = array_single_none(data)
        else:
            render_text = self.text
        if render_text:
            dialog_text_tuples = []
            dialog_text_height = 0
            last_text_height = 0
            text_v_align = None
            for text_item in render_text:
                if (text_item.text is None):
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
            dialog_text_offset = 0
            if text_v_align is not TextVAlign.Top:
                dialog_text_height -= render_text[-1].font_v_padding
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
        # Set the Screen Timeout if using the previous Menu's timeout
        if core_display is not None and self.use_menu_timeout:
            timeout = core_display.timeout
        else:
            timeout = self.timeout
        Timer.timeout(timeout)
        Backlight.screen_wake()


##################################################################################
# TFTMENU HEADER CLASS
##################################################################################
class Header(object):
    text = None
    data = None
    type = 0
    height = 0
    refresh = None
    last_update = None
    location = None

    ##################################################################################
    # HEADER INIT METHOD
    ##################################################################################
    def __init__(self, text=None, data=None, type=HeadFootType.NoDisplay, height=None, refresh=None):
        if text is None:
            self.text = HeadFootLine(None)
        elif not isinstance(text, HeadFootLine):
            self.text = HeadFootLine(unicode(text))
        else:
            self.text = text
        self.type = type
        self.data = data
        self.height = height
        self.refresh = refresh
        self.location = HeadFootLocation.Top
        # if self.height is None:
        #     self.height = Defaults.default_header_height
        if self.refresh is None:
            if self.type == HeadFootType.Date:
                self.refresh = DisplayHeaderRefresh.Day
            elif self.type == HeadFootType.Time12 or self.type == HeadFootType.Time24 or \
                            self.type == HeadFootType.DateTime12 or \
                            self.type == HeadFootType.DateTime24:
                self.refresh = DisplayHeaderRefresh.Minute
            else:
                self.refresh = DisplayHeaderRefresh.NoRefresh


    ##################################################################################
    # HEADER (AND FOOTER) RENDER METHOD
    ##################################################################################
    def render(self, display, clear=False):
        # Get Header Text based on type.  If HeadFootType.UserText, nothing changes
        if self.type == HeadFootType.NoDisplay:
            return
        elif self.type == HeadFootType.Date:
            self.text.text = time.strftime("%B %d, %Y")
        elif self.type == HeadFootType.Time12:
            self.text.text = time.strftime("%-I:%M %p")
        elif self.type == HeadFootType.Time24:
            self.text.text = time.strftime("%H:%M")
        elif self.type == HeadFootType.DateTime12:
            self.text.text = time.strftime("%m/%d/%y  %-I:%M %p")
        elif self.type == HeadFootType.DateTime24:
            self.text.text = time.strftime("%d/%m/%y  %H:%M")
        elif self.type == HeadFootType.DateTimeCustom:
            if not self.data is None:
                self.text.text = time.strftime(self.data)
        elif self.type == HeadFootType.HostName:
            host_name = run_cmd("hostname")
            if self.text.text:
                self.text.text = self.text.text.format(host_name[:-1])
            else:
                self.text.text =  host_name[:-1]
        elif self.type == HeadFootType.IpAddress:
            ip_address = get_ip_address()
            if self.text.text:
                self.text.text = self.text.text.format(ip_address)
            else:
                self.text.text = ip_address
        elif self.type == HeadFootType.UserFunction:
            if self.data is not None:
                self.text.text = unicode(self.data(self))
        elif self.type is not HeadFootType.UserText:
            return
        if self.text.text is None:
            self.text.text = ""
        # Draw Header
        headfoot_surface, headfoot_font_rect = self.text.render(display.background_color)
        headfoot_text_width = headfoot_font_rect.width
        headfoot_text_height = headfoot_font_rect.height
        headfoot_top = 0
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

        if self.location is HeadFootLocation.Top:
            headfoot_offset = display.border_width
        else:
            headfoot_offset = button_pos
        # Handle horizontal alignment
        if self.text.font_h_align == TextHAlign.Left:
            headfoot_text_left = display.border_width + self.text.font_h_padding
        elif self.text.font_h_align == TextHAlign.Right:
            headfoot_text_left = Defaults.tft_width -  headfoot_text_width - display.border_width - \
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
    def update(self, display):
        if self.refresh == DisplayHeaderRefresh.NoRefresh:
            return
        curTime = int(time.time())
        localTime = time.localtime(curTime)
        useTwoSecondRange = False
        # Set Header Refresh if Date/Time is used
        if self.refresh == DisplayHeaderRefresh.Day:
            if localTime[TimeStruct.Hour] != 0 or localTime[TimeStruct.Minute] != 0 or\
                            localTime[TimeStruct.Second] != 0:
                return
            useTwoSecondRange = True
        elif self.refresh == DisplayHeaderRefresh.Hour:
            if localTime[TimeStruct.Minute] != 0 or localTime[TimeStruct.Second] != 0:
                return
            useTwoSecondRange = True
        elif self.refresh == DisplayHeaderRefresh.Minute:
            if localTime[TimeStruct.Second] != 0:
                return
            useTwoSecondRange = True
        else:
            useTwoSecondRange = False
        if useTwoSecondRange:
            if self.last_update == curTime or self.last_update == curTime - 1:
                return
        else:
            if self.last_update == curTime:
                return
        self.render(display, True)
        self.last_update = curTime


##################################################################################
# TFTMENU FOOTER CLASS
##################################################################################
class Footer(Header):

    ##################################################################################
    # FOOTER INIT METHOD
    ##################################################################################
    def __init__(self, text=None, data=None, type=HeadFootType.NoDisplay, height=None, refresh=None):
        super(Footer, self).__init__(text, data, type, height, refresh)
        self.location = HeadFootLocation.Bottom
                     
                     
##################################################################################
# TFTMENU BUTTON CLASS
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
        if self.width is None:
            self.width = Defaults.default_button_width
        if self.height is None:
            self.width = Defaults.default_button_height
        if self.border_width is None:
            self.border_width = Defaults.default_button_border_width


    ##################################################################################
    # BUTTON RENDER METHOD
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
            buttonTextLeft = self.x + self.border_width + self.text.font_h_padding
        elif self.text.font_h_align == TextHAlign.Right:
            buttonTextLeft = (self.x + self.width) - self.border_width - button_text_width - self.text.font_h_padding
        else:
            buttonTextLeft = (self.x + (self.width / 2)) - (button_text_width / 2)
        # Handle vertical alignment
        if self.text.font_v_align == TextVAlign.Top:
            buttonTextTop = self.y + self.border_width + self.text.font_v_padding
        elif self.text.font_v_align == TextVAlign.Bottom:
            buttonTextTop = (self.y + self.height) - self.border_width - button_text_height - self.text.font_v_padding
        else:
            buttonTextTop = (self.y + (self.height / 2)) - (button_text_height / 2)
        buttonTextRect = button_surface.get_rect(left=buttonTextLeft, top=buttonTextTop)
        # Blit the text on the screen
        Displays.screen.blit(button_surface, buttonTextRect)
        return button_rect
