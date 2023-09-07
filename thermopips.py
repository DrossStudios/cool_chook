# A draft attempt to use time-of-year, time-of-day, & tempurature to control lights (directly or via AC/DC relays) & fans

from machine import ADC, Pin, PWM
from time import time

class Temps:
	'''This class manages all temprature-themed variables, functions, formatting, etc.'''
	
	volt = ADC(4)
	fahrenheit = True
	therm = 0
	easyread = ""

	def fetch(self):
		volts = self.volt.read_u16()*(3.3/65536)
		if not self.fahrenheit:
			self.temp = 27-(volts-0.706)/0.001721
		else:
			# temp = 32+(1.8*(27-(volts-0.706)/0.00172))
			self.temp = 32+(48.6-1.8*(volts-0.706)/0.00172)
		return
	# end of method
	
	def format(self):
		if self.fahrenheit:
			self.easyread = f"{self.temp}{chr(176)}F"
		else:
			self.easyread = f"{self.temp}{chr(176)}C"
		return
	# end of method
# End of Class

class PWM_Dev():
	'''Individual PWM device and it's trigger values'''
	def __init__(self, pin, temp_on, temp_off, seas_on, seas_off):
		self.pin_id = PWM(Pin(pin))
		self.pin_id.freq(1500)
		self.pin_id.duty_u16(32767)
		self.fan_max = temp_on
		self.fan_off = temp_off
		self.season_on = seas_on
		self.season_off = seas_off
	# end of method

	def temp_ref(self, temp_check):
		if temp_check >= self.fan_off: self.pin_id.duty_u16(65535)
		elif temp_check <= self.fan_off: self.pin_id.duty_u16(0)
		else: self.pin_id.duty_u16(32767)

# End of Class

### Initiate things
log_file_name = ""
Temp = Temps()
Push = PWM_Dev(12,85,65,"Summer","Autumn")

while True:
	Temp.fetch()
	# Push.temp_ref(Temp.therm)
	Push.temp_ref(100)
