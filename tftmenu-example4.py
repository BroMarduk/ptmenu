#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
# The "from tftmenu import *" and "from tfttemplates import *" items need to be
# present in all display applicaitons.
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
Displays.initialize(DISP28CP)


##################################################################################
# MENU TEMPLATES
##################################################################################
mainMenuButtons = get_buttons(ButtonTemplate.FullScreen2x4, border_color=Color.Yellow, font_size=14,
                              names=["2x3 Header",
                                     "2x2 Header/Footer",
                                     "3x3 Header",
                                     "3x2 Header/Footer",
                                     "2x4 Full Screen",
                                     "3x4 Full Screen",
                                     "4x4 Full Screen",
                                     "Next"],
                              actions=[Action(DisplayAction.Display, "menu2x3Header"),
                                       Action(DisplayAction.Display, "menu2x2HeaderFooter"),
                                       Action(DisplayAction.Display, "menu3x3Header"),
                                       Action(DisplayAction.Display, "menu3x2HeaderFooter"),
                                       Action(DisplayAction.Display, "menu2x4Full"),
                                       Action(DisplayAction.Display, "menu3x4Full"),
                                       Action(DisplayAction.Display, "menu4x4Full"),
                                       Action(DisplayAction.Display, "Page2")])
if mainMenuButtons is not None:
    mainMenu = Menu(timeout=90, buttons=mainMenuButtons, header=Header(type=HeadFootType.NoDisplay))
    Displays.menus["Main"] = mainMenu
page2MenuButtons = get_buttons(ButtonTemplate.FullScreen2x4, border_color=Color.Yellow, font_size=14,
                               names=["1x1 Bottom",
                                      "1x1 Bottom Left",
                                      "1x1 Bottom Right",
                                      "1x1 Bottom Wide",
                                      "2x1 Bottom",
                                      "3x1 Bottom",
                                      "Back",
                                      "Exit"],
                               actions=[Action(DisplayAction.Display, "menu1x1Bottom"),
                                        Action(DisplayAction.Display, "menu1x1BottomLeft"),
                                        Action(DisplayAction.Display, "menu1x1BottomRight"),
                                        Action(DisplayAction.Display, "menu1x1BottomFullWidth"),
                                        Action(DisplayAction.Display, "menu2x1Bottom"),
                                        Action(DisplayAction.Display, "menu3x1Bottom"),
                                        Action(DisplayAction.Display, "Main"),
                                        Action(DisplayAction.Exit)])
if page2MenuButtons is not None:
    page2Menu = Menu(timeout=90, buttons=page2MenuButtons, header=Header(type=HeadFootType.NoDisplay))
    Displays.menus["Page2"] = page2Menu
buttons_2x3_header = get_buttons(ButtonTemplate.Header2x3, border_color=Color.Red)
if buttons_2x3_header is not None:
    buttons_2x3_header[-1].text = "Back"
    buttons_2x3_header[-1].action = Action(DisplayAction.Display, "Main")
    menu_2x3_header = Menu(timeout=90, buttons=buttons_2x3_header,
                           header=Header(type=HeadFootType.UserText,
                                         text=HeadFootLine(font_size=20, text="2 Col by 3 Row with Header")))
    Displays.menus["menu2x3Header"] = menu_2x3_header
buttons_2x2_headfoot = get_buttons(ButtonTemplate.HeaderFooter2x2, border_color=Color.Red)
if buttons_2x2_headfoot is not None:
    buttons_2x2_headfoot[-1].text = "Back"
    buttons_2x2_headfoot[-1].action = Action(DisplayAction.Display, "Main")
    menu_2x2_headfoot = Menu(timeout=90, buttons=buttons_2x2_headfoot,
                             header=Header(type=HeadFootType.UserText,
                                           text=HeadFootLine(font_size=20, text="2 Col by 3 Row with Head/Foot")),
                             footer=Footer(type=HeadFootType.DateTime12))
    Displays.menus["menu2x2HeaderFooter"] = menu_2x2_headfoot
buttons_3x3_header = get_buttons(ButtonTemplate.Header3x3, border_color=Color.Red)
if buttons_3x3_header is not None:
    buttons_3x3_header[-1].text = "Back"
    buttons_3x3_header[-1].action = Action(DisplayAction.Display, "Main")
    menu_3x3_header = Menu(timeout=90, buttons=buttons_3x3_header,
                           header=Header(type=HeadFootType.UserText,
                                         text=HeadFootLine(font_size=20, text="3 Col by 3 Row with Header")))
    Displays.menus["menu3x3Header"] = menu_3x3_header
buttons_3x2_headfoot = get_buttons(ButtonTemplate.HeaderFooter2x2, border_color=Color.Red)
if buttons_3x2_headfoot is not None:
    buttons_3x2_headfoot[-1].text = "Back"
    buttons_3x2_headfoot[-1].action = Action(DisplayAction.Display, "Main")
    menu_3x2_headfoot = Menu(timeout=90, buttons=buttons_3x2_headfoot,
                             header=Header(type=HeadFootType.UserText,
                                           text=HeadFootLine(font_size=20, text="2 Col by 3 Row with Head/Foot")),
                             footer=Footer(type=HeadFootType.DateTime12)
                             )
    Displays.menus["menu3x2HeaderFooter"] = menu_3x2_headfoot
buttons_2x4_full_screen = get_buttons(ButtonTemplate.FullScreen2x4, border_color=Color.Green)
if buttons_2x4_full_screen is not None:
    buttons_2x4_full_screen[-1].text = "Back"
    buttons_2x4_full_screen[-1].action = Action(DisplayAction.Display, "Main")
    menu_2x4_full_screen = Menu(timeout=90, buttons=buttons_2x4_full_screen)
    Displays.menus["menu2x4Full"] = menu_2x4_full_screen
buttons_3x4_full_screen = get_buttons(ButtonTemplate.FullScreen3x4, border_color=Color.Green)
if buttons_3x4_full_screen is not None:
    buttons_3x4_full_screen[-1].text = "Back"
    buttons_3x4_full_screen[-1].action = Action(DisplayAction.Display, "Main")
    menu_3x4_full_screen = Menu(timeout=90, buttons=buttons_3x4_full_screen)
    Displays.menus["menu3x4Full"] = menu_3x4_full_screen
buttons_4x4_full_screen = get_buttons(ButtonTemplate.FullScreen4x4, border_color=Color.Green)
if buttons_4x4_full_screen is not None:
    buttons_4x4_full_screen[-1].text = "Back"
    buttons_4x4_full_screen[-1].action = Action(DisplayAction.Display, "Main")
    menu_4x4_full_screen = Menu(timeout=90, buttons=buttons_4x4_full_screen)
    Displays.menus["menu4x4Full"] = menu_4x4_full_screen
buttons_1x1_bottom = get_buttons(ButtonTemplate.Bottom1x1, border_color=Color.Cyan)
if buttons_1x1_bottom is not None:
    buttons_1x1_bottom[-1].text = "Back"
    buttons_1x1_bottom[-1].action = Action(DisplayAction.Display, "Page2")
    menu_1x1_bottom = Menu(timeout=90, buttons=buttons_1x1_bottom)
    Displays.menus["menu1x1Bottom"] = menu_1x1_bottom
buttons_1x1_bottom_left = get_buttons(ButtonTemplate.BottomLeft1x1, border_color=Color.Cyan)
if buttons_1x1_bottom_left is not None:
    buttons_1x1_bottom_left[-1].text = "Back"
    buttons_1x1_bottom_left[-1].action = Action(DisplayAction.Display, "Page2")
    menu_1x1_bottom_left = Menu(timeout=90, buttons=buttons_1x1_bottom_left)
    Displays.menus["menu1x1BottomLeft"] = menu_1x1_bottom_left
buttons_1x1_bottom_right = get_buttons(ButtonTemplate.BottomRight1x1, border_color=Color.Cyan)
if buttons_1x1_bottom_right is not None:
    buttons_1x1_bottom_right[-1].text = "Back"
    buttons_1x1_bottom_right[-1].action = Action(DisplayAction.Display, "Page2")
    menu_1x1_bottom_right = Menu(timeout=90, buttons=buttons_1x1_bottom_right)
    Displays.menus["menu1x1BottomRight"] = menu_1x1_bottom_right
buttons_1x1_bottom_full_width = get_buttons(ButtonTemplate.BottomFullWidth1x1, border_color=Color.Cyan)
if buttons_1x1_bottom_full_width is not None:
    buttons_1x1_bottom_full_width[-1].text = "Back"
    buttons_1x1_bottom_full_width[-1].action = Action(DisplayAction.Display, "Page2")
    menu_1x1_bottom_full_width = Menu(timeout=90, buttons=buttons_1x1_bottom_full_width)
    Displays.menus["menu1x1BottomFullWidth"] = menu_1x1_bottom_full_width
buttons_2x1_bottom = get_buttons(ButtonTemplate.Bottom2x1, border_color=Color.Magenta)
if buttons_2x1_bottom is not None:
    buttons_2x1_bottom[-1].text = "Back"
    buttons_2x1_bottom[-1].action = Action(DisplayAction.Display, "Page2")
    menu_2x1_bottom = Menu(timeout=90, buttons=buttons_2x1_bottom)
    Displays.menus["menu2x1Bottom"] = menu_2x1_bottom
buttons_3x1_bottom = get_buttons(ButtonTemplate.Bottom3x1, border_color=Color.Magenta)
if buttons_3x1_bottom is not None:
    buttons_3x1_bottom[-1].text = "Back"
    buttons_3x1_bottom[-1].action = Action(DisplayAction.Display, "Page2")
    menu_3x1_bottom = Menu(timeout=90, buttons=buttons_3x1_bottom)
    Displays.menus["menu3x1Bottom"] = menu_3x1_bottom
Displays.start(initial_menu=Displays.menus["Main"], backlight_method=BacklightMethod.Pwm)
