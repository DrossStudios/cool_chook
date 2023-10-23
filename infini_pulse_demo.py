from time import *
from machine import ADC, Pin, PWM

led = PWM(Pin(25)) # use the on-board LED to demonstrate the PWM pulse
led.freq(1000)
led.duty_u16(1)

while True:
    for i in range(65536):
        led.duty_u16(i)
        sleep(0.1)
    for i in range(65535, -1,-1):
        led.duty_u16(i)
        sleep(0.1)
