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
* Code for the ds1302 RTC module (chip, board, & battery) has been pulled from [here][https://github.com/omarbenhamid/micropython-ds1302-rtc/tree/master], but modified to replace the in-file documentation that is just straight-up absent in the original source, and to add brick-meets-skull tier day/night cycle functionality, and similar-tier 4-seasons functionality.
    - Contrary to the source's ReadMe file, one does not simply enter the given function commands in order to retrieve an output; you must either assign a variable whose value is equal to the output, and then utilize that, or you must use a print-statement.
    - In the brick-meets-skull tier additional functions, the basic breakdown is thus:
        - *"Day"* is any time whose hour is greater-than-or-equal-to 6, and less-than 18 (i.e. 6a.m. and 6p.m.); if an hour-value falls outside that range, it's *"Night."* This results in an exact 12-12 split and should be sufficient for basic and/or imprecise day/night tracking. 
        - *"Winter"* is counted as the entire months of December through February; *"Spring"* is counted as the entire months of March through May; *"Summer"* is counted as the entire months of June through August; *"Autumn"* is counted as the entire months of September through November. Where I am from, this seems a little ridiculous because "Spring" is shrunk down to the second half of April through the first half of May, while "Autumn" doesn't seem to kick-off until at least *mid-*September and ends mid-October unless the snows are late; but I also know some regions basically don't even *have* winter and summer, just "rain/monsoon" and "dry", so a 25%-25%-25%-25% split of the year between the seasons makes the most "uniform" sense.
        - Anything more specific than these, such as "local sunrise/sunset times" or "The First Day of Spring(tm)" will require something much more complex, and robust.
    - Some functions do not seem to operate immediately out-of-the-box, meaning that on-going testing and refinement will be required.
        - First thing of note is that once a function has been used to return a value, it needs to be "doctored" with modulo (%) in order to produce the correct output (annoying, but fixable during said refinements)
        - There is a non-0 chance that during one of the hardware builds, when I put the wires on in the wrong order, I fried something in the chip. I should order more, as well as check inventory for spare parts. Ideally, I source the chip-proper as well as the module boards, because the module boards are a separate failure point.
        

### Hardware
[https://europe1.discourse-cdn.com/arduino/original/4X/a/8/b/a8bd36c195356699119cfc0a6035746bc159f546.jpeg]
[https://noctua.at/pub/media/wysiwyg/faqs/noctua_pin_configuration_5v_fans.png]
* Well, I have confirmed through trial and error that a 12V fan will power directly off the Pico's 5V bus, but with only a 3-pin connector, there's no controlling the fan speed. People with tons more experience/knowledge than I can now commence screaming, "I coulda told you that!" But, being that's an unhelpful comment, I don't care what they say. If, however, someone reading has a step-by-step guide on how to control the speed of a 3-pin PC fan (presumably 12V) from a Pico, with or without powering the two separately, I'll take that in-lieu of condecension.
* Replacing the fan with a [Scyth 120mm 12V 4-pin PWM fan][https://www.newegg.com/scythe-su1225fd12mr-rhp-case-fan/p/1YF-0015-000G9?Item=9SIA9ZH8245025], I've been able to nail down the code for pinning and controlling the fan from a Pico
* Right now, the fans are being under-powered due to getting only 5V from 5vSys Bus. The plan is to eventually either:
    a. replace the fan with a Noctua 5V PWM fan
    b. add a 5v>12V buck converter in between the 5vSys Bus and the 12V fans
* The deciding factor ultimately will be whether 12V Fans x3 (approx. 0.39Amps) + 5V>12V Buck Converter (approx 1.4Amp capacity) is more or less expensive than Noctua 5V Fans x3
Diagram     -   Nomenclature    -   This Build
* Black     -   Ground/Earth    -   Purple
* Yellow    -   +12V power      -   Red (+5V)
* Green     -   RPM signal pin  -   Black
* Blue      -   +5V PWM signal  -   White (+3.3V)

