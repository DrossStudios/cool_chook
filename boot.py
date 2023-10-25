'''This file contains tests, imports, and logs required to ensure a smooth run every time'''

bootmsg = ""
errmsg = ""

try:
    import ds1302
except ImportError:
    pass
    # write a py file that uses onboard RTC to mimic board
    # log this error
#except: other errors
#    log and (if able) correct
#else:
#    whatever's needed

try:
    bootlog = open("boot_log.txt", "a")
    # append date/time for boot, and any errors above
    pass
except FileNotFoundError: 
    # create the log file and provide it's initial data
    pass
except:
    # unknown error reporting  