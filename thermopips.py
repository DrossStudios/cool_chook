# A draft attempt to use time-of-year, time-of-day, & tempurature to control lights (directly or via AC/DC relays) & fans

from machine import ADC, Pin, PWM
#from time import time

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

class DS1302:
	'''Source: https://github.com/Guitarman9119/Raspberry-Pi-Pico-/blob/main/DS1302%20RTC/ds1302.py
	Downloaded approx. 9:45pm MDT, 19 Sep 2023.
	
	This class is used unmodified from the original state, except to include it directly in the main.py code instead of a
	separate module. The reason for this election is that when used in a separate module, functions such as (namely) 
	date_time() were returning errors as being undefined, which they clearly are. I can only assume this is a RAM overflow 
	issue, as when the code is included directly instead of imported, these errors do not occur.
	
	As this is not a class of my own creation, it does not have any of my conventions in naming or commenting.
	
	Additionally: the original file contents *are* stored in a ds1302.py module, for easy update and/or cross-compare if 
	ever needed.'''
	def __init__(self, clk, dio, cs):
		self.clk = clk
		self.dio = dio
		self.cs = cs
		self.clk.init(Pin.OUT)
		self.cs.init(Pin.OUT)

	def _dec2hex(self, dat):
		return (dat//10) * 16 + (dat % 10)

	def _hex2dec(self, dat):
		return (dat//16) * 10 + (dat % 16)

	def _write_byte(self, dat):
		self.dio.init(Pin.OUT)
		for i in range(8):
			self.dio.value((dat >> i) & 1)
			self.clk.value(1)
			self.clk.value(0)

	def _read_byte(self):
		d = 0
		self.dio.init(Pin.IN)
		for i in range(8):
			d = d | (self.dio.value() << i)
			self.clk.value(1)
			self.clk.value(0)
			return d

	def _get_reg(self, reg):
		self.cs.value(1)
		self._write_byte(reg)
		t = self._read_byte()
		self.cs.value(0)
		return t

	def _set_reg(self, reg, dat):
		self.cs.value(1)
		self._write_byte(reg)
		self._write_byte(dat)
		self.cs.value(0)

	def _wr(self, reg, dat):
		self._set_reg(DS1302_REG_WP, 0)
		self._set_reg(reg, dat)
		self._set_reg(DS1302_REG_WP, 0x80)

	def start(self):
		t = self._get_reg(DS1302_REG_SECOND + 1)
		self._wr(DS1302_REG_SECOND, t & 0x7f)

	def stop(self):
		t = self._get_reg(DS1302_REG_SECOND + 1)
		self._wr(DS1302_REG_SECOND, t | 0x80)

	def second(self, second=None):
		if second == None:
			return self._hex2dec(self._get_reg(DS1302_REG_SECOND+1)) % 60
		else:
			self._wr(DS1302_REG_SECOND, self._dec2hex(second % 60))

	def minute(self, minute=None):
		if minute == None:
			return self._hex2dec(self._get_reg(DS1302_REG_MINUTE+1))
		else:
			self._wr(DS1302_REG_MINUTE, self._dec2hex(minute % 60))

	def hour(self, hour=None):
		if hour == None:
			return self._hex2dec(self._get_reg(DS1302_REG_HOUR+1))
		else:
			self._wr(DS1302_REG_HOUR, self._dec2hex(hour % 24))

	def weekday(self, weekday=None):
		if weekday == None:
			return self._hex2dec(self._get_reg(DS1302_REG_WEEKDAY+1))
		else:
			self._wr(DS1302_REG_WEEKDAY, self._dec2hex(weekday % 8))

	def day(self, day=None):
		if day == None:
			return self._hex2dec(self._get_reg(DS1302_REG_DAY+1))
		else:
			self._wr(DS1302_REG_DAY, self._dec2hex(day % 32))

	def month(self, month=None):
		if month == None:
			return self._hex2dec(self._get_reg(DS1302_REG_MONTH+1))
		else:
			self._wr(DS1302_REG_MONTH, self._dec2hex(month % 13))

	def year(self, year=None):
		if year == None:
			return self._hex2dec(self._get_reg(DS1302_REG_YEAR+1)) + 2000
		else:
			self._wr(DS1302_REG_YEAR, self._dec2hex(year % 100))

	def date_time(self, dat=None):
		if dat == None:
			return [self.year(), self.month(), self.day(), self.weekday(), self.hour(), self.minute(), self.second()]
		else:
			self.year(dat[0])
			self.month(dat[1])
			self.day(dat[2])
			self.weekday(dat[3])
			self.hour(dat[4])
			self.minute(dat[5])
			self.second(dat[6])

	def ram(self, reg, dat=None):
		if dat == None:
			return self._get_reg(DS1302_REG_RAM + 1 + (reg % 31)*2)
		else:
			self._wr(DS1302_REG_RAM + (reg % 31)*2, dat)
### End of Class ###

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
	# end of method

	def poll_dev(self, therm_in):
		self.Push.temp_ref(therm_in)
		self.Pull.temp_ref(therm_in)
		self.Circulation.temp_ref(therm_in)
		self.Heat.temp_ref(therm_in)
	# end of method
	
### End of Class ###

### Initiate things
log_file_name = ""
Temp = Temps()
Test = PWM_Dev(0,66,75,"Summer","Autumn",True) # 75 and 66 are code-testing values, because they're easily reproducable in-lab
Coop = Device_Info()

#while True:
#	Temp.fetch()
#	Coop.Push.temp_ref(Temp.therm)
#	Coop.poll_dev(Temp.therm)

ds = DS1302(Pin(10),Pin(11),Pin(12))

ds.date_time() # returns the current datetime.
#ds.date_time([2023, 9, 19, 2, 22, 8, 0]) # set datetime for 19 Sep 2023, 22:08:00. (A Tuesday, the 3rd day of the week >> value 2)

print(ds.date_time())