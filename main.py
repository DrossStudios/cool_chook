from machine import ADC, Pin, PWM, RTC
from utime import sleep, sleep_us
from c4 import *

### Initiate things
log_file_name = ""
Temp = Temps()
Coop = Device_Info()
LogMe = Logger(Coop.RTCmod.datetime())

### Test-Code lines
#print(Coop.RTCmod.datetime())
#Test_heat = PWM_Dev(0,"heat", (66,75), ("Summer","Autumn")) # 75 and 66 are code-testing values, because they're easily reproducable in-lab
#Test_cool = PWM_Dev(0,"cool", (66,75), ("Summer","Autumn"))
#Test_time = PWM_Dev(0,"time", ("day",30), ("Summer","Autumn"))

### Execution lines
last_run = Coop.RTCmod.datetime()
while True:
	Temp.fetch()
	pull_now = Coop.RTCmod.datetime()
	Coop.poll_dev(Temp.therm, pull_now, LogMe)
	if pull_now[4] > last_run[4]:
		Temp.format()
		LogMe.record_therms(Temp.easyread, pull_now)
	last_run = pull_now
	LogMe.time_out(pull_now)
