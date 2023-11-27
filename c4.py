from machine import ADC, Pin, PWM, RTC
from utime import sleep, sleep_us

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
		self.format()
		#print(self.easyread) # test line; comment-out before final production-release
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
				a string ("day", "night", or "24") and an integer between 0 and 3599
				NOTE: in a string/integrr pair, negative (-) numbers will be treated as 0, and numbers >3599 will be treated as 3599
		seas_on,
			-tuple, containing 2 strings from the following 5: "spring", "summer", "autumn", "winter", "all"
				NOTE: during __init__, if either value is "all", the 1st will be rewritten as "all" and the 2nd will be null-string("")
		):'''
	def __init__(self,
			pin, 			# GPIO pin number
			temp_or_time,	# String: "heat", "cool", or "time"
			_on_off, 		# Tuple: 2 integers reresenting min/max temps; or a string ("day","night","24") and an integer (0-3599)
			seas_on,		# Tuple: any 2 ("spring", "summer", "autumn", "winter", "all")
			):
		self.pin_id = PWM(Pin(pin))
		self.pin_id.freq(300) # fan-specific; may need adjustment for other devices.
		self.pin_id.duty_u16(65535) # this number is the max value that can be used
		self.trigger_mode = temp_or_time.lower()
		self.fade_end = "0:0"
		if type(_on_off[0]) == int and _on_off[0] > _on_off[1]: _on_off = (_on_off[1],_on_off[0])
		if self.trigger_mode == "cool":
			self.dev_on = _on_off[1]
			self.dev_off = _on_off[0]
		elif self.trigger_mode == "time":
			pass
			#self.dev_on = _on_off[0]
			# calculate the fade-finish times as 0600hrs or 1800hrs + _on_off[1] -- hour % 12 == 6 then min >= (_on_off[1] // 60) then second >= _on_off[1] % 60
			#self.dev_off = _on_off[1]
			#self.fade_end = f"{_on_off[1]//60}:{_on_off[1]%60}"
		elif self.trigger_mode == "heat":
			self.dev_on = _on_off[0]
			self.dev_off = _on_off[1]
			self.fade_end = f"{_on_off[1]//60}:{_on_off[1]%60}"
		else: # heat
			self.dev_on = _on_off[0]
			self.dev_off = _on_off[1]
		if seas_on[0].lower() == "all" or seas_on[1].lower() == "all":
			seas_on = ("all","")
		self.season_on = seas_on[0]
		self.season_off = seas_on[1]
		self.fade_count = 0
	# end of method

	def cool_ref(self, temp_check):
		'''Compare temp sensor to settings, determine whether to turn on/down/off/up associated cooling device.'''
		if temp_check >= self.dev_on: 
			self.pin_id.duty_u16(65535)
			#print(f">{self.dev_on}") # test-line to be commented out after testing
		elif temp_check <= self.dev_off: 
			self.pin_id.duty_u16(1) 
			#print(f"<{self.dev_off}") # test-line to be commented out after testing
		else: 
			self.pin_id.duty_u16(18878) # this number approximates 33% of 65535
			#print("ideal") # test-line to be commented out after testing
	# end of method

	def heat_ref(self, temp_check):
		'''Compare temp sensor to settings, determine whether to turn on/down/off/up associated heating device.'''
		if temp_check <= self.dev_on: 
			self.pin_id.duty_u16(65535)
			#print(f">{self.dev_on}") # test-line to be commented out after testing
		elif temp_check >= self.dev_off: 
			self.pin_id.duty_u16(1) 
			#print(f"<{self.dev_off}") # test-line to be commented out after testing
		else: 
			self.pin_id.duty_u16(18878) # this number approximates 33% of 65535
			#print("ideal") # test-line to be commented out after testing
	# end of method

	def season(self, time_in):
		if time_in[1] >= 3 and time_in[1] < 6: return "spring"
		elif time_in[1] >= 6 and time_in[1] < 9: return "summer"
		elif time_in[1] >= 9 and time_in[1] < 12 : return "autumn"
		else: return "winter"
	# end of method

	def day_cycle(self, time_in):
		if time_in[4] >= 6 and time_in[4] < 18: return "day"
		else: return "night"

	def time_ref(self, time_in):
		'''Compare RTC value(s) to settings, determine whether the associated device needs its fade phase to be advanced, if said phase is complete, or if said phase needs to be triggered.'''
		if self.season_on == self.season(time_in) or self.season_on == "all":
			if self.dev_on == "24": # all-day, everyday during this season
				self.pin_id.duty_u16(65535)
			elif self.dev_on == self.day_cycle(time_in) and self.fade_count <= self.dev_off: # The time is "now" but the fade is still progressing
				# progressively adjust .duty_u16() from 1 to 65535 in ratios of seconds from first all-true instance until .dev_off's
				# value in seconds has passed.
				# NOTE: calculations *must* allow for an immediate jump from 1 to 65535 if the fade rate (.def_off) is 0
				
				pass
			elif self.dev_on == self.day_cycle(time_in) and self.fade_count > self.dev_off: # The time is "now" and the fade is done
				self.pin_id.duty_u16(65535)
			elif self.dev_on != self.day_cycle(time_in) and self.fade_count > 0: # The time is "not now" but the fade needs to process
				# exact reverse-process of elif-statement above, with same NOTE requirement
				
				pass
			else: self.pin_id.duty_u16(1)
		else: self.pin_id.duty_u16(1)
	# end of method

	def dev_check(self, temp_check, time_in):
		'''A uniform function that any device can be plugged into, and then use it's settings to determine which sub-function is needed to handle its resolution.'''
		if self.trigger_mode == "time": self.time_ref(time_in)
		elif self.trigger_mode == "heat": self.heat_ref(temp_check)
		elif self.trigger_mode == "cool": self.cool_ref(temp_check)
		else: LogMe.record_error(f"device-check failure:\n{self}", time_in)
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
					a string ("day", "night", or "24") and an integer between 0 and 3599
					NOTE: in a string/integrr pair, negative (-) numbers will be treated as 0, and numbers >3599 will be treated as 3599
			seas_on,
				-tuple, containing 2 strings from the following 5: "spring", "summer", "autumn", "winter", "all"
					NOTE: during __init__, if either value is "all", the 1st will be rewritten as "all" and the 2nd will be null-string("")
		)'''
		self.Tan		= PWM_Dev(0, "time", ("day", 1800), ("summer", "autumn"))	# P-0
		self.Light		= PWM_Dev(2, "time", ("day", 1800), ("all", "")) 			# P-1
		self.Circulation= PWM_Dev(4, "heat", (50, 80), ("all", "")) 				# P-2
		self.Push 		= PWM_Dev(6, "cool", (70, 90), ("all", "")) 				# P-3
		self.Pull 		= PWM_Dev(8, "cool", (70, 90), ("all", "")) 				# P-4
		self.Heat 		= PWM_Dev(10, "heat", (25, 25), ("all", "")) 				# P-5
		self.DeIce		= PWM_Dev(12, "heat", (35, 35), ("all", "")) 				# P-6
		self.RTCmod 	= RTC()
	# end of method

	def poll_dev(self, therm_in, time_in):
		'''Polls all PWM-configured devices'''
		self.Push.dev_check(therm_in, time_in)
		self.Pull.dev_check(therm_in, time_in)
		self.Circulation.dev_check(therm_in, time_in)
		self.Heat.dev_check(therm_in, time_in)
		self.DeIce.dev_check(therm_in, time_in)
		self.Tan.dev_check(therm_in, time_in)
		self.Light.dev_check(therm_in, time_in)
	# end of method

	# Correlation of datetime() indexies and what they represent
	# 0 year
	# 1 month
	# 2 date
	# 3 day of the week (Monday is the 1st index, 0)
	# 4 hour in 24hr cycle
	# 5 minute
	# 6 second
	# 7 microsecond

	def season(self, time_in):
		if time_in[1] >= 3 and time_in[1] < 6: return "spring"
		elif time_in[1] >= 6 and time_in[1] < 9: return "summer"
		elif time_in[1] >= 9 and time_in[1] < 12 : return "autumn"
		else: return "winter"
	# end of method

	def day_cycle(self, time_in):
		if time_in[4] >= 6 and time_in[4] < 18: return "day"
		else: return "night"
### End of Class ###

class Logger:
	'''Logging functions, including error logging when errors are raised and handled, and hourly temprature logging.'''
	def __init__(self, time_in):
		self.therm_log = "/log/therm_log.txt"
		self.run_error_log = "/log/run_errors_log.txt"
		try:
			log_test = open(self.run_error_log, "r")
		except OSError as add_error:
			with open(self.therm_log, "w") as msg_in:
				print("Mid-run Errors Log", file=msg_in)
		else:
			log_test.close()
		try:
			log_test = open(self.therm_log, "r")
		except OSError as add_error:
			self.record_error(f"Hourly thermals log missing:\n{add_error}\nFile created", time_in)
			with open(self.therm_log, "w") as msg_in:
				print("Thermal Readings Log", file=msg_in)
		else:
			log_test.close()
		self.test_value = ""
	# end of method

	def nice_time(self, time_in):
		if isinstance(time_in, tuple):
			output = f"{time_in[2]} "
			if time_in[2] == 1: output += "Jan, "
			elif time_in[2] == 2: output += "Feb, "
			elif time_in[2] == 3: output += "Mar, "
			elif time_in[2] == 4: output += "Apr, "
			elif time_in[2] == 5: output += "May, "
			elif time_in[2] == 6: output += "Jun, "
			elif time_in[2] == 7: output += "Jul, "
			elif time_in[2] == 8: output += "Aug, "
			elif time_in[2] == 9: output += "Sep, "
			elif time_in[2] == 10: output += "Oct, "
			elif time_in[2] == 11: output += "Nov, "
			elif time_in[2] == 12: output += "Dec, "
			else: output+= "M??, "
			output += f"{time_in[4]}:"
			if len(str(time_in[5])) == 1: output += f"0{time_in[5]}:"
			else: output += f"{time_in[5]}:"
			if len(str(time_in[6])) == 1: output += f"0{time_in[5]}"
			else: output += f"{time_in[5]}"
			return output
		else: return time_in
	# end of method

	def record_error(self, error_in, time_in):
		time_in = self.nice_time(time_in)
		with open(self.run_error_log, "a") as msg_in:
			print(f"{time_in}: {error_in}\n", file=msg_in)
	# end of method

	def poll_log(self, dev_in, therm_in, time_in):
		'''A clone of poll_dev(), but also logs the changes (if any)'''
		msg_out = f"{self.nice_time(time_in)}\n"
		## Push fan
		self.test_value = dev_in.Push.pin_id.duty_u16()
		dev_in.Push.dev_check(therm_in, time_in)
		if self.test_value != dev_in.Push.pin_id.duty_u16(): msg_out += f"'Push fan' experienced a change: {self.test_value} to {dev_in.Push.pin_id.duty_u16()}\n"
		
		## Pull fan
		self.test_value = dev_in.Pull.pin_id.duty_u16()
		dev_in.Pull.dev_check(therm_in, time_in)
		if self.test_value != dev_in.Push.pin_id.duty_u16(): msg_out += f"'Push fan' experienced a change: {self.test_value} to {dev_in.Push.pin_id.duty_u16()}\n"
		
		## Circulation fan
		self.test_value = dev_in.Circulation.pin_id.duty_u16()
		dev_in.Circulation.dev_check(therm_in, time_in)
		if self.test_value != dev_in.Push.pin_id.duty_u16(): msg_out += f"'Push fan' experienced a change: {self.test_value} to {dev_in.Push.pin_id.duty_u16()}\n"
		
		## Heat relay
		self.test_value = dev_in.Heat.pin_id.duty_u16()
		dev_in.Heat.dev_check(therm_in, time_in)
		if self.test_value != dev_in.Push.pin_id.duty_u16(): msg_out += f"'Push fan' experienced a change: {self.test_value} to {dev_in.Push.pin_id.duty_u16()}\n"
		
		## De-Icing relay
		self.test_value = dev_in.DeIce.pin_id.duty_u16()
		dev_in.DeIce.dev_check(therm_in, time_in)
		if self.test_value != dev_in.Push.pin_id.duty_u16(): msg_out += f"'Push fan' experienced a change: {self.test_value} to {dev_in.Push.pin_id.duty_u16()}\n"
		
		## Tanning UV LED's
		self.test_value = dev_in.Tan.pin_id.duty_u16()
		dev_in.Tan.dev_check(therm_in, time_in)
		if self.test_value != dev_in.Push.pin_id.duty_u16(): msg_out += f"'Push fan' experienced a change: {self.test_value} to {dev_in.Push.pin_id.duty_u16()}\n"
		
		## Lighting LED's
		self.test_value = dev_in.Light.pin_id.duty_u16()
		dev_in.Light.dev_check(therm_in, time_in)
		if self.test_value != dev_in.Push.pin_id.duty_u16(): msg_out += f"'Push fan' experienced a change: {self.test_value} to {dev_in.Push.pin_id.duty_u16()}\n"
	# end of method

	def record_change(self, msg_in, time_in):
		time_in = self.nice_time(time_in)
		with open("/log/state_changes.log", "a") as update:
			print(f"{time_in}: {msg_in}", file=update)
	# end of method

	def time_out(self, time_in):
		with open("last_time.txt", "w") as updating:
			string_out = ""
			for i in time_in:
				string_out += f"{i} "
			print(string_out, file=updating)
	# end of method

	def record_therms(self, therm_in, time_in):
		# For this specific method, it is assumed that the therm_in argument has been pre-formatted for the given system (F vs C)
		# log output without <degree-symbol>F/C attached to a temp record is due to the formatting either being broken or unused.
		with open("/log/therm_log.txt", "a") as therm_out:
			print(f"{time_in}: {therm_in}", file=therm_out)
	# end of method
# end of class
