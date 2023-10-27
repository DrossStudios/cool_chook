'''This file contains tests, imports, and logs required to ensure a smooth run every time'''
from machine import Pin, ADC, PWM, RTC
from utime import sleep, sleep_us
#from datetime import datetime, date, time # can't actually use datetime in uPy without manually loading the lib

bootmsg = ""
errmsg = ""
rtc = RTC()

try:
    from ds1302 import DS1302
except ImportError as add_error:
    errmsg += f"ImportError: ds1302.py missing\n{add_error}\n\n"
    # Need to figure out how to import datetime in a way that it replaces ds1302. 
    # NOTE: being that I have manually ensured ds1302.py is *not* missing, this can be dealt with later 
except Exception as add_error:
    errmsg += f"Unexpected Error:\n{add_error}\n\n"
    # most likely, this would be due to something within the ds1302.py 
else:
    try:
        ds = DS1302(Pin(12),Pin(13),Pin(14))
        # tuple passed to ds1302.date_time is: (year, month, date, day of week, hour, minute, second)
        # NOTE: system default renders Monday as the 1st day of the week (0), not Sunday; changing this is a future QOL goal
        if ds.year() == 2165:
            ds.date_time((2023, 10, 26, 3, 13, 0, 0))
        if ds.year() == 2165:
            raise ValueError("DS1302 hardware faulty/missing")
    except ValueError as add_error:
        errmsg += f"Hardware Error:\n{add_error}\n\n"
    try:
        ds.year() == rtc.datetime()[0] # type: ignore
    except NameError as add_error:
        try:
            open("last_time.txt", "r")
        except FileNotFoundError as add_error:
            errmsg += f"FileNotFoundError: last_time.txt\n{add_error}\n\n"
            rtc.datetime((2023, 10, 26, 0, 14, 0, 0, 0))
            with open("last_time.txt", "w") as time_backup:
                date_now = rtc.datetime()
                # date/time tuple sequence is as follows: (year, month, day, weekday, hours, minutes, seconds, subseconds)
                print(f"{date_now[0]} {date_now[1]} {date_now[2]} {date_now[3]} {date_now[4]} {date_now[5]} {date_now[6]} {date_now[7]}", file=time_backup)
        else:
            with open("last_time.txt", "w") as time_backup:
                time_in = time_backup.read().split()
                rtc.datetime(time_in[0], time_in[1], time_in[2], time_in[3], time_in[4], time_in[5], time_in[6], time_in[7])
    else:
        if ds.year() != rtc.datetime()[1]: # type: ignore
            rtc.datetime((ds.year(), ds.month(), ds.day(), ds.weekday, ds.hour(), ds.minute(), ds.second(), 0)) # type: ignore
# done trying to get the time clock to a reasonably accurate time

try:
    open("boot_log.txt", "a")
except FileNotFoundError as add_error: 
    # create the log file and provide it's initial data
    errmsg += f"FileNotFoundError: boot_log.txt missing; file created\n{add_error}\n\n"
    with open("boot_log.txt", "w") as bootlog:
        print(f"Cool Chooks Climate Controller\nBoot Log\n", file=bootlog)
except Exception as add_error:
    # unknown error reporting
    errmsg += f"Unexpected Error:\n{add_error}\n\n"
finally:
    with open("boot_log.txt", "a") as bootlog:
        boot_out = f"{rtc.datetime()} - Boot cycle complete\n" # type: ignore
        if errmsg == "": boot_out += f"Errors:\nNone"
        else: boot_out += f"Errors:\n{errmsg}"
        print(boot_out, file = bootlog)