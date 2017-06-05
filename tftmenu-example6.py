#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
# THe random import is used only for the random_button_color callback function and
# is not normally needed.   The "from tftmenu import *" and "from tfttemplates
# import *" items need to be present in all display applications.
import tftvantage
from tftmenu import *
from tfttemplates import *
from tftvantage import Vantage


##################################################################################
# GET WEATHER FUNCTION
##################################################################################
# Example of a button call back function.  The menu and button parameters are
# passed in and can be changed.  The function can return a new Display object
# if a new menu should be loaded or returning None.  The menu.force_refresh is set
# to force a menu to redraw (useful if graphic elements have changed and need to
# be re-rendered.  By default if the same menu is reloaded more than once in a row,
# it is not rendered on subsequent shows.
def get_current_weather():
    vantage_wx = Vantage(**{"type": "serial", "port": "/dev/ttyUSB0", "baudrate": "19200", "wait_before_retry": 1.2, 
                            "command_delay": 1, "timeout": 6})
    loop_item = vantage_wx.getLatestWeatherLoop()

    if not loop_item:
        print ("No weather data was retrieved.")
    else:
        print ("Outside Temperature", loop_item['outTemp'])
        print ("Outside Humidity", loop_item['outHumidity'])
        print ("Inside Temperature", loop_item['inTemp'])
        print ("Inside Humidity", loop_item['inHumidity'])
        print ("Wind Direction", loop_item['windDir'])
        print ("Wind Speed", loop_item['windSpeed'])
        print ("Barometric Pressure", loop_item['barometer'])
        print ("Barometric Trend", loop_item['barometricTrend'])
        print ("Daily Rain", loop_item['dayRain'])
        print ("Rain Rate", loop_item['rainRate'])
        print ("Forecast", loop_item['forecastIcon'])
        print ("Forecast Rule", tftvantage.forecastRules[loop_item['forecastRule']])
        print ("Sunrise", time.strftime("%I:%M%P", time.localtime(loop_item['sunrise'])))
        print ("Sunset", time.strftime("%I:%M%P", time.localtime(loop_item['sunset'])))


##################################################################################
# DISPLAY INITIALIZATION
##################################################################################
# The proper Adafruit PiTFT type needs to be passed to the initialization method
# in order to correctly initialize the GPIOs for the button functionality and set
# the correct screen resolution.  The following displays are supported, which is
# all of the Adafruit PiTFT displays.  If using the 2.2 inch display without
# touch support (currently the only one), a mouse will need to be utilized for
# the menu to work correctly.
# DISP22NT   = AF_2315 = NONE22 = 1  # GPIOs 17,22,23,27,(18)
# DISP24R    = AF_2455 = RES24  = 2  # GPIOs 16,13,12,6,5,(18)
# DISP28R    = AF_1601 = RES28  = 3  # GPIOs 23,22,21/27,18,(None)
# DISP28C    = AF_1983 = CAP28  = 4  # GPIOs 23,22,21/27,17,(18)
# DISP28RP   = AF_2298 = RES28P = 5  # GPIOs 17,22,23,27,(18)
# DISP28CP   = AF_2423 = CAP28P = 6  # GPIOs 17,22,23,27,(18)
# DISP32RP   = AF_2626 = RES32P = 7  # GPIOs 22,23,17,27,(18)
# DISP35R    = AF_2097 = RES35  = 8  # GPIOs (18)
# DISP35RP   = AF_2441 = RES35P = 9  # GPIOs (18)
Displays.initialize(DISP28CP, global_font="./Fonts/BebasNeue.otf")
Defaults.default_headfoot_font_color = Color.Silver
Defaults.default_text_line_font_color = Color.Silver
Defaults.default_dialog_font_color = Color.Silver
Defaults.default_button_font_color = Color.Silver
Defaults.default_button_font_size = 24

##################################################################################
# MENU TEMPLATES
##################################################################################
mainMenuActions = [Action(DisplayAction.Display, "CurrentWx"),
                   Action(DisplayAction.Display, "ForecastWx"),
                   Action(DisplayAction.Display, "DetailedWx"),
                   Action(DisplayAction.Display, "RadarWx"),
                   Action(DisplayAction.Shell),
                   Action(DisplayAction.Display, "ConfirmExit")]
mainMenuButtons = get_buttons(ButtonTemplate.Header2x3, ButtonDirection.LeftRightTopBottom,
                              names=["Current", "Forecast", "Details", "Radar", "Shell", "Exit"],
                              actions=mainMenuActions,
                              border_color=[Color.Blue, Color.Blue, Color.Blue, Color.Blue, Color.Yellow, Color.Red])
mainMenu = Menu(timeout=90, buttons=mainMenuButtons,
                header=Header(mode=HeadFootType.DateTime12,
                              text=HeadFootLine(font_pad=False)))
Displays.menus["Main"] = mainMenu


##################################################################################
# DIALOG TEMPLATES
##################################################################################
# Three-Line Yes/No dialog box used to confirm exit
dialogConfirmExitText = [DialogLine("PLEASE CONFIRM", font_size=30, font_v_padding=14, font_pad=True),
                         DialogLine("Are you sure you want to Exit?\nYou will need to restart "
                                    "menu to resume functionality", font_size=24, wrap_text=True, font_pad=True)]
dialogConfirmExitActions = [Action(DisplayAction.Exit), Action(DisplayAction.Back)]
dialogConfirmExit = Dialog(dialogConfirmExitText, DialogStyle.YesNo, Color.Black, Color.Green,
                           actions=dialogConfirmExitActions, use_menu_timeout=True, use_menu_colors=True)
Displays.menus["ConfirmExit"] = dialogConfirmExit

# Current Weather Dialog
dialogCurrentWxText = [DialogLine("", font_size=30, font_pad=False)]
dialogCurrentWxActions = [Action(DisplayAction.Back)]
dialogCurrentWx = Dialog(dialogCurrentWxText, DialogStyle.FullScreenOk, Color.Black, Color.Blue,
                         actions=dialogCurrentWxActions, use_menu_timeout=True)
Displays.menus["CurrentWx"] = dialogCurrentWx

# Forecast Weather Dialog
dialogForecastWxText = [DialogLine("", font_size=30, font_pad=False)]
dialogForecastWxActions = [Action(DisplayAction.Back)]
dialogForecastWx = Dialog(dialogForecastWxText, DialogStyle.FullScreenOk, Color.Black, Color.Orange,
                          actions=dialogForecastWxActions, use_menu_timeout=True)
Displays.menus["ForecastWx"] = dialogForecastWx

# Detailed Weather Dialog
dialogDetailedWxText = [DialogLine("", font_size=30, font_pad=False)]
dialogDetailedWxActions = [Action(DisplayAction.Back)]
dialogDetailedWx = Dialog(dialogDetailedWxText, DialogStyle.FullScreenOk, Color.Black, Color.Green,
                        actions=dialogDetailedWxActions, use_menu_timeout=True)
Displays.menus["DetailedWx"] = dialogDetailedWx

# Radar Weather Dialog
dialogRadarWxText = [DialogLine("", font_size=30, font_pad=False)]
dialogRadarWxActions = [Action(DisplayAction.Back)]
dialogRadarWx = Dialog(dialogRadarWxText, DialogStyle.FullScreenOk, Color.Black, Color.Purple,
                       actions=dialogRadarWxActions, use_menu_timeout=True)
Displays.menus["RadarWx"] = dialogRadarWx

Displays.start(initial_menu="Main", backlight_method=BacklightMethod.Pwm, backlight_restore_last=True,
               backlight_state_sleep=True, backlight_auto=True)
