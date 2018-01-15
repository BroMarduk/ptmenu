# PTMenu

A menu system for the Adafruit (and possibly other) PiTFT displays (most with touchscreen).

This project is a menu system for most of the Adafruit PiTFT displays. These displays are designed for the Raspberry Pi and require kernel changes and overlays to properly work. Instructions for configuring these displays can be found on the Adafruit Web Site at the following locations:

1. [Adafruit 2.2" PiTFT Non-Touch](https://learn.adafruit.com/adafruit-2-2-pitft-hat-320-240-primary-display-for-raspberry-pi/easy-install?view=all)
2. [Adafruit 2.4" & 2.8" & 3.2" Resistive](https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/downloads?view=all)
3. [Adafruit 2.8" Capacitive](https://learn.adafruit.com/adafruit-2-8-pitft-capacitive-touch/easy-install?view=all)
4. [Adafruit 3.5" Resistive](https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install?view=all)
 
## Inspirations

There are a few different menu systems out there for the different TFT Displays. I have tried quite a few (including many on the Arduino platform as well) and found I was modifying these menus or combining features of different menus to get the desired functionally I desired. Somewhere mid-December of 2016, this combined with my desire to learn Python let me to try and combine all the functionality I needed into my own menu.  While the actual coding was started from scratch, there are numerous places where ideas, interface design or a few lines of code were borrowed.  

1. [garthvh's pitftmenu](https://github.com/garthvh/pitftmenu)

   Along with [Re4son's fork](https://github.com/Re4son/pitftmenu) this project provided me a starting point for what functionality I needed as a base.  My menu design used this menu systems button coordinates as a starting point.  I also used it as a basis to learn how to execute commands in Python, start X and to implement code to handle system shutdown on a low battery.
2. [Jeremy Blythe's Blog](https://jeremyblythe.blogspot.com/2014/09/raspberry-pi-pygame-ui-basics.html)
  
   Great resource for learning how to use pygame with a TFT.  Bridges the gap between the Adafruit documentation for the PiTFT and the pygame docs.
3. [pygame Documentation and Examples](https://www.pygame.org/docs)
  
   Learning a new library is always a challenge and even more so when the documentation is lacking.  With pygame, this is not the case.  Don't get me wrong, there is a learning curve learning the library, but the documentation and examples make almost all challenges solvable.
4. [Adafruit Learning System](https://learn.adafruit.com)

   It's one thing to support the products you sell and another to provide explicit tutorials on just about everything you make.  Adafruit may not be the only site that does this ([Sparkfun](http://learn.sparkfun.com) comes to mind), but I think they do it better than anyone else.  I referenced their documentation above.  Also a special thanks to the customer service department at Adafruit for replacing my 3.5" PiTFT which I didn't notice it had a small crack in the screen until I took it out of the box six months later.  Without that gesture, I would not have 3.5" support (or at least not TESTED 3.5" support).

## Requirements

In order to use the PTMenu, the following requirements are necessary:

1. A Raspberry Pi
  
   Any version, including the Zero should work.  Tested on an original Raspberry Pi, a Raspberry Pi 2 and a Raspberry Pi 3.  Once I solder the header on my Raspberry Pi Zero, I will test it as well.
2. An Adafruit PiTFT plugged into the header on the Raspberry Pi.
  
   All Adafruit PiTFTs are supported, but note that the 2.2" PiTFT is non-touch and would require a mouse to use.
3. Raspian Stretch, Jessie or Wheezy installed.   
  
   Other flavors that support the Adafruit PiTFTs, such as Kali, should also work, although I have not tested on anything but Jessie & Stretch.   You can use one of the Adafruit PiTFT images or use the available PiTFT Helper scripts (or manual instructions) from Adafruit to install.   If the display loads the console on boot, things should be working. 
4. Python 2.7 installed as a package.

   Python 2.7 should be installed on most Raspberry Pi's by default.  If for some reason it was not or was removed that it will need to be reinstalled. 
5. Pygame installed as a package

   Pygame can be installed by running the following two commands:
  
   <b>sudo apt-get install python-pip</b>

   <b>sudo apt-get install python-pygame</b>
6. libsdl1.2-15-5

   If running Stretch or Jessie on the Raspberry Pi, the touch screen support in libsdl 1.2 has been broken for pygame.  To make it work, you need to revert to the last version from Wheezy (libsdl1.2-15-5).  Instructions to do this can be found on the [pitftmenu site](https://github.com/garthvh/pitftmenu).  Instructions and a script can be found on the [Adafruit site](https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/pitft-pygame-tips).  I could get mine working by using the Adafruit script, but it does seem to need to be run again after doing an upgrade to the Raspberry Pi.
   
7. wiringpi (Optional)

   If backlight and/or GPIO support is desired, the wiringpi library will need to be installed.  If not it can beinstalled using the following command:
   
   <b>sudo apt-get install wiringpi</b>

## Features

While the main functionality of the application is to display a screen with buttons that respond to actions (and it is the main function!), I built this to handle other features that I wanted or thought would make the menu system flexible enough to customize to meet future needs as well as leverage features of the Adafruit hardware.

+ Powerful and configurable when customizations are needed
+ Multiple Display screen (Meus, Dialogs, Splash) types.
+ Support for built-in screen blanking (customizable for each display)
+ Wake up on touch or hardware button press (including from system screen blank)
+ Controllable backlight support for PWM, ECHO and STMPE methods
+ Support for PiTFT's with hardware buttons
+ Adjustable dimming when using PWM for backlight
+ On/Off backlight support when using PWM for sound playback
+ Support for Adafruit's Power Button GPIO with detection
+ Built in soft button templates for 13 soft button configurations
+ Displays built on a 320x480 screen will work on a 240x320 screen and vice-versa.
+ Customizable button render order (multiple combinations of left-right and top-bottom)
+ Shell support without having to exit menu
+ Multiple text alignments for buttons/text/headers (left, center, right, top, middle, bottom)
+ Support for right-clicking buttons.
+ Full color support for borders, backgrounds and button borders
+ Button "down" visual indications.
+ Ability to call custom functions on button presses and refresh events
+ Built in support for date, time, host name in headers and footers
+ Ability to start x in either an attached monitor or on the PiTFT

## Installing
+ cd ~
+ git clone https://github.com/BroMarduk/ptmenu
+ cd ptmenu

## Examples

Once in the ptmenu directory, there are 5 example projects in the directory that can be run with python.  The <b>Displays.initialize()</b> function needs to be changed in each one to the actual Adafruit PiTFT device present and attached to the Raspberry Pi.  The list of devices is in each example above the <b>Displays.initialize()</b> line with multiple formats to make it easy to select the correct device.  This should be the only change necessary to run the program, assuming all of the requirements are met.

Supported Display Identifiers (any Method or the Value will work):

|  Device                            |  Value 1 | Value 2 | Value 3 | Int Value | GPIOs (Backlight)     |
|------------------------------------|----------|---------|---------|:---------:|-----------------------|
| Adafruit 2315 2.2" No Touch        | DISP22NT | AF_2315 | NONE22  | 1         | 17,22,23,27,(18)      |
| Adafruit 2455 2.4" Resistive       | DISP24R  | AF_2455 | RES24   | 2         | 16,13,12,6,5,(18)     |
| Adafruit 1601 2.8" Resistive       | DISP28R  | AF_1601 | RES28   | 3         | 23,22,21/27,18,(None) |
| Adafruit 1983 2.8" Capacitive      | DISP28C  | AF_1983 | CAP28   | 4         | 23,22,21/27,17,(18)   |
| Adafruit 2298 2.8" Resistive Plus  | DISP28RP | AF_2298 | RES28P  | 5         | 17,22,23,27,(18)      |
| Adafruit 2423 2.8" Capacitive Plus | DISP28CP | AF_2423 | CAP28P  | 6         | 17,22,23,27,(18)      |
| Adafruit 2626 3.2" Resistive Plus  | DISP32RP | AF_2626 | RES32P  | 7         | 22,23,17,27,(18)      |
| Adafruit 2097 3.5" Resistive       | DISP35R  | AF_2097 | RES35   | 8         | (18)                  |
| Adafruit 2441 3.5" Resistive Plus  | DISP35RP | AF_2441 | RES35P  | 9         | (18)                  |

+ <b>sudo python tftmenu-example1.py</b>

  Hello Menu! Example - Demonstrates a simple two button menu.  The "Hello" button demonstrates a splash display and the "Goodbye" button exits the menu.
  
+ <b>sudo python tftmenu-example2.py</b>

  Advanced Menu Example - Demonstrates a majority of the features of the menu, including the hard buttons on some of the Adafruit displays
  
+ <b>sudo python tftmenu-example3.py</b>

  Demonstrates the different button order combinations visually.  L indicating Left, R indicating Right, T indicating Top and B indicating Bottom.  So "R-L / T-B" would indicate an order of Right to Left, then Top to Bottom.   All 8 possible combinations can be viewed.
  
+ <b>sudo python tftmenu-example4.py</b>

  Demonstrates the thirteen included button templates.   Additional templates can be created or in some cases where the template has blank space, additional buttons can be added.
  
+ <b>sudo python tftmenu-example5.py</b>

  Demonstrates some of the possible menu headers (can also be used in footers) that can be displayed.  In addition to the built-in headers, a custom function can also be provided.  This example uses a function called display_pi_temp(), which will show the current temperature of the pi, color coded to be green if below 60 degrees Celsius, Yellow if between 60 and 70 degrees Celsius, and Red if over 70 degrees.  (Also uses Blue if below 0 degrees Celsius, just in case it’s winter and you have the Pi outside).  These temps are based on the operating temperature of the LAN port, which seems to be the smallest range of specified operating temperatures I could find.
 
## Creating First Display
[Coming Soon]

## Advanced Display Features
[Coming Soon]

## Button Actions
[Coming Soon]

## Button Templates
[Coming Soon]

## Planned Enhancements

While I have been writing code for a while, this is my first Python project.  I'm sure there are lots of places where my old C# habits kicked in that would make a Pythonista cringe.  For that I am sorry.  If anyone using this finds any of those snippets, feel free to point those places out to me and once I understand the underlying reasons, I'll happily improve them.  Especially for a performance boost.  That said, there is also additional functionally in the planning stages that is documented below.  This list is somewhat prioritized, but subject to change based on any feedback I get.

In addition, I plan to go back and re-add comments and logging back in.   I stripped most of these areas out so I could get the project posted until I could go back and address my overly cryptic comments and logging into something that someone could possibly understand.

+ [DONE] Re-add understandable comments to source code.
+ [DONE] Add more (configurable) splash items for warnings, errors, information etc.
+ [DONE] Add more logging for operation and debugging
+ [DONE] Move the GPIO Buttons into a template similar to the Display Buttons templates.
+ [DONE] Add detection for broken libsdl1.2debian version and provide correction script in code
+ [DONE] Add support for launching StartX as an action
+ Make header/footer types and their functionality into tokens that can be used in text.
+ Add images/icons to buttons/headers/footers
+ Move internal text to resources for use with gettext and improve globalization.
+ Allow for arrow navigation and selection (only mouse and touch currently supported)
+ Support for Pimoroni HyperPixel (480x800 pixel display)
+ Add an installation script for all packages and to download respository.
