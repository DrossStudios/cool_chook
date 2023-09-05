# A draft attempt to use time-of-year, time-of-day, & tempurature to control lights (directly or via AC/DC relays) & fans

from machine import ADC, Pin, PWM
from time import time

class Temps:
	'''This class manages all temprature-themed variables, functions, formatting, etc.'''
	
	therm = ADC(4)
	fahrenheit = True

	def fetch_temp(self):
		volts = self.therm.read_u16()*(3.3/65536)
		if not self.fahrenheit:
			temp = 27-(volts-0.706)/0.001721
		else:
			# temp = 32+(1.8*(27-(volts-0.706)/0.00172))
			temp = 32+(48.6-1.8(volts-0.706)/0.00172)
