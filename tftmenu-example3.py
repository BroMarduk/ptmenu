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
mainMenuButtons = get_buttons(ButtonTemplate.Header3x3, border_color=Color.Yellow, font_size=18,
                              names=["L-R / T-B",
                                     "L-R / B-T",
                                     "R-L / T-B",
                                     "R-L / B-T",
                                     "T-B / L-R",
                                     "T-B / R-L",
                                     "B-T / L-R",
                                     "B-T / R-L",
                                     "Exit"],
                              actions=[Action(DisplayAction.Display, "menuLRTB"),
                                       Action(DisplayAction.Display, "menuLRBT"),
                                       Action(DisplayAction.Display, "menuRLTB"),
                                       Action(DisplayAction.Display, "menuRLBT"),
                                       Action(DisplayAction.Display, "menuTBLR"),
                                       Action(DisplayAction.Display, "menuTBRL"),
                                       Action(DisplayAction.Display, "menuBTLR"),
                                       Action(DisplayAction.Display, "menuBTRL"),
                                       Action(DisplayAction.Exit)])
if mainMenuButtons is not None:
    mainMenu = Menu(timeout=90, buttons=mainMenuButtons,
                    header=Header(mode=HeadFootType.UserText,
                                  text=HeadFootLine(text="Button Order Examples", font_size=25)))
    Displays.menus["Main"] = mainMenu
buttons_lrtb = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.LeftRightTopBottom, border_color=Color.Red)
if buttons_lrtb is not None:
    buttons_lrtb[len(buttons_lrtb) - 1].text = "Back"
    buttons_lrtb[len(buttons_lrtb) - 1].action = Action(DisplayAction.Display, "Main")
    menu_lrtb = Menu(timeout=90, buttons=buttons_lrtb, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuLRTB"] = menu_lrtb
buttons_lrbt = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.LeftRightBottomTop, border_color=Color.Red)
if buttons_lrbt is not None:
    buttons_lrbt[len(buttons_lrbt) - 1].text = "Back"
    buttons_lrbt[len(buttons_lrbt) - 1].action = Action(DisplayAction.Display, "Main")
    menu_lrbt = Menu(timeout=90, buttons=buttons_lrbt, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuLRBT"] = menu_lrbt
buttons_rltb = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.RightLeftTopBottom, border_color=Color.Green)
if buttons_rltb is not None:
    buttons_rltb[len(buttons_rltb) - 1].text = "Back"
    buttons_rltb[len(buttons_rltb) - 1].action = Action(DisplayAction.Display, "Main")
    menu_rltb = Menu(timeout=90, buttons=buttons_rltb, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuRLTB"] = menu_rltb
buttons_rlbt = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.RightLeftBottomTop, border_color=Color.Green)
if buttons_rlbt is not None:
    buttons_rlbt[len(buttons_rlbt) - 1].text = "Back"
    buttons_rlbt[len(buttons_rlbt) - 1].action = Action(DisplayAction.Display, "Main")
    menu_rlbt = Menu(timeout=90, buttons=buttons_rlbt, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuRLBT"] = menu_rlbt
buttons_tblr = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.TopBottomLeftRight, border_color=Color.Blue)
if buttons_tblr is not None:
    buttons_tblr[len(buttons_tblr) - 1].text = "Back"
    buttons_tblr[len(buttons_tblr) - 1].action = Action(DisplayAction.Display, "Main")
    menu_tblr = Menu(timeout=90, buttons=buttons_tblr, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuTBLR"] = menu_tblr
buttons_tbrl = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.TopBottomRightLeft, border_color=Color.Blue)
if buttons_tbrl is not None:
    buttons_tbrl[len(buttons_tbrl) - 1].text = "Back"
    buttons_tbrl[len(buttons_tbrl) - 1].action = Action(DisplayAction.Display, "Main")
    menu_tbrl = Menu(timeout=90, buttons=buttons_tbrl, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuTBRL"] = menu_tbrl
buttons_btlr = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.BottomTopLeftRight, border_color=Color.Orange)
if buttons_btlr is not None:
    buttons_btlr[len(buttons_btlr) - 1].text = "Back"
    buttons_btlr[len(buttons_btlr) - 1].action = Action(DisplayAction.Display, "Main")
    menu_btlr = Menu(timeout=90, buttons=buttons_btlr, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuBTLR"] = menu_btlr
buttons_btrl = get_buttons(ButtonTemplate.FullScreen4x4, ButtonDirection.BottomTopRightLeft, border_color=Color.Orange)
if buttons_btrl is not None:
    buttons_btrl[len(buttons_btrl) - 1].text = "Back"
    buttons_btrl[len(buttons_btrl) - 1].action = Action(DisplayAction.Display, "Main")
    menu_btrl = Menu(timeout=90, buttons=buttons_btrl, header=Header(mode=HeadFootType.NoDisplay))
    Displays.menus["menuBTRL"] = menu_btrl
Displays.start(initial_menu=Displays.menus["Main"], backlight_method=BacklightMethod.Pwm)
