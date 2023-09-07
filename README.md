# cool_chook
To control chicken-coop climate based on thermal sensors and presumed time-of-year.


## Minimum Requirements
* Raspberry Pi Pico-W -or- Raspberry Pi Pico with WIZNet Ethernet HAT -or- WIZNet Pico
* UV LED
* Relay that can power-on/-off 120VAC circuits with an activation voltage of 3.3VDC or 5VDC
* Fan, 3.3-12VDC
* Heat lamp, 120VAC
* Wire
* 330 Ohmm resisters, x?
* Bread-board for mounting components

## Additional/Ideal components
* Access to a 3D printer (to fab weather-resistant housing(s) for components)
* More fans (for a push-pull arrangement, plus any other air-circulation schemes)
* More UV LED's, 4x (for varied UV availability)
* Relay duplicate(s) (for individually-controlled 120VAC circuits and/or blood-sacrifices)
* Solenoids and/or stepper-motors (for extra/fancy climate-control options)
* RTC module
* External thermal sensor(s) (for additional thermal control points)
* White LED(s) (for illumination in an otherwise dark area)

## Project Scope
Use the RPi Pico's built-in thermal sensor and internal clock to determine whether the heat-lamp and/or fans should be on or off, and to what intensity the UV LED(s) should be set based on time-of-year (more during the winter months, less/none during summer).

## Steps
### Code
* it's in-progress

### Hardware
[https://europe1.discourse-cdn.com/arduino/original/4X/a/8/b/a8bd36c195356699119cfc0a6035746bc159f546.jpeg]
[https://noctua.at/pub/media/wysiwyg/faqs/noctua_pin_configuration_5v_fans.png]
* Well, I have confirmed through trial and error that a 12V fan will power directly off the Pico's 5V bus, but with only a 3-pin connector, there's no controlling the fan speed. People with tons more experience/knowledge than I can now commence screaming, "I coulda told you that!" But, being that's an unhelpful comment, I don't care what they say. If, however, someone reading has a step-by-step guide on how to control the speed of a 3-pin PC fan (presumably 12V) from a Pico, with or without powering the two separately, I'll take that in-lieu of condecension.

Diagram     -   Nomenclature    -   This Build
* Black     -   Ground/Earth    -   Purple
* Red       -   +12V power      -   Red
* Yellow    -   Sensor          -   White