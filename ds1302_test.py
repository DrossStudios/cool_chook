# Copy/Paste the contents of this file to main.py in order to check whether a ds1302 chip/board combo is functional or not
# NOTE: modify this file into a test-function to include in the ds1302.py file propper
from machine import Pin
from ds1302 import *
from time import *

ds = DS1302(Pin(12),Pin(13),Pin(14))
led = Pin(25, Pin.OUT)
led.value(0)

while True:
    yr_chk = int(ds.year())
    if yr_chk == 2165:
        led.value(1)
        sleep(1)
        led.value(0)
        sleep(1)
        #print(yr_chk)
    else:
        led.value(0)
        sleep(2)
        #print(yr_chk)
