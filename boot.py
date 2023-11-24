'''This file contains tests, imports, and logs required to ensure a smooth run every time'''
from machine import Pin, ADC, PWM, RTC
from utime import sleep, sleep_us
#from datetime import datetime, date, time # can't actually use datetime in uPy without manually loading the lib

rtc = RTC()

# variables for testing
boot_bldr = "boot_build.txt"
with open(boot_bldr, "w") as tester:
    print("created 'msg' variables and RTC instance\n", file=tester)

def boot_build(msg_in):
    with open(boot_bldr, "a") as tester:
        print(f"{msg_in}\n", file=tester)
# end of function

### Phase 0: create the log-recording function(s)
def boot_errors(error_in, msg_in=""):
    with open("/log/boot_log.txt","a") as recorder:
        print(f"Error Caught: {error_in}\n{msg_in}", file=recorder)
##### Phase 0: Setup "nice boot" environment
try:

    ### Phase 1: make sure the boot [error] logging file ('/log/boot_log.txt') exists; if not, create it
    try:   
        now_boot = open("/log/boot_log.txt", "a")
    except OSError as add_error: 
        # Test-line to trace the program's progress
        boot_build("'boot_log.txt' didn't exist yet")
    
        # create the log file and provide it's initial data
        bootlog = open("/log/boot_log.txt", "w")
        print(f"Cool Chooks Climate Controller\nBoot Log\n", file=bootlog)
        bootlog.close()
    except Exception as add_error:
        # unknown error reporting
        boot_build(f"Unexpected Error:\n{add_error}\n")
        boot_errors(add_error, "Unexpected Error")
    else:
        now_boot.close()
    # end of phase 1

    ### Phase 2: make sure the thermal logging file (therm_log.txt) exists; if not, create it
    try:
        check_therm = open("/log/therm_log.txt", "r")
    except OSError as errmsg:
        boot_build("thermal-log missing")
        boot_errors(errmsg, f"'/log/therm_log.txt' missing\nCreating it...")
        with open("/log/therm_log.txt", "w") as fixing:
            print(f"Hourly temprature readings log:\n", file=fixing)
    else: 
        boot_build("thermal-log present")
        check_therm.close()
    # end of phase 2

    ### Phase 3: make sure the boot [error] logging file (run_error_log.txt) exists; if not, create it
    try:
        check_errlog = open("/log/run_errors_log.txt", "r")
    except OSError as errmsg:
        boot_build("errors-log missing")
        boot_errors(errmsg, f"'/log/run_errors_log.txt' missing\nCreating it...")
        with open("/log/run_errors_log.txt", "w") as fixing:
            print(f"Log of errors encountered while running:\n", file=fixing)
    else: 
        boot_build("errors-log present")
        check_errlog.close()
    # end of phase 3

    ### Phase 4: make sure the state-change log exists
    "/log/state_changes.log"
    try:
        check_errlog = open("/log/state_changes.log", "r")
    except OSError as errmsg:
        boot_build("state-change log missing")
        boot_errors(errmsg, f"'/log/state_changes.log' missing\nCreating it...")
        with open("/log/state_changes.log", "w") as fixing:
            print(f"Log of changes to device states (turning on/off or idle):\n", file=fixing)
    else: 
        boot_build("state-change log present")
        check_errlog.close()
    # end of phase 4

    ### Phase 5: make sure the last_time.txt file exists; if not, create it
    try:
        check_last = open("last_time.txt", "r")
    except Exception as errmsg:
        boot_build("time back-up missing")
        boot_errors(errmsg, f"'last_time.txt' missing\nCreating it...")
        with open("last_time.txt", "w") as fixing:
            print("2023 11 15 3 15 3 0", file=fixing)
    else: 
        boot_build("time back-up present")
        check_last.close()
    # end of phase 5

    ### Phase 6: make sure the ds1302.py module exists:
    try:
        from ds1302 import DS1302
    except ImportError as errmsg:
        # ds1302.py is missing
        boot_build("ds1302.py missing")
        boot_errors(errmsg, "ds1302.py missing")
        # insert work-around code here
    except Exception as errmsg:
        # some other fatal error
        boot_build("Unexpected import error regarding ds1302.py")
        boot_errors(errmsg, "Unexpected import error regarding ds1302.py")
    else:
        boot_build("ds1302.py present and imported OK")
        # "theoretically," everything should work...
        try:
            boot_build("Trying to instantiate the DS1302 class")
            ds = DS1302(Pin(12),Pin(13),Pin(14))
            # tuple passed to ds1302.date_time is: (year, month, date, day of week, hour, minute, second)
            # NOTE: system default renders Monday as the 1st day of the week (0), not Sunday; changing this is a future QOL goal
            if ds.year() == 2165:
                boot_build("default year value is 2165; fixing...")
                ds.date_time((2023, 11, 15, 3, 15, 21, 0))
            if ds.year() == 2165:
                raise ValueError("DS1302 hardware faulty/missing")
        except ValueError as errmsg:
            # Despite attempts, ds1302 chip is unable to seed the pico RTC; using last_time.txt to seed time
            boot_build("Hardware Error - either the ds1302 chip/board is missing, or fatally faulted")
            boot_errors(errmsg, "Hardware Error - either the ds1302 chip/board is missing, or fatally faulted")
            # Now, bypass the ds1302 chip using the last_time.txt file
            with open("last_time.txt", "r") as time_backup:
                time_in = time_backup.read().split()
                for item in range(len(time_in)):
                    time_in[item] = int(time_in[item])
                if len(time_in) == 7: time_in.append(0)
                rtc.datetime(time_in)
                boot_build("Attempted to set rtc.datetime() according to last_time.txt")
        except Exception as errmsg:
            # sideways event
            boot_build("Unexpected Error - something sideways with instantiating DS1302()")
            boot_errors(errmsg, "Unexpected Error - something sideways with instantiating DS1302()")
        else:
            # working as expected; using the ds1302 datetime values to seed machine.RTC values
            boot_build("DS1302 loaded correctly, and ds1302 chip's date/time is (marginally) accurate.\nTrying to validate whether the machine.RTC Module and DS1302 Hardware agree")
            if rtc.datetime()[0] == ds.year:
                boot_build("rtc.datetime and ds.date_time (sufficiently) match")
            elif rtc.datetime()[0] == 2021:
                # if ds.year() != rtc.datetime()[0], use an exception to assign ds.date_time() values to rtc.datetime(<tuple>)
                boot_build("rtc.datetime's year value is default; using the values on the ds1302 chip to update it")
                rtc.datetime(ds.date_time())
    # end of phase 6
    
except Exception as errmsg:
    print(errmsg)
    with open("total_boot.fail", "w") as total_fail:
        print(errmsg, file=total_fail)

boot_build(f"Final boot-state complete at {rtc.datetime()}")