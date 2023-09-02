import time
from machine import ADC, Pin, PWM

led = Pin(25, Pin.OUT)
led.value(1)

