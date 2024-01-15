from machine import Pin
from time import time

DS1302_REG_SECOND   = (0x80) # value given in hex; equivalent to 128
DS1302_REG_MINUTE   = (0x82) # value given in hex; equivalent to 130
DS1302_REG_HOUR     = (0x84) # value given in hex; equivalent to 132
DS1302_REG_DAY      = (0x86) # value given in hex; equivalent to 134
DS1302_REG_MONTH    = (0x88) # value given in hex; equivalent to 136
DS1302_REG_WEEKDAY  = (0x8A) # value given in hex; equivalent to 138
DS1302_REG_YEAR     = (0x8C) # value given in hex; equivalent to 140
DS1302_REG_WP       = (0x8E) # value given in hex; equivalent to 142
DS1302_REG_CTRL     = (0x90) # value given in hex; equivalent to 144
DS1302_REG_RAM      = (0xC0) # value given in hex; equivalent to 192

# NOTE: In my not-so-humble opinion, the in-file/in-line documentation in this module suuuuucks! To that end, all in-file/in-line 
# comments and tripple-quote documentation are my own additions as I work to understand each function and how to best utilize it

# NOTE: Error traceback, for some reason, will go to the last good, non-blank like (this may mean it directs you to a comment-line, 
# when the issue is the next coded line down). Not sure exactly why that is (maybe it's a VS-Code idiosyncrocy?), but something to be 
# aware of.

class DS1302:
    '''A module to enable a microcontroller board running micropython to utilize the ds1302 chip on a 5-pin board using a trickle-
    -charged CR2032 button battery for memory permanence. The original code was pulled from [https://github.com/omarbenhamid/micropython-ds1302-rtc/tree/master]
    and has been modified to supply documentation that is lacking in the original source.
    '''
    def __init__(self, clk, dio, cs):
        '''Initialize the micro-board pin-out details and output initial signals to RTC board'''
        self.clk = clk          # ID number of the "clock" pin
        self.dio = dio          # ID number of the DIO or "D.ata I.nput O.utput" pin
        self.cs = cs            # ID number of the CS/RST or "" pin
        self.clk.init(Pin.OUT)
        self.cs.init(Pin.OUT)

    def _dec2hex(self, deci):
        '''Take in decimal data and return hexidecimal data'''
        return (deci//10) * 16 + (deci % 10)

    def _hex2dec(self, hexi):
        '''Take in hexidecimal data and return decimal data'''
        return (hexi//16) * 10 + (hexi % 16)

    def _write_byte(self, dat):
        '''Write bytes to the RTC chip'''
        self.dio.init(Pin.OUT)
        for i in range(8):
            self.dio.value((dat >> i) & 1)
            self.clk.value(1)
            self.clk.value(0)

    def _read_byte(self):
        '''Read bytes from the RTC chip'''
        d = 0
        self.dio.init(Pin.IN)
        for i in range(8):
            d = d | (self.dio.value() << i) # d = the binary of previous-d and the value of self.dio where at least one bit = 1, after 
            # self.dio has had its bits shifted left i places
            self.clk.value(1)               # turn the clock-pin on
            self.clk.value(0)               # turn the clock-pin off
        return d                            # output the fully-compiled binary "d"

    def _get_reg(self, reg):
        '''Get information from the given registry'''
        self.cs.value(1)        # turn on the CS/RST pin
        self._write_byte(reg)   # use the passed-in registry to write something to the RTC chip
        t = self._read_byte()   # read-back from the chip and output the value to "t"
        self.cs.value(0)        # turn off the CS/RST pin
        return t                # return the value of "t" to the call-point in the program

    def _set_reg(self, reg, dat):
        '''Set the given registry with new value info'''
        self.cs.value(1)
        self._write_byte(reg)
        self._write_byte(dat)
        self.cs.value(0)

    def _wr(self, reg, dat):
        ''''''
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
        '''Either set (if an integer-argument is given) or return (if *no* argument is given) the seconds-value'''
        if second == None:
            step_1 = DS1302_REG_SECOND+1
            print(step_1)
            step_2 = self._get_reg(step_1)
            print(step_2)
            step_3 = self._hex2dec(step_2)
            print(step_3)
            step_4 = step_3 % 60
            print(step_4)
            return step_4
            # return self._hex2dec(self._get_reg(DS1302_REG_SECOND+1)) % 60 # original code
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
            return [self.year(), self.month(), self.day(), self.weekday(), self.hour(), self.minute(), self.second()] # added self.day_cycle (defined below)
        else:
            self.year(dat[0])
            self.month(dat[1])
            self.day(dat[2])
            self.weekday(dat[3])
            self.hour(dat[4])
            self.minute(dat[5])
            self.second(dat[6])
            #self.day_cycle(dat[4])  # custom code: use hours to hammer-meets-brick determine "daytime" vs "nighttime"
            #self.season(dat[1])     # custom code: use month to hammer-meets-brick determine "spring," "summer," "autumn," or "winter"

    def ram(self, reg, dat=None):
        if dat == None:
            return self._get_reg(DS1302_REG_RAM + 1 + (reg % 31)*2)
        else:
            self._wr(DS1302_REG_RAM + (reg % 31)*2, dat)
    
    ### Custom Functions
    def day_cycle(self, day=None):
        '''Custom function to help approximate a day/night cycle, rather than force users into calculating it themselves. 
        Location agnostic.'''
        hour_of_day = int(self.hour(day))
        if hour_of_day >= 6 and hour_of_day < 18: self.daytime = "day"
        else: self.daytime = "night"
    # end of method

    def season(self, month=None):
        '''Custom function to help approximate a 4-seasons cycle, rather than force users into calculating it themselves. 
        Location agnostic.'''
        #print(month)
        what_month = (int(self.month(month)) % 13) + 1
        #print(what_month)
        if what_month >= 3 and what_month < 6: return "spring"
        elif what_month >= 6 and what_month < 9: return "summer"
        elif what_month >= 9 and what_month < 12: return "autumn"
        else: return "winter"

# End of Class

### Test Lines ###
# Initiate the test instance
print(DS1302_REG_SECOND)
ds = DS1302(Pin(12),Pin(13),Pin(14))
print(DS1302_REG_SECOND)
ds.date_time([2002, 1, 1, 1, 0, 0, 55]) # [year, month, date, day-of-week, hour, minute, second]
print(DS1302_REG_SECOND)

# specific code-lines
print(ds.date_time())
print(ds.second())
#for i in range(60):
#    print(ds.second())
    
