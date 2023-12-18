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
				NOTE: during __init__(), if either value is "all", the 1st will be rewritten as "all" and the 2nd will be null-string("")
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
			self.dev_on = _on_off[1] # high value means high temp, thus "turn on cooling fans"
			self.dev_off = _on_off[0] # low temp means "turn off cooling"
			# side note: the gap between low and high 
		elif self.trigger_mode == "time":
			pass
			self.dev_on = _on_off[0] # has a string-value of "day", "night", or "24"
			if _on_off[1] > 0:
				self.dev_off = ((6+_on_off[1])//3600, _on_off[1]//60, _on_off[1]%60) # hours, minutes, seconds
			else: 
				self.dev_off = (0, 0, 0) # i.e. "immediately, no fade"
		elif self.trigger_mode.lower() == "heat":
			self.dev_on = _on_off[0] # low value means low temp, thus "turn on heat relay"
			self.dev_off = _on_off[1] # high temps
		else: # heat
			self.dev_on = _on_off[0]
			self.dev_off = _on_off[1]
		if seas_on[0].lower() == "all" or seas_on[1].lower() == "all":
			seas_on = ("all","")
		self.season_on = seas_on[0]
		self.season_off = seas_on[1]
		self.fade_count = 0
	# end of method

	def cool_ref(self, temp_check, log):
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

	def heat_ref(self, temp_check, log):
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
		
		# Test Line
		print(f"time_in[hour]: {time_in[4]}\ndaytime? {(time_in[4] >= 6, time_in[4] < 18, time_in[4] >= 6 and time_in[4] < 18)}")
		if time_in[4] >= 6 and time_in[4] < 18: return "day"
		else: return "night"
	# end of method

	def time_ref(self, time_in, log):
		'''Compare RTC value(s) to settings, determine whether the associated device needs its fade phase to be advanced, if said phase is complete, or if said phase needs to be triggered.'''
		if self.dev_on == self.dev_on.upper(): # device is currently fading in/out
			if time_in[4] in (self.dev_off[0]+6, self.dev_off[0]+18): # has the fade-in/-out reached the goal hour?
				if self.dev_off[1] == time_in[5]: # has the fade-in/-out reached the goal minute?
					if self.dev_off[2] == time_in[6]: # has the fade-in/-out reached the goal second?
						if self.dev_on.lower() == self.day_cycle(time_in): # the trigger_mode matches the current daytime phase
							self.pin_id.duty_u16(65535) # the device is now fully "on"
						else:
							self.pin_id.duty_u16(1) # the device is fully "off"
						self.dev_on = self.dev_on.lower()
			now_secs = time_in[4]*3600 + time_in[5]*60 + time_in[6] # value ranges are 21600-28799 or 64800-71999
			if now_secs >= 64800: now_secs -= 43200 # render the number of seconds as from 12am (0600:00 - 0759:59)
			change_secs = self.dev_off[0]*3600 + self.dev_off[1]*60 + self.dev_off[2]
			goal_secs = change_secs + 21600 # value range is between 21600-28799
			try: # take the diff between goal & now; calc the decimal percentage of progress
				fade_progress = (goal_secs - now_secs) / change_secs
			except:
				fade_progress = 0

			# Test Line
			print(f"goal: {goal_secs}\t- now: {now_secs}\t- progress: {fade_progress*100}%")
			print(f"Are dev_on ({self.dev_on.lower()}) and day_cycle ({self.day_cycle(time_in)}) equal? {self.dev_on.lower() == self.day_cycle(time_in)}")
			
			if self.dev_on.lower() == self.day_cycle(time_in): # is the daytime cycle in sync with the device's settings?
				# if yes, increase .duty_u16 closer to 65535
				self.pin_id.duty_u16(65535 - int(65535 * fade_progress))
			else: # if not, decrease .duty_u16 closer to 1
				if int(65535 * fade_progress) > 0:
					self.pin_id.duty_u16(int(65535 * fade_progress))
				else:
					self.pin_id.duty_u16(1)

			# Test Line
			print(self.pin_id.duty_u16())

		elif self.dev_on == self.dev_on.lower(): # device is not currently in fade-in/-out			
			
			# Test Line
			print("Made it to mode re-definition")
			
			self.dev_on = self.dev_on.upper()
	# end of method

	def dev_check(self, temp_check, time_in, log):
		'''A uniform function that any device can be plugged into, and then use it's settings to determine which sub-function is needed to handle its resolution.'''
		if self.trigger_mode == "time": self.time_ref(time_in, log)
		elif self.trigger_mode == "heat": self.heat_ref(temp_check, log)
		elif self.trigger_mode == "cool": self.cool_ref(temp_check, log)
		else: log.record_error(f"device-check failure:\n{self}", time_in)
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
					NOTE: during __init__(), if either value is "all", the 1st will be rewritten as "all" and the 2nd will be null-string("")
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

	def poll_dev(self, therm_in, time_in, log):
		'''Polls all PWM-configured devices'''
		self.Push.dev_check(therm_in, time_in, log)
		self.Pull.dev_check(therm_in, time_in, log)
		self.Circulation.dev_check(therm_in, time_in, log)
		self.Heat.dev_check(therm_in, time_in, log)
		self.DeIce.dev_check(therm_in, time_in, log)
		self.Tan.dev_check(therm_in, time_in, log)
		self.Light.dev_check(therm_in, time_in, log)
	# end of method
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
### End of Class ###

class TMan:
	'''A function for accessing and testing the various system components from the command-line of an attached computer
	<documentation of commands subsequently available after initially running the function>'''
	def __init__(self):
		self.ManTest = Device_Info()
		if self.ManTest.RTCmod.datetime()[0] != 2023: self.ManTest.RTCmod.datetime((2023,1,1,7,12,0,0,0))
		sleep(0.1)
		init_hr = self.ManTest.RTCmod.datetime()[4]
		self.TTemp = Temps()
		self.TLog = Logger(self.ManTest.RTCmod.datetime())
		self.help = f"Choose a parameter to change. If you already know what value you want to change it to, you may enter that value as well\nwith a comma separating them.\n\tExample:'>>> Pin ID, 7'\n Command Options (capitalization doesn't matter):\n\t[duty]\t[fade test]\t[frequency]\t[pin id]\t[quit]\t[sim temp]/[st]\t[sim time]/[sc]\n[d]uty\t\t- change the PWM duty-cycle (8-bit based voltage fraction) from 1-65535.\n[f]ade test\t- run a 30-second test of the PWM-fade code, to ensure it is working perfectly. System will be unresponsive until the\n\t\t\ttest is complete.\n[fr]equency\t- change the PWM frequency.\n[h]elp\t\t- re-display this menu.\n[p]in id\t\t- change the GPIO pin number (Note: use of odd-numbers *should* result in false-negatives; positive test results\n\t\t\tindicate a wiring problem).\n[q]uit\t\t- duh.\nsim temp\t- use an artificial temprature reading to check for propper device response.\nsim time\t- use an artificial seed-time to simulate activity in a different time phase (example being running 'nighttime' function\n\t\t\ttesting during daytime without changing device values or waiting for nighttime)."
		self.TEnv = Device_Info()
		while True: # get the pin ID from the user
			try:
				pinID = int(input("Pin number? "))
			except:
				print("Please use integers")
			else: 
				break
		while True: # get the desired type
			dev_type = input("Choose one of the following operating modes:\n1. 'heat'\n2. 'cool'\n3. 'time'").lower().strip()
			try:
				dev_type = int(dev_type)
			except:
				if dev_type not in ('heat','cool','time'): print("Invalid response. Please try again.")
				else: break
			else:
				if 0 > dev_type > 3: print("Invalid response. Please try again.")
				else: 
					if int(dev_type) == 1: dev_type = 'heat'
					elif int(dev_type) == 2: dev_type = 'cool'
					else: dev_type = 'time'
					break
		while True: # get the starting state
			on_off = input("Start with the device 'on' or 'off'? ").lower().strip()
			if on_off not in ("on", "off"): print("Invalid response. Try again")
			else: break
		print("Setting up device")

		# NOTE: need to add a block here to assign appropriate values to the _on_off tuple based on the value of on_off above
		# 	- for "heat", if "off" use a high temp set; if "on" use a very low temp
		# 	- for "cool", swap the high/low settings for "heat"
		# 	- for "time", compare ManTest.RTCmod.datetime() to "on"/"off" (if it's daytime and "on", set to "day"; etc.) and use fade-value of 30 
		if dev_type == "heat" and on_off == "off": f_on_off = (80,80)
		elif dev_type == "heat" and on_off == "on": f_on_off = (40,40)
		elif dev_type == "cool" and on_off == "off": f_on_off = (40,80)
		elif dev_type == "cool" and on_off == "on": f_on_off = (80,120)
		elif dev_type == "time" and on_off == "on":
			if init_hr in range(6,17): f_on_off = ("day",30)
			else: f_on_off = ("night", 30)
		else:
			if init_hr in range(6,17): f_on_off = ("night",30)
			else: f_on_off = ("day", 30)
		self.TDev = PWM_Dev(pinID, dev_type, f_on_off, ("all",""))
	
	def go(self):
		print(self.help)
		while True: # testing loop - runs till user quits
			beaking = input("Enter your testing option: ").lower()
			if beaking in ("quit","q"):	break
			elif beaking in ("help","h"): print(self.help)
			elif beaking in ("fade","f"):
				# check for compatibility
				if self.TDev.trigger_mode.lower() != "time": 
					print(f"Sorry, device-type is incorrect:\nIs: '{self.TDev.trigger_mode}'; needs to be: 'time'.")
					continue 
				# get current duty value
				Fade_Time = RTC()
				Fade_Time.datetime((2023, 1, 1, 7, 6, 0, 0, 0)) # (yr, mo, date, day-o-wk, hr, min, sec, subsec)
				# run the test itself
				force_break = 0
				while True:
					time_in = Fade_Time.datetime()
					self.TDev.time_ref(time_in, self.TLog)
					if self.TDev.dev_on.lower() == self.TDev.dev_on: # i.e. *not* all-caps
						break
					sleep(0.1)
					force_break += 1
					if force_break == 300:
						break
			elif beaking in ("frequency","fr"):
				print(f"Current device frequency: {self.TDev.pin_id.freq()} Hz")
				while True:
					try:
						new_data = int(input("New device frequency: "))
					except:
						print("Invalid entry. Please enter an integer...")
					else:
						break
				self.TDev.pin_id.freq(new_data)
			elif beaking in ("duty","d"):
				print(f"Current device duty: {self.TDev.pin_id.duty_u16()}:65535")
				while True:
					try:
						new_data = int(input("New device duty: "))
						if 1 > new_data > 65535: raise ValueError
					except:
						print("Invalid entry. Please enter an integer between 1 and 65535...")
					else:
						break
				self.TDev.pin_id.duty_u16(new_data)
			elif beaking in ("pin id","p"):
				# create a clone of the previous TDev, but with a new pin ID
				pass
			elif beaking in ("sim temp","st"):
				# artificially set a fake thermal reading and use that instead of the Pico's thermal sensor input
				while True:
					try:
						fake_temp = int(input("Please enter a tempurature value: "))
					except:
						print("Please use only numerals (and a '.' if you want to enter a decimal)")
					else:
						break
				if self.TDev.trigger_mode.lower() == "heat": self.TDev.heat_ref(fake_temp, self.TLog)
				elif self.TDev.trigger_mode.lower() == "cool": self.TDev.cool_ref(fake_temp, self.TLog)
			elif beaking in ("sim time","sc"):
				# artificially set a fake clock-value for the device to test against. Doesn't modify the RTC values; merely fits the format of RTC.datetime()
				pass
