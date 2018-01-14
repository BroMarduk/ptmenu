#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
# The "from tftmenu import *" and "from tfttemplates import *" items need to be
# present in all display applications.
from tftmenu import *
from tfttemplates import *

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
Displays.initialize(DISP35RP)


##################################################################################
# MENU TEMPLATES
##################################################################################
# Create buttons for menu using a template (BUTTONS_2X1_BOTTOM) that adds two
# buttons.  The first says "Hello" and the second says "Goodbye".  Actions are set
# to show a "Hello!" message using and add actions to show a message using the
# SPLASH_INFO built-in dialog (used internally).  The second button, "Goodbye"
# button exits the application.
buttons = get_buttons(ButtonTemplate.Bottom2x1,
                      names=["Hello", "Goodbye"],
                      actions=[Action(DisplayAction.Display, SplashBuiltIn.Info,
                                      [SplashLine("HELLO!", Defaults.default_splash_font_size_title),
                                       SplashLine("Welcome to the menu."),
                                       SplashLine("(This screen will close in 5 seconds.)")]),
                               Action(DisplayAction.Exit)])
# Creates a menu of type Menu and adds the buttons and a header to the menu.  The
# buttons are the buttons created in the previous statement and the header is
# created in-line using a user displayed message.  The text property can be
# string or a HeaderText (technically it can be any BaseText item)
mainMenu = Menu(buttons=buttons, header=Header(mode=HeadFootType.UserText, text="Hello Menu!"))
# Adds the mainMenu created above to the Displays collection with the name
# "Main".
Displays.menus["Main"] = mainMenu
# Starts the menu by initializing the necessary components and displaying the
# menu called "Main".  Start can also be called with the menu object itself
# (mainMenu) as an alternative.  Creating a menu with an existing name will
# replace the previous menu with the new one.  Execution will continue on the
Displays.start("Main")
