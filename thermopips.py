# A draft attempt to use time-of-year, time-of-day, & tempurature to control lights (directly or via AC/DC relays) & fans

from machine import ADC, Pin, PWM
from time import time
from ds1302 import DS1302

###### Borrowed Classes ######

###### Original Classes ######
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
### End of Class ###

class PWM_Dev():
	'''Individual PWM device and it's trigger values
	<instance name> PWM_Dev(
		pin, 
			-integer value, 1-16(?) for GPIO pin number
		temp_or_time,	
			-string, being "heat", "cool", or "time"
		_on_off,
			-tuple, containing either a pair of:
				integers (min and max temp readings)
				-or-
				a string ("day", "night", or "24") and an integer between 0 and 3600
				NOTE: in a string/integrr pair, negative (-) numbers will be treated as 0, and numbers >3600 will be treated as 3600
		seas_on,
			-tuple, containing 2 strings from the following 5: "spring", "summer", "autumn", "winter", "all"
				NOTE: during __init__, if either value is "all", the 1st will be rewritten as "all" and the 2nd will be null-string("")
		):'''
	def __init__(self,
			pin, 			# GPIO pin number
			temp_or_time,	# String: "heat", "cool", or "time"
			_on_off, 		# Tuple: 2 integers reresenting min/max temps; or a string ("day","night","24") and an integer (0-3600)
			seas_on,		# Tuple: any 2 ("spring", "summer", "autumn", "winter", "all")
			):
		self.pin_id = PWM(Pin(pin))
		self.pin_id.freq(300) # fan-specific; may need adjustment for other devices.
		self.pin_id.duty_u16(65535) # this number is the max value that can be used
		self.trigger_mode = temp_or_time.lower()
		if _on_off[0] > _on_off[1]: _on_off = (_on_off[1],_on_off[0])
		if self.trigger_mode == "cool":
			self.dev_on = _on_off[1]
			self.dev_off = _on_off[0]
		else:
			self.dev_on = _on_off[0]
			self.dev_off = _on_off[1]
		if seas_on[0].lower() == "all" or seas_on[1].lower() == "all":
			seas_on = ("all","")
		self.season_on = seas_on[0]
		self.season_off = seas_on[1]
	# end of method

	def temp_ref(self, temp_check):
		if temp_check >= self.dev_on: 
			self.pin_id.duty_u16(65535)
			print(f">{self.dev_on}") # test-line to be commented out after testing
		elif temp_check <= self.dev_off: 
			self.pin_id.duty_u16(1) 
			print(f"<{self.dev_off}") # test-line to be commented out after testing
		else: 
			self.pin_id.duty_u16(18878) # this number approximates 33% of 65535
			print("ideal") # test-line to be commented out after testing
	# end of method

	def time_ref(self, time_in):
		return
	# end of method

	def dev_check(self, temp_check, time_in):
		if self.trigger_mode == "time": self.time_ref(time_in)
		else: self.temp_ref(temp_check)
	# end of method

### End of Class ###

class Device_Info:
	'''establish basic device info and settings'''
	def __init__(self):
		'''If any additional items need to be added, use the following format:

		self.<device name> = PWM_Dev(
			pin, 
				-integer value, 1-16(?) for GPIO pin number
			temp_or_time,	
				-string, being "heat", "cool", or "time"
			_on_off,
				-tuple, containing either a pair of:
					integers (min and max temp readings)
					-or-
					a string ("day", "night", or "24") and an integer between 0 and 3600
					NOTE: in a string/integrr pair, negative (-) numbers will be treated as 0, and numbers >3600 will be treated as 3600
			seas_on,
				-tuple, containing 2 strings from the following 5: "spring", "summer", "autumn", "winter", "all"
					NOTE: during __init__, if either value is "all", the 1st will be rewritten as "all" and the 2nd will be null-string("")
		)'''
		self.Push 		= PWM_Dev(0, "cool", (70, 90), ("all", ""))
		self.Pull 		= PWM_Dev(2, "cool", (70, 90), ("all", ""))
		self.Circulation= PWM_Dev(4, "heat", (50, 80), ("all", ""))
		self.Heat 		= PWM_Dev(6, "heat", (35, 35), ("all", ""))
		self.Tan		= PWM_Dev(8, "time", ("day", 1800), ("summer", "autumn"))
		self.Light		= PWM_Dev(25, "time", ("day", 1800), ("all", ""))
		self.RTC 		= DS1302(Pin(11),Pin(12),Pin(13))
		self.RTC.start()
	# end of method

	def poll_dev(self, therm_in):
		# Add these steps:
		#	Check wheather the self.RTC.day boolean equals dev(?).day_cycle or dev(?).day_cycle = "24"
		#		if yes, validate settings according to therm_in
		self.Push.temp_ref(therm_in)
		self.Pull.temp_ref(therm_in)
		self.Circulation.temp_ref(therm_in)
		self.Heat.temp_ref(therm_in)
	# end of method
	
### End of Class ###

### Initiate things
log_file_name = ""
Temp = Temps()
Test_heat = PWM_Dev(0,"heat", (66,75), ("Summer","Autumn")) # 75 and 66 are code-testing values, because they're easily reproducable in-lab
Test_cool = PWM_Dev(0,"cool", (66,75), ("Summer","Autumn"))
Test_time = PWM_Dev(0,"time", ("day",30), ("Summer","Autumn"))
Coop = Device_Info()
# Comment-out these commands as-needed for proper configuration
#Coop.RTC.date_time([2023, 9, 20, 3, 9, 0, 0]) # set datetime for 20 Sep 2023, 09:00:00. (A Wednesday, the 4th day of the week >> value 3)

### Test-Code lines
print(Coop.RTC.date_time())
#while True:
#	Temp.fetch()
#	Coop.Push.temp_ref(Temp.therm)
#	Coop.poll_dev(Temp.therm)