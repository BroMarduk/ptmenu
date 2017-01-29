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

  Along with [Re4son's fork](https://github.com/Re4son/pitftmenu) this project provided me a starting point for what functionality I needed as a base.  My menu design used this menu systems button coordinates as a starting point.  I also used it as a basis to learn how to execute commands in Python and to implement code to handle system shutdown on a low battery.
2. [Jeremy Blythe's Blog](http://jeremyblythe.blogspot.com/2014/09/raspberry-pi-pygame-ui-basics.html)
  
  Great resource for learning how to use pygame with a TFT.  Bridges the gap between the Adafruit documentation for the PiTFT and the pygame docs.
3. [pygame Documentation and Examples](http://www.pygame.org/docs/)
  
  Learning a new library is always a challenge and even more so when the documentation is lacking.  With pygame, this is not the case.  Don't get me wrong, there is a learning curve learning the library, but the documentation and examples make almost all challenges solvable.
4. [Adafruit Learning System](https://learn.adafruit.com/)

  It's one thing to support the products you sell and another to provide explicit tutorials on just about everything you make.  Adafruit may not be the only site that does this ([Sparkfun](learn.sparkfun.com) comes to mind), but I think they do it better than anyone else.  I referenced their documentation above.  Also, a special thanks to the customer service department at Adafruit for replacing my 3.5" PiTFT which I didn't notice it had a small crack in the screen until I took it out of the box six months later.  Without that gesture, I would not have 3.5" support (or at least not TESTED 3.5" support).
i
## Requirements

In order to use the PTMenu, the following requirements are necessary:

1. A Raspberry Pi
  
  Any version, including the Zero should work.  Tested on an original Raspberry Pi, a Raspberry Pi 2 and a Raspberry Pi 3.  Once I solder the header into my Zero, I will test it as well.
2. An Adafruit PiTFT plugged into the header on the Raspberry Pi.
  
  All Adafruit PiTFTs are supported, but note that the 2.2" PiTFT is non-touch and would require a mouse to use.
3. Raspian Jessie or Wheezy installed.   
  
  Other flavors that support the Adafruit PiTFTs, such as Kali, should also work, although I have not tested on anything but Jessie.
4. Python 2.7 installed as a package.
  Python 2.7 should be installed on most Raspberry Pi's by default.  If for some reason it was not or was removed that it will need to be reinstalled. 
5. Pygame installed as a package
  Pygame can be installed by running the following two commands:
  
  <b>sudo apt-get install python-pip</b>
  
  <b>sudo apt-get install python-pygame</b>
6. libsdl1.2-15-5

  If running Jessie on the Raspberry Pi, the touch screen support in libsdl 1.2 has been broken for pygame.  To make it work, you need to revert to the last version from Wheezy (libsdl1.2-15-5).  Instructions to do this can be found on the [pitftmenu site](https://github.com/garthvh/pitftmenu).  Instructions and a script can be found on the [Adafruit site](https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/pitft-pygame-tips).  I could get mine working by using the Adafruit script, but it does seem to need to be run again after doing an upgrade to the Raspberry Pi.

## Features

While the main functionality of the application is to display a screen with buttons that respond to actions (and it is the main function!), I built this to handle other features that I wanted or thought would make the 
1. Powerful and configurable when customizations are needed
2. Multiple Display screen (Meus, Dialogs, Splash) types.
3. Support for built-in screen blanking (customizable for each display)
4. Wake up on touch or hardware button press (including from system screen blank)
5. Controllable backlight support for PWM, ECHO and STMPE methods
6. Support for PiTFT's with hardware buttons
7. Adjustable dimming when using PWM for backlight
8. On/Off backlight support when using PWM for sound playback
9. Support for Adafruit's Power Button GPIO with detection
10. Built in soft button templates for 13 soft button configurations
11. Displays built on a 320x480 screen will work on a 240x320 screen
12. Customizable button render order (multiple combinations of left-right and top-bottom)
13. Shell support without having to exit menu
14. Multiple text alignments for buttons/text/headers (left, center, right, top, middle, bottom)
15. Support for right-clicking buttons.
16. Full color support for borders, backgrounds and button borders
17. Button "down" visual indications.
18. Ability to call custom functions on button presses and refresh events
19. Built in support for date, time, host name in headers and footers

## Installing
[Coming Soon]

## Creating First Display
[Coming Soon]

## Advanced Display Features
[Coming Soon]

## Planned Enhancements

This is my first Python project I have ever done.  I'm sure there are lots of places where my old C# habits kicked in that would make a Pythonista cringe.  For that I am sorry.  If anyone using this finds any of those snippets, feel free to point those places out to me and once I understand the underlying reasons, I'll happily improve them.  Especially for a performance boost.  That said, there is also additional functionally in the planning stages that is documented below.  This list is somewhat prioritized, but subject to change based on any feedback I get.

In addition, I plan to go back and re-add comments and logging back in.   I stripped most of these areas out so I could get the project posted until I could go back and address my overly cryptic comments and logging into something that someone could possibly understand.

1. Re-add understandable comments to source code. (20% complete)
2. Add more (configurable) splash items for warnings, errors, information etc.
3. Add more logging for operation and debugging
4. Move the GPIO Buttons into a template similar to the Display Buttons templates.
4. Make header/footer types and their functionality into tokens that can be used in text.
5. Add images/icons to buttons
6. Move internal text to resources for use with gettext and improve globalization.
