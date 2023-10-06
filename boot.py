'''This file contains tests, imports, and logs required to ensure a smooth run every time'''

try:
    with open("log_file.txt", "a") as log_file:
        # append date/time for boot, and any errors above
        pass
except FileNotFoundError: 
    # create the log file and provide it's initial data
    pass
except:
    # unknown error reporting  