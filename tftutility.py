#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
import argparse
import logging
import os
import socket
import subprocess

import pygame
import pygame.freetype

##################################################################################
# CONFIGURE LOGGING
##################################################################################
# Creates the logger and allows for use of command line parameter when running a
# menu display of --log followed by the level of logging.   This parameter will be
# WARNING if not passed in or an invalid parameter is used
# Create Logger with 'tftmenu' name.
##################################################################################
logger = logging.getLogger("tftmenu")
logger.setLevel(logging.DEBUG)
# Create File Handler which logs all messages
file_handler = logging.FileHandler("tftmenu.log")
file_handler.setLevel(logging.DEBUG)
parser = argparse.ArgumentParser()
parser.add_argument("--log", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="WARNING")
try:
    args = parser.parse_args()
    logging_level = getattr(logging, args.log.upper(), None)
except AttributeError, e:
    logger.warning("Invalid command line attribute passed in.  Setting console logging level to WARNING")
    logging_level = getattr(logging, "WARNING", None)
# Create Console Handler with the level set to WARNING or that passed in from the
# command-line given.
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging_level)
# Create Formatter and add it to the Handlers
formatter = logging.Formatter("%(levelname)-8s %(asctime)s.%(msecs)-003d %(module)s:%(lineno)d - %(message)s",
                              "%Y/%m/%d %H:%M:%S")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
# Add the Handlers to the Logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


##################################################################################
# RUN CMD METHOD
##################################################################################
# Method to run a command an return the output of the commend in a string or a
# list. This code was modified from the code in garthVH and re4son branch located
# at https://github.com/garthvh/pitftmenu and https://github.com/Re4son/pitftmenu
# respectively
##################################################################################
def run_cmd(cmd):
    if isinstance(cmd, list):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    else:
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    return output


##################################################################################
# IS ROOT METHOD
##################################################################################
# Method that returns True if the EUID (Effective User ID) is 0 (root) and False
# if not reboot.
##################################################################################
def is_root():
    return os.geteuid() is 0


##################################################################################
# TFT TYPE CONSTANTS
##################################################################################
DISP22NT   = AF_2315 = NONE22 = 1  # GPIOs 17,22,23,27,(18)
DISP24R    = AF_2455 = RES24  = 2  # GPIOs 16,13,12,6,5,(18)
DISP28R    = AF_1601 = RES28  = 3  # GPIOs 23,22,21/27,18,(None)
DISP28C    = AF_1983 = CAP28  = 4  # GPIOs 23,22,21/27,17,(18)
DISP28RP   = AF_2298 = RES28P = 5  # GPIOs 17,22,23,27,(18)
DISP28CP   = AF_2423 = CAP28P = 6  # GPIOs 17,22,23,27,(18)
DISP32RP   = AF_2626 = RES32P = 7  # GPIOs 22,23,17,27,(18)
DISP35R    = AF_2097 = RES35  = 8  # GPIOs (18)
DISP35RP   = AF_2441 = RES35P = 9  # GPIOs (18)


##################################################################################
# SCREEN CONSTANTS
##################################################################################
# Used to wake the Pi from its own sleep state.
##################################################################################
class Screen:
    Tty         = "tty{0}".format(run_cmd("fgconsole")[:-1])
    WakeCommand = "printf \033[13]"
    WakePipe    = "sudo tee /dev/{0} > /dev/null".format(Tty)


##################################################################################
# COMMAND CLASS CONSTANTS
##################################################################################
# Constants used to shutdown, reboot or start X.
##################################################################################
class Command:
    Shutdown   = "sudo shutdown -h now"
    Reboot     = "sudo shutdown -r now"
    StartXHdmi = "FRAMEBUFFER=/dev/fb0 startx"
    StartXTft  = "FRAMEBUFFER=/dev/fb1 startx"


##################################################################################
# SHUTDOWN CLASS CONSTANTS
##################################################################################
# Constants used during calls to Displays.shutdown().  Normal indicates a user
# initiated exit by CTL-C or Escape (when not shelled), Error indicates that an
# error has determined the Displays need to be shut down, Terminate when a signal
# indicating the pi or python is being shutdown or killed.  Reboot and Shutdown
# indicate to perform a normal shutdown then either reboot or shutdown the pi
# respectively.
##################################################################################
class Shutdown:
    Normal    = 0
    Error     = 1
    Terminate = 2
    Reboot    = 4
    Shutdown  = 5


##################################################################################
# DIALOG BUTTON TEXT CLASS CONSTANTS
##################################################################################
# Standard text for dialog buttons.   Provides a one stop place to set these
# should alternate text be desired.
##################################################################################
class DialogButtonText:
    Yes    = "Yes"
    No     = "No"
    OK     = "OK"
    Cancel = "Cancel"


##################################################################################
# ATTRIBUTES CLASS CONSTANTS
##################################################################################
# Names of attributes used by calls to hasattr()
##################################################################################
class Attributes:
    Header = "header"
    Footer = "footer"


##################################################################################
# COLOR DEFINITIONS
##################################################################################
# Some standard colors defined for use.  Can easily be extended or modified.
##################################################################################
class Color:
    # Color     R    G    B
    White      = (255, 255, 255)
    Pink       = (255, 192, 203)
    DarkPink   = (255,105,180)
    Red        = (255, 0, 0)
    DarkRed    = (139, 0, 0)
    Maroon     = (128, 0, 0)
    Orange     = (255, 128, 0)
    DarkOrange = (255, 69, 0)
    Yellow     = (255, 255, 0)
    Gold       = (184, 134,11)
    Olive      = (128, 128, 0)
    Lime       = (0, 255, 0)
    Green      = (0, 128, 0)
    DarkGreen  = (0, 80, 0)
    Cyan       = (0, 255, 255)
    Teal       = (0, 128, 128)
    Blue       = (0, 0, 255)
    Sky        = (0, 191, 255)
    Navy       = (0, 0, 128)
    Purple     = (128, 0, 128)
    Orchid     = (153, 50, 204)
    Magenta    = (255, 0, 255)
    Silver     = (192, 192, 192)
    Gray       = (128, 128, 128)
    Tan        = (210, 180, 140)
    Brown      = (139, 69, 19)
    Black      = (0, 0, 0)


##################################################################################
# BUTTON TEMPLATE CONSTANTS
##################################################################################
# Constants for the different button templates.  If additional templates are
# added, an additional item should also be added here.
##################################################################################
class ButtonTemplate:
    Header2x3          = 0
    HeaderFooter2x2    = 1
    Header3x3          = 2
    HeaderFooter3x2    = 3
    FullScreen2x4      = 4
    FullScreen3x4      = 5
    FullScreen4x4      = 6
    Bottom1x1          = 7
    BottomLeft1x1      = 8
    BottomRight1x1     = 9
    BottomFullWidth1x1 = 10
    Bottom2x1          = 11
    Bottom3x1          = 12
    FullScreenButton   = 13


##################################################################################
# BUTTON DIRECTION CONSTANTS
##################################################################################
# Constants for the direction the buttons are rendered.  Should cover all left/
# right and top/down combinations.
##################################################################################
class ButtonDirection:
    LeftRightTopBottom = 0
    LeftRightBottomTop = 1
    RightLeftTopBottom = 2
    RightLeftBottomTop = 3
    TopBottomLeftRight = 4
    TopBottomRightLeft = 5
    BottomTopLeftRight = 6
    BottomTopRightLeft = 7


##################################################################################
# BUTTON TUPLE CONSTANTS
##################################################################################
# Constants used for button tuple used by the TftTemplates module.
##################################################################################
class ButtonTuple:
    Columns        = 0
    Rows           = 1
    ColumnsStart   = 2
    RowsStart      = 3
    ColumnsSpacing = 4
    RowsSpacing    = 5
    Width          = 6
    Height         = 7


##################################################################################
# TIMES CONSTANTS
##################################################################################
# Changeable Parameters.  Should be good but can be changed if needed
##################################################################################
class Times:
    SleepLoop    = 0.05
    SleepShort   = 0.25
    SleepLong    = 1
    SwitchBounce = 400
    RightClick   = 0.750


##################################################################################
# BACKLIGHT METHOD CONSTANTS
##################################################################################
# Backlight Method to use.  Which one to use depends on what you want to do with
# the backlight, whether the backlight PWM is enabled (on certain PiTft displays),
# and what version of Raspian is being used (Jessie and Wheezy are supported).
##################################################################################
class BacklightMethod:
    NoBacklight = 0
    Pwm         = 1
    PwmBinary   = 2
    Stmpe       = 3
    Echo        = 4
    Echo252     = 5


##################################################################################
# DISPLAY RESOLUTION CONSTANTS
##################################################################################
# Constants indicating the two currently supported display resolutions.  All
# current Adafruit PiTft display and MOST third party displays use one of these
# two resolutions.
##################################################################################
class DisplayResolution:
    Small320x240 = 0
    Large480x320 = 1


##################################################################################
# DISPLAY ACTION CONSTANTS
##################################################################################
class DisplayAction:
    NoAction      = 0
    Display       = 1
    Back          = 2
    Exit          = 3
    Reboot        = 4
    Shutdown      = 5
    Function      = 6
    ScreenSleep   = 7
    BacklightUp   = 8
    BacklightDown = 9
    Shell         = 10
    StartX        = 11
    Execute       = 12


##################################################################################
#  ACTION FUNCTION CONSTANTS
##################################################################################
class GpioButtonAction:
    NoAction      = 0
    Display       = 1
    Exit          = 2
    Reboot        = 3
    Shutdown      = 4
    Function      = 5
    ScreenSleep   = 6
    ScreenWake    = 7
    ScreenToggle  = 8
    BacklightDown = 9
    BacklightUp   = 10
    Shell         = 11
    StartX        = 12
    Execute       = 13


##################################################################################
# MENU HEAD/FOOT CONSTANTS
##################################################################################
# Constants indicating the type of header or footer that should be displayed.  The
# NoDisplay will render a blank header, Date will render the long date, Time12 and
# Time24 will display time in Hours:Minutes format in either 12 (with AM/PM) or 24
# hour mode.  DateTime12 and DateTime24 will return the short date along with
# either 12 or 24 hour time.  DateTimeCustom will allow for a custom format to be
# passed in.  HostName and IpAddress will display the Pi's HostName or the Pi's IP
# Address.  UserText allows any specified user text to be passed in and
# UserFunction displays the result of a passed in function.  In addition to the
# header type, this will also help determine the header refresh rate
class HeadFootType:
    NoDisplay      = 0
    Date           = 1
    Time12         = 2
    Time24         = 3
    DateTime12     = 4
    DateTime24     = 5
    DateTimeCustom = 6
    HostName       = 7
    IpAddress      = 8
    UserText       = 9
    UserFunction   = 10


##################################################################################
# MENU HEAD/FOOT LOCATION CONSTANTS
##################################################################################
# The location of the header or footer.  Top is above the highest button, Below is
# under the lowest button.
##################################################################################
class HeadFootLocation:
    Top    = 0
    Bottom = 1


##################################################################################
# DISPLAY HEADER REFRESH CLASS CONSTANTS
##################################################################################
# Constants to determine the frequency of refreshes to the header or footer.  The
# All setting will update the header at the highest possible frequency.
##################################################################################
class DisplayHeaderRefresh:
    NoRefresh = 0
    Day       = 1
    Hour      = 2
    Minute    = 3
    Second    = 4
    All       = 5


##################################################################################
# SPLASH BUILT-INs
##################################################################################
# Constants containing the names of the built-in Splash displays.
##################################################################################
class SplashBuiltIn:
    Blank   = "Blank"
    Exit    = "Exit"
    Info    = "Info"
    Error   = "Error"
    Warning = "Warning"
    Battery = "LowBattery"


##################################################################################
# SPLASH MUTE LEVEL
##################################################################################
# Constant flags to allow for muting of specific levels of Splash displays.  They
# can be combined to create custom levels of muting.
##################################################################################
class SplashMuteLevel:
    NoMute  = 0
    Exit    = 1
    Info    = 2
    Warning = 4
    Error   = 8
    Battery = 16
    Quiet   = 31


##################################################################################
# TIME STRUCT CONSTANTS
##################################################################################
# Constants used for the date/time struct positions
##################################################################################
class TimeStruct:
    Year      = 0
    Month     = 1
    MonthDay  = 2
    Hour      = 3
    Minute    = 4
    Second    = 5
    DayOfWeek = 6
    DayofYear = 7
    IsDst     = 8


##################################################################################
# HORIZONTAL TEXT ALIGNMENT CONSTANTS
##################################################################################
# Constants for horizontal text alignment
##################################################################################
class TextHAlign:
    Left   = 0
    Center = 1
    Right  = 2


##################################################################################
# VERTICAL TEXT ALIGNMENT CONSTANTS
##################################################################################
# Constants for vertical text alignment
##################################################################################
class TextVAlign:
    Top    = 0
    Middle = 1
    Bottom = 2


##################################################################################
# TEXT TUPLE CONSTANTS
##################################################################################
# Constants for the indexes of the tuple use to set text positions.
##################################################################################
class TextTuple:
    Surface  = 0
    Width    = 1
    Height   = 2
    HAlign   = 3
    HPadding = 4
    VPadding = 5


##################################################################################
# DIALOG STYLE CONSTANTS
##################################################################################
# Constants for the types of dialog styles that can be created by the Dialog
# display class.  These determine buttons and button positions.
##################################################################################
class DialogStyle:
    Ok           = 0
    OkLeft       = 1
    OkRight      = 2
    OkFullScreen = 3
    OkCancel     = 4
    YesNo        = 5
    YesNoCancel  = 6
    FullScreenOk = 7
    Custom       = 8


##################################################################################
# MOUSE BUTTON CONSTANTS
##################################################################################
# Constants indicating the pygame mouse buttons
##################################################################################
class MouseButton:
    Left   = 1
    Middle = 2
    Right  = 3


##################################################################################
# DEFAULTS CLASS
##################################################################################
# Class for holding the defaults for the different displays and text lines.  Some
# of the parameters are adjusted based on the size of the tft in use.  Currently
# 240x320 and 320x480 screens are supported.
##################################################################################
class Defaults:
    ##################################################################################
    # DEFAULTS DEFAULT CONSTANTS
    ##################################################################################
    # Default constants that apply to all resolutions
    ##################################################################################
    DEFAULT_BACKGROUND_COLOR = Color.Black
    DEFAULT_BORDER_COLOR = Color.Blue
    DEFAULT_TIMEOUT = 0
    DEFAULT_TEXT_LINE_FONT_COLOR = Color.White
    DEFAULT_TEXT_LINE_FONT = None
    DEFAULT_TEXT_LINE_FONT_SIZE = 15
    DEFAULT_TEXT_LINE_FONT_ALIGN = TextHAlign.Center
    DEFAULT_TEXT_LINE_FONT_VALIGN = TextVAlign.Middle
    DEFAULT_HEADFOOT_FONT_COLOR = Color.White
    DEFAULT_HEADFOOT_FONT = None
    DEFAULT_HEADFOOT_FONT_SIZE = 30
    DEFAULT_HEADFOOT_FONT_ALIGN = TextHAlign.Center
    DEFAULT_HEADFOOT_FONT_VALIGN = TextVAlign.Middle
    DEFAULT_SPLASH_BACKGROUND_COLOR = Color.Black
    DEFAULT_SPLASH_FONT_COLOR = Color.White
    DEFAULT_SPLASH_FONT = None
    DEFAULT_SPLASH_FONT_SIZE_TITLE = 30
    DEFAULT_SPLASH_FONT_SIZE = 15
    DEFAULT_SPLASH_TIMEOUT_SHORT = 2
    DEFAULT_SPLASH_TIMEOUT_MEDIUM = 5
    DEFAULT_SPLASH_TIMEOUT_LONG = 15
    DEFAULT_SPLASH_FONT_ALIGN = TextHAlign.Center
    DEFAULT_SPLASH_FONT_VALIGN = TextVAlign.Middle
    DEFAULT_DIALOG_BACKGROUND_COLOR = Color.Black
    DEFAULT_DIALOG_BORDER_COLOR = Color.Blue
    DEFAULT_DIALOG_TIMEOUT = 0
    DEFAULT_DIALOG_FONT_COLOR = Color.White
    DEFAULT_DIALOG_FONT = None
    DEFAULT_DIALOG_FONT_SIZE_TITLE = 30
    DEFAULT_DIALOG_FONT_SIZE = 15
    DEFAULT_DIALOG_FONT_ALIGN = TextHAlign.Center
    DEFAULT_DIALOG_FONT_VALIGN = TextVAlign.Middle
    DEFAULT_BUTTON_BORDER_COLOR = Color.Blue
    DEFAULT_BUTTON_FONT_COLOR = Color.White
    DEFAULT_BUTTON_FONT = None
    DEFAULT_BUTTON_FONT_SIZE = 20
    DEFAULT_BUTTON_FONT_ALIGN = TextHAlign.Center
    DEFAULT_BUTTON_FONT_VALIGN = TextVAlign.Middle
    DEFAULT_TFT_TYPE = None

    ##################################################################################
    # DEFAULTS DEFAULT 320x240 CONSTANTS
    ##################################################################################
    # Default constants for the 320x240 resolution
    ##################################################################################
    DEFAULT_BORDER_WIDTH_320x240 = 4
    DEFAULT_TEXT_LINE_FONT_H_PADDING_320x240 = 6
    DEFAULT_TEXT_LINE_FONT_V_PADDING_320x240 = 8
    DEFAULT_SPLASH_BORDER_WIDTH_320x240 = 4
    DEFAULT_SPLASH_FONT_H_PADDING_320x240 = 6
    DEFAULT_SPLASH_FONT_V_PADDING_320x240 = 8
    DEFAULT_DIALOG_BORDER_WIDTH_320x240 = 4
    DEFAULT_DIALOG_FONT_H_PADDING_320x240 = 6
    DEFAULT_DIALOG_FONT_V_PADDING_320x240 = 8
    DEFAULT_HEADFOOT_FONT_H_PADDING_320x240 = 6
    DEFAULT_HEADFOOT_FONT_V_PADDING_320x240 = 8
    DEFAULT_BUTTON_FONT_H_PADDING_320x240 = 2
    DEFAULT_BUTTON_FONT_V_PADDING_320x240 = 2
    DEFAULT_BUTTON_BORDER_WIDTH_320x240 = 4
    DEFAULT_BUTTON_WIDTH_320x240 = 145
    DEFAULT_BUTTON_HEIGHT_320x240 = 54
    DEFAULT_WIDTH_320x240 = 320
    DEFAULT_HEIGHT_320x240 = 240
    DEFAULT_FONT_RESOLUTION_320x240 = 72

    ##################################################################################
    # DEFAULTS DEFAULT 480x320 CONSTANTS
    ##################################################################################
    # Default constants for the 480x320 resolution
    ##################################################################################
    DEFAULT_BORDER_WIDTH_480x320 = 6
    DEFAULT_TEXT_LINE_FONT_H_PADDING_480x320 = 7
    DEFAULT_TEXT_LINE_FONT_V_PADDING_480x320 = 7
    DEFAULT_SPLASH_BORDER_WIDTH_480x320 = 6
    DEFAULT_SPLASH_FONT_H_PADDING_480x320 = 6
    DEFAULT_SPLASH_FONT_V_PADDING_480x320 = 8
    DEFAULT_DIALOG_BORDER_WIDTH_480x320 = 6
    DEFAULT_DIALOG_FONT_H_PADDING_480x320 = 6
    DEFAULT_DIALOG_FONT_V_PADDING_480x320 = 6
    DEFAULT_HEADFOOT_FONT_H_PADDDING_480x320 = 6
    DEFAULT_HEADFOOT_FONT_V_PADDING_480x320 = 6
    DEFAULT_BUTTON_FONT_H_PADDING_480x320 = 3
    DEFAULT_BUTTON_FONT_V_PADDING_480x320 = 3
    DEFAULT_BUTTON_BORDER_WIDTH_480x320 = 6
    DEFAULT_BUTTON_WIDTH_480x320 = 225
    DEFAULT_BUTTON_HEIGHT_480x320 = 72
    DEFAULT_WIDTH_480x320 = 480
    DEFAULT_HEIGHT_480x320 = 320
    DEFAULT_FONT_RESOLUTION_480x320 = 108

    ##################################################################################
    # DEFAULTS DEFAULT PROPERTIES
    ##################################################################################
    default_background_color          = DEFAULT_BACKGROUND_COLOR
    default_border_color              = DEFAULT_BORDER_COLOR
    default_timeout                   = DEFAULT_TIMEOUT
    default_text_line_font_color      = DEFAULT_TEXT_LINE_FONT_COLOR
    default_text_line_font            = DEFAULT_TEXT_LINE_FONT
    default_text_line_font_size       = DEFAULT_TEXT_LINE_FONT_SIZE
    default_text_line_font_h_align    = DEFAULT_TEXT_LINE_FONT_ALIGN
    default_text_line_font_v_align    = DEFAULT_TEXT_LINE_FONT_VALIGN
    default_splash_background_color   = DEFAULT_SPLASH_BACKGROUND_COLOR
    default_splash_timeout            = DEFAULT_SPLASH_TIMEOUT_MEDIUM
    default_splash_font_color         = DEFAULT_SPLASH_FONT_COLOR
    default_splash_font               = DEFAULT_SPLASH_FONT
    default_splash_font_size_title    = DEFAULT_SPLASH_FONT_SIZE_TITLE
    default_splash_font_size          = DEFAULT_SPLASH_FONT_SIZE
    default_splash_font_h_align       = DEFAULT_SPLASH_FONT_ALIGN
    default_splash_font_v_align       = DEFAULT_SPLASH_FONT_VALIGN
    default_dialog_background_color   = DEFAULT_DIALOG_BACKGROUND_COLOR
    default_dialog_border_color       = DEFAULT_DIALOG_BORDER_COLOR
    default_dialog_timeout            = DEFAULT_DIALOG_TIMEOUT
    default_dialog_font_color         = DEFAULT_TEXT_LINE_FONT_COLOR
    default_dialog_font               = DEFAULT_TEXT_LINE_FONT
    default_dialog_font_size_title    = DEFAULT_DIALOG_FONT_SIZE_TITLE
    default_dialog_font_size          = DEFAULT_DIALOG_FONT_SIZE
    default_dialog_font_h_align       = DEFAULT_TEXT_LINE_FONT_ALIGN
    default_dialog_font_v_align       = DEFAULT_TEXT_LINE_FONT_VALIGN
    default_headfoot_font_color         = DEFAULT_HEADFOOT_FONT_COLOR
    default_headfoot_font               = DEFAULT_HEADFOOT_FONT
    default_headfoot_font_size          = DEFAULT_HEADFOOT_FONT_SIZE
    default_headfoot_font_h_align       = DEFAULT_HEADFOOT_FONT_ALIGN
    default_headfoot_font_v_align       = DEFAULT_HEADFOOT_FONT_VALIGN
    default_button_border_color       = DEFAULT_BUTTON_BORDER_COLOR
    default_button_font_color         = DEFAULT_BUTTON_FONT_COLOR
    default_button_font               = DEFAULT_BUTTON_FONT
    default_button_font_size          = DEFAULT_BUTTON_FONT_SIZE
    default_button_font_h_align       = DEFAULT_BUTTON_FONT_ALIGN
    default_button_font_v_align       = DEFAULT_BUTTON_FONT_VALIGN
    tft_type                          = DEFAULT_TFT_TYPE
    default_text_line_font_h_padding  = DEFAULT_TEXT_LINE_FONT_H_PADDING_320x240
    default_text_line_font_v_padding  = DEFAULT_TEXT_LINE_FONT_V_PADDING_320x240
    default_splash_border_width       = DEFAULT_SPLASH_BORDER_WIDTH_320x240
    default_splash_font_h_padding     = DEFAULT_SPLASH_FONT_H_PADDING_320x240
    default_splash_font_v_padding     = DEFAULT_SPLASH_FONT_V_PADDING_320x240
    default_dialog_border_width       = DEFAULT_DIALOG_BORDER_WIDTH_320x240
    default_dialog_font_h_padding     = DEFAULT_DIALOG_FONT_H_PADDING_320x240
    default_dialog_font_v_padding     = DEFAULT_DIALOG_FONT_V_PADDING_320x240
    default_headfoot_font_h_padding     = DEFAULT_HEADFOOT_FONT_H_PADDING_320x240
    default_headfoot_font_v_padding     = DEFAULT_HEADFOOT_FONT_V_PADDING_320x240
    default_button_font_h_padding     = DEFAULT_BUTTON_FONT_H_PADDING_320x240
    default_button_font_v_padding     = DEFAULT_BUTTON_FONT_V_PADDING_320x240
    default_button_border_width       = DEFAULT_BUTTON_BORDER_WIDTH_320x240
    default_button_width              = DEFAULT_BUTTON_WIDTH_320x240
    default_button_height             = DEFAULT_BUTTON_HEIGHT_320x240
    default_border_width              = DEFAULT_BORDER_WIDTH_320x240
    default_font_resolution           = DEFAULT_FONT_RESOLUTION_320x240
    tft_resolution                    = DisplayResolution.Small320x240
    tft_size = tft_width, tft_height  = DEFAULT_WIDTH_320x240, DEFAULT_HEIGHT_320x240

    @classmethod
    def set_defaults(cls, tft_type, global_background_color=None, global_border_width=None,
                     global_border_color=None, global_font=None, global_font_size=None, global_font_color=None,
                     global_font_h_padding=None, global_font_v_padding=None,
                     global_font_h_align=None, global_font_v_align=None):
        cls.tft_type = tft_type
        if (tft_type == DISP35R) or (tft_type == DISP35RP):
            cls.default_border_width              = Defaults.DEFAULT_BORDER_WIDTH_480x320
            cls.default_text_line_font_h_padding  = Defaults.DEFAULT_TEXT_LINE_FONT_H_PADDING_480x320
            cls.default_text_line_font_v_padding  = Defaults.DEFAULT_TEXT_LINE_FONT_V_PADDING_480x320
            cls.default_splash_border_width       = Defaults.DEFAULT_SPLASH_BORDER_WIDTH_480x320
            cls.default_splash_font_h_padding     = Defaults.DEFAULT_SPLASH_FONT_H_PADDING_480x320
            cls.default_splash_font_v_padding     = Defaults.DEFAULT_SPLASH_FONT_V_PADDING_480x320
            cls.default_dialog_border_width       = Defaults.DEFAULT_DIALOG_BORDER_WIDTH_480x320
            cls.default_dialog_font_h_padding     = Defaults.DEFAULT_DIALOG_FONT_H_PADDING_480x320
            cls.default_dialog_font_v_padding     = Defaults.DEFAULT_DIALOG_FONT_V_PADDING_480x320
            cls.default_headfoot_font_h_padding     = Defaults.DEFAULT_HEADFOOT_FONT_H_PADDDING_480x320
            cls.default_headfoot_font_v_padding     = Defaults.DEFAULT_HEADFOOT_FONT_V_PADDING_480x320
            cls.default_button_font_h_padding     = Defaults.DEFAULT_BUTTON_FONT_H_PADDING_480x320
            cls.default_button_font_v_padding     = Defaults.DEFAULT_BUTTON_FONT_V_PADDING_480x320
            cls.default_button_border_width       = Defaults.DEFAULT_BUTTON_BORDER_WIDTH_480x320
            cls.default_button_width              = Defaults.DEFAULT_BUTTON_WIDTH_480x320
            cls.default_button_height             = Defaults.DEFAULT_BUTTON_HEIGHT_480x320
            cls.default_font_resolution           = Defaults.DEFAULT_FONT_RESOLUTION_480x320
            cls.tft_resolution                    = DisplayResolution.Large480x320
            cls.tft_width                         = Defaults.DEFAULT_WIDTH_480x320
            cls.tft_height                        = Defaults.DEFAULT_HEIGHT_480x320
            cls.tft_size                          = (cls.tft_width, cls.tft_height)
        if global_background_color is not None:
            cls.default_background_color = global_background_color
            cls.default_splash_background_color = global_background_color
            cls.default_splash_background_color = global_background_color
        if global_border_width is not None:
            cls.default_border_width = global_border_width
            cls.default_dialog_border_width = global_border_width
            cls.default_button_border_width = global_border_width
        if global_border_color is not None:
            cls.default_border_color = global_border_color
            cls.default_dialog_border_color = global_border_color
            cls.default_button_border_color = global_border_color
        if global_font is None or isinstance(global_font, pygame.freetype.Font) or os.path.exists(global_font):
            cls.default_text_line_font = global_font
            cls.default_splash_font = global_font
            cls.default_dialog_font = global_font
            cls.default_headfoot_font = global_font
            cls.default_button_font = global_font
        if global_font_size is not None:
            cls.default_text_line_font_size = global_font_size
            cls.default_splash_font_size = global_font_size
            cls.default_dialog_font_size = global_font_size
            cls.default_headfoot_font_size = global_font_size
            cls.default_button_font_size = global_font_size
        if global_font_color is not None:
            cls.default_text_line_font_color = global_font_color
            cls.default_splash_font_color = global_font_color
            cls.default_dialog_font_color = global_font_color
            cls.default_headfoot_font_color = global_font_color
            cls.default_button_font_color = global_font_color
        if global_font_h_padding is not None:
            cls.default_text_line_font_h_padding = global_font_h_padding
            cls.default_splash_font_h_padding = global_font_h_padding
            cls.default_dialog_font_h_padding = global_font_h_padding
            cls.default_headfoot_font_h_padding = global_font_h_padding
            cls.default_button_font_h_padding = global_font_h_padding
        if global_font_v_padding is not None:
            cls.default_text_line_v_padding = global_font_v_padding
            cls.default_splash_v_padding = global_font_v_padding
            cls.default_dialog_v_paddingt = global_font_v_padding
            cls.default_headfoot_v_padding = global_font_v_padding
            cls.default_button_v_padding = global_font_v_padding
        if global_font_h_align is not None:
            cls.default_text_line_font_h_align = global_font_h_align
            cls.default_splash_font_h_align = global_font_h_align
            cls.default_dialog_font_h_align = global_font_h_align
            cls.default_headfoot_font_h_align = global_font_h_align
            cls.default_button_font_h_align = global_font_h_align
        if global_font_v_align is not None:
            cls.default_text_line_v_align = global_font_v_align
            cls.default_splash_v_align = global_font_v_align
            cls.default_dialog_v_alignt = global_font_v_align
            cls.default_headfoot_v_align = global_font_v_align
            cls.default_button_v_align = global_font_v_align


##################################################################################
# MERGE METHOD
##################################################################################
# Method that unions the contents of two lists together.  Duplicate items are
# only added in once (with the first list having priority).
##################################################################################
def merge(*arguments):
    output = []
    for arg in arguments:
        if arg is not None:
            if isinstance(arg, list):
                output += arg
            else:
                output += [arg]
    return output


##################################################################################
# ARRAY_SINGLE_NONE METHOD
##################################################################################
# Method that takes a singleton item and makes it a list.  If an item is already
# a list, then it is returned.   THe no_coerce_none parameter determines if a None
# value is returned as none (when no_coerce_none is True) or an empty list when
# no_coerce_none is True
##################################################################################
def array_single_none(item, no_coerce_none=False):
    if isinstance(item, list):
        return item
    elif item is None:
        if no_coerce_none:
            return None
        else:
            return []
    else:
        return [item]


##################################################################################
# REMOVE DUPLICATES METHOD
##################################################################################
# Method to remove any duplicate values from a list.
##################################################################################
def remove_duplicates(sequence):
    uniques = set()
    return [item for item in sequence if item not in uniques and not uniques.add(item)]


##################################################################################
# GET_IP_ADDRESS METHOD
##################################################################################
# Method used to return the primary local IP address of the device.
##################################################################################
def get_ip_address():
    local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        local_socket.connect(('10.0.0.0', 0))
        ip = local_socket.getsockname()[0]
    except IOError:
        ip = '127.0.0.1'
    finally:
        local_socket.close()
    return ip


##################################################################################
# DRAW_TRUE_WITH_RECT METHOD
##################################################################################
# Method that draws a rectangle with 'square' borders for more crisp buttons and
# borders using the a rectangle as input.
##################################################################################
def draw_true_with_rect(screen, color, rect, border_width):
    return draw_true_rect(screen, color, rect.x, rect.y, rect.width, rect.height, border_width)


##################################################################################
# DRAW_TRUE_RECT METHOD
##################################################################################
# Method that draws a rectangle with 'square' borders for more crisp buttons and
# borders using the rectangle parameters as input.
##################################################################################
def draw_true_rect(screen, color, x, y, width, height, border_width):
    if border_width == 0:
        return pygame.draw.rect(screen, color, (x, y, width, height), border_width)
    rect = pygame.draw.rect(screen, color, (x, y, width, height), 1)
    border_count = 1
    while border_count < border_width:
        x += 1
        y += 1
        width -= 2
        height -= 2
        pygame.draw.rect(screen, color, (x, y, width, height), 1)
        border_count += 1
    return rect


##################################################################################
# WRAP_TEXT_LINE METHOD
##################################################################################
# Method that is modified from the function code located on the pygame wiki site:
# http://pygame.org/wiki/TextWrap to work with freetype and return the lines in a
# list.  This will take text and determine if it fits in the specified width
# parameter.  Newline characters also create breaks.  The return is a tuple that
# contains each text line along with the text, height (should be the same) and
# width of each.
##################################################################################
def wrap_text_line(font, text, width):
    text_lines = []
    text_height = []
    text_width = []
    i = 1
    # A few random words and symbols that have ascenders and descenders
    max_height = font.get_rect("jet Mopping quiT!([}|/").height
    while text:
        font_rect = font.get_rect(text[:i])
        # Loop through the words until we exceed the width, run out of characters,
        # run out of spaces or run out of words.
        while (font_rect.width < width and i < len(text) and "\n" not in text[:i]) or\
                (" " not in text[:i] and text[:i] is not text):
            i += 1
            font_rect = font.get_rect(text[:i])
        # if we've wrapped the text, then adjust the wrap to the last word
        if "\n" in text[:i]:
            i = text.find("\n", 0, i) + 1
        elif i < len(text):
            i = text.rfind(" ", 0, i) + 1
        line_text = text[:i].strip("\n")
        text_rect = font.get_rect(line_text)
        text_lines.append(line_text)
        text_height.append(max_height)
        text_width.append(text_rect.width)
        text = text[i:]
    return text_lines, text_height, text_width


##################################################################################
# GET_BUTTONS_START_HEIGHT METHOD
##################################################################################
# Method that returns the y location or top of the top most button that is not
# None (and therefore not displayed) from a list of buttons.
##################################################################################
def get_buttons_start_height(buttons):
    min_height = Defaults.tft_height
    if buttons is not None:
        for button in buttons:
            if button.text is not None and button.y < min_height:
                min_height = button.y
    return min_height


##################################################################################
# GET_BUTTONS_END_HEIGHT METHOD
##################################################################################
# Method that returns the bottom of the lowest visible button (text not set to
# None) from a list of buttons.
##################################################################################
def get_buttons_end_height(buttons):
    max_height = -1
    if buttons is not None:
        for button in buttons:
            if button.text is not None and button.y + button.height > max_height:
                max_height = button.y + button.height
    return max_height + 1


##################################################################################
# SEND WAKE COMMAND METHOD
##################################################################################
# Method to 'wake' the screen should the built-in screen blanking functionality
# be active.   This is done by executing a command similarly to the following:
# $ printf \033[13] | sudo tee /dev/tty1 > /dev/null.
##################################################################################
def send_wake_command():
    process = subprocess.Popen(Screen.WakeCommand.split(), stdout=subprocess.PIPE)
    subprocess.Popen(Screen.WakePipe.split(), stdin=process.stdout, stdout=subprocess.PIPE)


##################################################################################
# ALREADY INITIALIZED EXCEPTION
##################################################################################
class AlreadyInitializedException(Exception):
    pass


##################################################################################
# NOT INITIALIZED EXCEPTION
##################################################################################
class NotInitializedException(Exception):
    pass


##################################################################################
# BACKLIGHT NOT ENABLED EXCEPTION
##################################################################################
class BacklightNotEnabled(Exception):
    pass
