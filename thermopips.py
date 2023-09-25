# A draft attempt to use time-of-year, time-of-day, & tempurature to control lights (directly or via AC/DC relays) & fans

from machine import ADC, Pin, PWM
from time import time
from ds1302 import DS1302

###### Borrowed Classes ######
# These variables are defined for use in the DS1302 class. See in-Class comment for source data
DS1302_REG_SECOND = (0x80)
DS1302_REG_MINUTE = (0x82)
DS1302_REG_HOUR   = (0x84)
DS1302_REG_DAY    = (0x86)
DS1302_REG_MONTH  = (0x88)
DS1302_REG_WEEKDAY= (0x8A)
DS1302_REG_YEAR   = (0x8C)
DS1302_REG_WP     = (0x8E)
DS1302_REG_CTRL   = (0x90)
DS1302_REG_RAM    = (0xC0)


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
	'''Individual PWM device and it's trigger values'''
	def __init__(self, pin, temp_off, temp_on, seas_on, seas_off, day_cyc, cool):
		self.pin_id = PWM(Pin(pin))
		self.pin_id.freq(5000)
		self.pin_id.duty_u16(65535) # this number is the max value that can be used
		self.fan_max = temp_on
		self.fan_off = temp_off
		self.season_on = seas_on
		self.season_off = seas_off
		self.cooling = cool
		self.day_cycle = day_cyc
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

### End of Class ###

class Device_Info:
	'''establish basic device info and settings'''
	def __init__(self):
		'''If any additional items need to be added, use the following format:

		self.<device name> = PWM_Dev(

			<An integer without quotes; the GPIO pin number used to control the device>,

			<An integer without quotes; the lowest trigger-temprature>,

			<An integer without quotes; the highest trigger-temprature>,

			<A capitalized string in quotes, using one of the 5: All, Winter, Spring, Summer, Autumn. The start of the season 
			activates the device>,

			<A capitalized string in quotes, using one of the 5: All, Winter, Spring, Summer, Autumn. The start of the season 
			deactivates the device>,

			<A boolean value; True activates the device at the highest trigger-tempreature and deactivates it at the lowest 
			trigger-temprature; False reverses this arrangement>
		)'''
		self.Push 		= PWM_Dev(0, 70, 90, "Spring", "Autumn", "24", True)
		self.Pull 		= PWM_Dev(2, 70, 90, "Spring", "Autumn", "24", True)
		self.Circulation= PWM_Dev(4, 50, 80, "Autumn", "Spring", "24", False)
		self.Heat 		= PWM_Dev(6, 35, 35, "Autumn", "Spring", "24", False)
		self.RTC 		= DS1302(Pin(10),Pin(11),Pin(12))
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
Test = PWM_Dev(0,66,75,"Summer","Autumn","24",True) # 75 and 66 are code-testing values, because they're easily reproducable in-lab
Coop = Device_Info()
# Comment-out these commands as-needed for proper configuration
#Coop.RTC.date_time([2023, 9, 20, 3, 9, 0, 0]) # set datetime for 20 Sep 2023, 09:00:00. (A Wednesday, the 4th day of the week >> value 3)

### Test-Code lines
print(Coop.RTC.date_time())
#while True:
#	Temp.fetch()
#	Coop.Push.temp_ref(Temp.therm)
#	Coop.poll_dev(Temp.therm)