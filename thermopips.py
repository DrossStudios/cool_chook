# A draft attempt to use time-of-year, time-of-day, & tempurature to control lights (directly or via AC/DC relays) & fans

from machine import ADC, Pin, PWM
from time import time

class Device_Info:
	'''establish basic device info and settings'''
	file_name = "coop.conf"
	file_data = file_name.readlines()
	dev_list = []
	datable = False
	for item in file_data:
		if not datable and item[:5] = "-----": datable= True
		elif datable and item[:6].lower() = "example": break
		else:
			#use .split(",") and .strip() to reduce each line down to a dict with the first object appended to dev_list and then used to call an instance of PEM_Dev, with all other objects passed as arguments to the Class
	def poll_dev(self):
		for dev in self.dev_list
	
# End of Class

class Temps:
	'''This class manages all temprature-themed variables, functions, formatting, etc.'''
	
	volt = ADC(4) 		# on-board thermal sensor
	fahrenheit = True	# default setting - intended to be modified by a .conf file, if needed
	therm = 0			# default value, updated repeatedly during execution
	easyread = ""		# default blank line, updated whenever self.therm is updated

	def fetch(self):
		volts = self.volt.read_u16()*(3.3/65536)
		if not self.fahrenheit:
			self.therm = 27-(volts-0.706)/0.001721
		else:
			# temp = 32+(1.8*(27-(volts-0.706)/0.00172))
			self.therm = 32+(48.6-1.8*(volts-0.706)/0.00172)
		print(self.therm)
		return
	# end of method
	
	def format(self):
		if self.fahrenheit:
			self.easyread = f"{self.therm}{chr(176)}F"
		else:
			self.easyread = f"{self.therm}{chr(176)}C"
		return
	# end of method
# End of Class

class PWM_Dev():
	'''Individual PWM device and it's trigger values'''
	def __init__(self, pin, temp_off, temp_on, seas_on, seas_off):
		self.pin_id = PWM(Pin(pin))
		self.pin_id.freq(5000)
		self.pin_id.duty_u16(65535) # this number is the max value that can be used
		self.fan_max = temp_on
		self.fan_off = temp_off
		self.season_on = seas_on
		self.season_off = seas_off
	# end of method

	def temp_ref(self, temp_check):
		if temp_check >= self.fan_max: 
			self.pin_id.duty_u16(65535)
			print(f">{self.fan_max}")
		elif temp_check <= self.fan_off: 
			self.pin_id.duty_u16(1) 
			print(f"<{self.fan_off}")
		else: 
			self.pin_id.duty_u16(18878) # this number approximates 33% of 65535
			print("ideal")

# End of Class

### Initiate things
log_file_name = ""
Temp = Temps()
Push = PWM_Dev(0,66,75,"Summer","Autumn") # 75 and 66 are code-testing values, because they're easily reproducable in-lab


while True:
	Temp.fetch()
	Push.temp_ref(Temp.therm)

