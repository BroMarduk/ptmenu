#!/usr/bin/python
##################################################################################
# IMPORTS
##################################################################################
# THe random import is used only for the random_button_color callback function and
# is not normally needed.   The "from tftmenu import *" and "from tfttemplates
# import *" items need to be present in all display applications.
import random

from tftmenu import *
from tfttemplates import *


##################################################################################
# RANDOM BUTTON CALLBACK FUNCTION
##################################################################################
# Example of a button call back function.  The menu and button parameters are
# passed in and can be changed.  The function can return a new Display object
# if a new menu should be loaded or returning None.  The menu.force_refresh is set
# to force a menu to redraw (useful if graphic elements have changed and need to
# be re-rendered.  By default if the same menu is reloaded more than once in a row,
# it is not rendered on subsequent shows.
def random_button_color(menu, button):
    if button is not None:
        button_color = random.randint(0, 6)
        if button_color is 0:
            button.border_color = Color.Red
        elif button_color is 1:
            button.border_color = Color.Orange
        elif button_color is 2:
            button.border_color = Color.Yellow
        elif button_color is 3:
            button.border_color = Color.Green
        elif button_color is 4:
            button.border_color = Color.Blue
        elif button_color is 5:
            button.border_color = Color.Indigo
        else:
            button.border_color = Color.Purple
        menu.force_refresh = True


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
Displays.initialize(DISP35RP, global_font="./Fonts/BebasNeue.otf")
Defaults.default_headfoot_font_color = Color.Silver
Defaults.default_text_line_font_color = Color.Silver
Defaults.default_dialog_font_color = Color.Silver
Defaults.default_button_font_color = Color.Silver
Defaults.default_button_font_size = 24


##################################################################################
# MENU TEMPLATES
##################################################################################
mainMenuActions = [Action(DisplayAction.Display, SplashBuiltIn.Warning,
                          [SplashLine("PLEASE WAIT", Defaults.default_splash_font_size_title),
                           SplashLine("...about 5 seconds.", Defaults.default_splash_font_size)]),
                   Action(DisplayAction.Display, "CustomFrench"),
                   Action(DisplayAction.Display, "YesNoCancel"),
                   Action(DisplayAction.NoAction), Action(DisplayAction.Display, "Page2"),
                   Action(DisplayAction.Display, "ConfirmExit")]
mainMenuButtons = get_buttons(ButtonTemplate.Header2x3, ButtonDirection.LeftRightTopBottom,
                              names=["Warning", "French", "Yes/No/Cancel", None, "Next", "Exit"],
                              actions=mainMenuActions,
                              border_color=[None, Color.Green, Color.Green, None, Color.Yellow, Color.Red])
mainMenu = Menu(timeout=90, buttons=mainMenuButtons,
                header=Header(mode=HeadFootType.DateTime12,
                              text=HeadFootLine(font_pad=False)))
Displays.menus["Main"] = mainMenu
page2MenuActions = [Action(DisplayAction.Display, "Backlight"), Action(DisplayAction.Shell),
                    Action(DisplayAction.Function, random_button_color),
                    Action(DisplayAction.Display, "ScreenButton"), Action(DisplayAction.Display, "Main"),
                    Action(DisplayAction.Display, "YesNoColored")]
page2MenuButtons = get_buttons(ButtonTemplate.Header2x3, ButtonDirection.LeftRightTopBottom,
                               names=["Backlight", "Shell", "Random", "Full", "Previous", "Exit"],
                               actions=page2MenuActions,
                               border_color=[Color.Red, Color.Green, Color.Cyan, Color.Orange, Color.Yellow])
page2Menu = Menu(border_color=Color.Red, timeout=10, buttons=page2MenuButtons,
                 header=Header(mode=HeadFootType.UserText, text=HeadFootLine(text="Secondary Menu", font_pad=False)))
Displays.menus["Page2"] = page2Menu
backlightMenuActions = [Action(DisplayAction.BacklightUp), Action(DisplayAction.ScreenSleep),
                        Action(DisplayAction.BacklightDown), Action(DisplayAction.Display, "Main")]
backlightMenuButtons = get_buttons(ButtonTemplate.HeaderFooter2x2, ButtonDirection.LeftRightTopBottom,
                                   names=["Up", "Sleep", "Down", "Back"], actions=backlightMenuActions,
                                   border_color=[Color.Yellow, Color.Yellow, Color.Yellow, Color.Green])
backlightMenu = Menu(border_color=Color.Green, timeout=10, buttons=backlightMenuButtons,
                     header=Header(mode=HeadFootType.UserText, text=HeadFootLine(text="Backlight", font_pad=False)),
                     footer=Footer(mode=HeadFootType.IpAddress, text=HeadFootLine(text="Your IP: {0}", font_pad=False)))
Displays.menus["Backlight"] = backlightMenu


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
# Two-Line Yes/No/Cancel dialog box used to confirm exit.  Pressing cancel
# displays a message then returns back to the main menu (not the dialog) that
# itself.
dialogYesNoCancelText = [DialogLine("Are you sure you want to Exit?", font_size=26, font_v_align=TextVAlign.Top),
                         DialogLine("You will need to restart menu to continue",
                                    font_size=20, font_v_align=TextVAlign.Bottom)]
dialogYesNoCancelActions = [Action(DisplayAction.Exit), Action(DisplayAction.Back),
                            Action(DisplayAction.Display, SplashBuiltIn.Info,
                                   [SplashLine("OPERATION CANCELLED", Defaults.default_splash_font_size_title,
                                               wrap_text=True),
                                    SplashLine("The previous operation has been cancelled.",
                                               Defaults.default_splash_font_size, wrap_text=True)])]
dialogYesNoCancel = Dialog(dialogYesNoCancelText, DialogStyle.YesNoCancel, Color.Black, Color.Orange,
                           actions=dialogYesNoCancelActions, use_menu_timeout=True, use_menu_colors=True)
Displays.menus["YesNoCancel"] = dialogYesNoCancel
# Custom French dialog box used to confirm exit.  Oui = Yes, Non = No.  Uses
# custom button font color as well as different button colors for each button
dialogCustomFrenchText = [DialogLine("Voulez-vous vraiment quitter?", font_size=24, font_pad=False)]
dialogCustomFrenchButtons = get_buttons(ButtonTemplate.Bottom2x1, ButtonDirection.LeftRightTopBottom,
                                        names=["Oui", "Non"], font_color=[Color.White, Color.Magenta],
                                        actions=[Action(DisplayAction.Exit),
                                                 Action(DisplayAction.Back)],
                                        border_color=[Color.White, Color.Magenta])
dialogCustomFrench = Dialog(dialogCustomFrenchText, DialogStyle.Custom, Color.Black, Color.Gray,
                            buttons=dialogCustomFrenchButtons)
Displays.menus["CustomFrench"] = dialogCustomFrench
# Full screen dialog.  Has no visible button, but touching anywhere on the
# screen will dismiss the dialog.
dialogScreenButtonText = [DialogLine("Touch anywhere on the", font_size=30, font_pad=False),
                          DialogLine("screen to dismiss", font_size=30, font_pad=False)]
dialogScreenButtonActions = [Action(DisplayAction.Back)]
dialogScreenButton = Dialog(dialogScreenButtonText, DialogStyle.FullScreenOk, Color.Black, Color.Orange,
                            actions=dialogScreenButtonActions, use_menu_timeout=True)
Displays.menus["ScreenButton"] = dialogScreenButton
# Two-Line Yes/No dialog box used to confirm exit.  This dialog uses red for
# the Yes button and Green for the No button border colors.
dialogYesNoColoredText = [DialogLine("Are you sure you want to Exit?", font_size=26, font_pad=False),
                          DialogLine("You will need to restart menu to continue", font_size=20, font_pad=False)]
dialogYesNoColoredActions = [Action(DisplayAction.Exit), Action(DisplayAction.Back)]
dialogYesNoColoredButtons = get_buttons(ButtonTemplate.Bottom2x1, names=[DialogButtonText.Yes, DialogButtonText.No],
                                        actions=dialogYesNoColoredActions, background_color=Color.Black,
                                        border_color=None)
dialogYesNoColored = Dialog(dialogYesNoColoredText, DialogStyle.YesNo, background_color=Color.Black,
                            buttons=dialogYesNoColoredButtons, actions=dialogYesNoColoredActions,
                            border_color=Color.Yellow, use_menu_timeout=True, use_menu_colors=True)
dialogYesNoColored.buttons[0].border_color = Color.Red
dialogYesNoColored.buttons[1].border_color = Color.Green
Displays.menus["YesNoColored"] = dialogYesNoColored
Displays.start(initial_menu="Main", backlight_method=BacklightMethod.Pwm, backlight_restore_last=True,
               backlight_auto=True)
