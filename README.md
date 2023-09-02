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
