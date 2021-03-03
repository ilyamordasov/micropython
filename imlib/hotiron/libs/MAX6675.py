from machine import Pin
import utime
from FIR import FIR

class MAX6675():

    def __init__(self, cs=14, so=12, sck=27):

        #Thermocouple
        self.cs = Pin(cs, Pin.OUT)
        self.cs.high()

        self.so = Pin(so, Pin.IN)
        self.so.low()

        self.sck = Pin(sck, Pin.OUT)
        self.sck.low()

        self.last_read_time = 0
        self.last_read_temp = 0
        self.last_error_tc = 0

        self.FIR = FIR(20)

    def millis():
        return int(round(utime.time() * 1000))


    def read(self):
        #check if new reading should be available
        #if True:
        if millis()-self.last_read_time > 220:

            #/*
            #  Bring CS pin low to allow us to read the data from
            #  the conversion process
            #*/
            self.cs.low()

            #/* Cycle the clock for dummy bit 15 */
            self.sck.high()
            utime.sleep_ms(1)
            self.sck.high()

            #/*
            # Read bits 14-3 from MAX6675 for the Temp. Loop for each bit reading
            #   the value and storing the final value in 'temp'
            # */
            value = 0
            for i in range(12):
                self.sck.high()
                read = self.so.value()
                read = (read << 12 - i)
                value += read
                self.sck.low()


            #/* Read the TC Input inp to check for TC Errors */
            self.sck.high()
            error_tc = self.so.value()
            self.sck.low()

            # /*
            #   Read the last two bits from the chip, faliure to do so will result
            #   in erratic readings from the chip.
            # */
            for i in range(2):
                self.sck.high()
                utime.sleep_ms(1)
                self.sck.low()

            self.cs.high()

            self.FIR.push(value)
            temp = (value * 0.25)
            self.last_read_time = millis()
            self.last_read_temp = temp
            self.last_error_tc = error_tc

            return temp,error_tc

        #to soon for new reading
        else:
            return self.last_read_temp,self.last_error_tc