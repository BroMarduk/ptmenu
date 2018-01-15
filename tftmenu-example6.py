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


class Weather:
    weather_data = None
    current_wx_last_update = None

    ##################################################################################
    # GET WEATHER FUNCTION
    ##################################################################################
    # Function to get the current weather conditions from the current weather loop on
    # the Davis Vantage console.
    ##################################################################################
    @classmethod
    def get_current_weather(cls):
        result = True
        vantage_wx = None
        try:
            vantage_wx = Vantage(
                **dict(type="serial", port="/dev/ttyUSB0", baudrate="19200", wait_before_retry=1.2, command_delay=0.5,
                       timeout=0.5, max_tries=1))
            cls.weather_data = vantage_wx.getLatestWeatherLoop()
        except Exception, ex:
            logger.debug("Error getting weather from Vantage: {0}".format(unicode(ex)))
            result = False
        finally:
            if vantage_wx is not None:
                vantage_wx.closePort()
            return result

    @classmethod
    def get_weather_details(cls):
        if not cls.weather_data:
            print ("No weather data was retrieved.")
        else:
            print ("Outside Temperature", cls.weather_data['outTemp'])
            print ("Outside Humidity", cls.weather_data['outHumidity'])
            print ("Inside Temperature", cls.weather_data['inTemp'])
            print ("Inside Humidity", cls.weather_data['inHumidity'])
            print ("Wind Direction", cls.weather_data['windDir'])
            print ("Wind Speed", cls.weather_data['windSpeed'])
            print ("Barometric Pressure", cls.weather_data['barometer'])
            print ("Barometric Trend", cls.weather_data['barometricTrend'])
            print ("Daily Rain", cls.weather_data['dayRain'])
            print ("Rain Rate", cls.weather_data['rainRate'])
            print ("Forecast", cls.weather_data['forecastIcon'])
            print ("Forecast Rule", tftvantage.forecastRules[cls.weather_data['forecastRule']])
            print ("Sunrise", time.strftime("%I:%M%P", time.localtime(cls.weather_data['sunrise'])))
            print ("Sunset", time.strftime("%I:%M%P", time.localtime(cls.weather_data['sunset'])))

    @classmethod
    def draw_current_weather(cls, screen, display):
        if screen is None or display is None:
            return
        cur_time = int(time.time())
        if cls.current_wx_last_update is not None:
            if cls.current_wx_last_update + 60 > cur_time:
                return
        if cls.get_current_weather():
            cls.get_weather_details()
            cls.current_wx_last_update = cur_time

        if DisplayResolution is DisplayResolution.Small320x240:
            newrect = draw_true_rect(Displays.screen, Color.Green, display.border_width - 1, display.border_width - 1,
                                     Defaults.tft_width - display.border_width,
                                     Defaults.tft_height - display.border_width, 0)
            pygame.display.update(newrect)
        else:
            newrect = draw_true_rect(Displays.screen, Color.Green, display.border_width - 1, display.border_width - 1,
                                     Defaults.tft_width - (display.border_width * 2),
                                     Defaults.tft_height - (display.border_width * 2), 0)
            pygame.display.update(newrect)


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
                         actions=dialogCurrentWxActions, use_menu_timeout=True,
                         draw_callback=Weather.draw_current_weather)
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
