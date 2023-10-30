from machine import Pin, PWM
from ds1302 import *
from utime import *

led = PWM(Pin(0))
led.freq(1000)
led.duty_u16(1)

while True:
    for i in range(65536):
        led.duty_u16(i)
        sleep(0.0001)
    for i in range(65535, -1,-1):
        led.duty_u16(i)
        sleep(0.0001)
