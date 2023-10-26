'''This file contains tests, imports, and logs required to ensure a smooth run every time'''
from machine import Pin, ADC, PWM
from time import sleep, sleep_us
from datetime import datetime, date, time,

bootmsg = ""
errmsg = ""

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
        # tuple passed to date_time is: (year, month, date, day of week, hour, minute, second)
        # system default renders Monday as the 1st day of the week (0), not Sunday.
        if ds.year() == 2165:
            ds.date_time((2023, 10, 26, 3, 13, 0, 0))
        if ds.year() == 2165:
            raise ValueError("DS1302 hardware faulty/missing")
    except ValueError as add_error:
        errmsg += f"Hardware Error:\n{add_error}\n\n"
    try:
        ds.year() == datetime.now().strftime("%Y")
    except NameError as add_error:
        try:
            open("last_time.txt", "r")
        except FileNotFoundError as add_error:
            errmsg += f"FileNotFoundError: last_time.txt\n{add_error}\n\n"
            datetime(2023, 10, 26, 14, 0, 0)
            with open("last_time.txt", "w") as time_backup:
                print(f"{date.year} {date.month} {date.day} {datetime.hour} {datetime.minute} {datetime.second}", file=time_backup)
        else:
            with open("last_time.txt", "w") as time_backup:
                time_in = time_backup.read().split()
                datetime(time_in[0], time_in[1], time_in[2], time_in[3], time_in[4], time_in[5], time_in[6])
    else:
        if ds.year() != datetime.now().strftime("%Y"):
            datetime(ds.year(), ds.month(), ds.day(), ds.hour(), ds.minute(), ds.second())
# done trying to get the time clock to a reasonably accurate time

try:
    open("boot_log.txt", "a")
except FileNotFoundError as add_error: 
    # create the log file and provide it's initial data
    errmsg += f"FileNotFoundError: boot_log.txt missing; file created\n{add_error}\n\n"
    with open("boot)log.txt", "w") as bootlog:
        print(f"Cool Chooks Climate Controller\nBoot Log\n")
except Exception as add_error:
    # unknown error reporting
    errmsg += f"Unexpected Error:\n{add_error}\n\n"
finally:
    with open("boot_log.txt", "a") as bootlog:
        boot_out = f"{datetime.now()} - Boot cycle complete\n"
        if errmsg == "": boot_out += f"Errors:\nNone"
        else: boot_out += f"Errors:\n{errmsg}"
        print(boot_out, file = bootlog)