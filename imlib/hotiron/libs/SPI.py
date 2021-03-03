from machine import Pin

class SPI():
    def __init__(self, cs = 'X10', sck = 5, miso = 2, mosi = 13, delay = 10):
        self.cs = Pin(cs, Pin.OUT)
        self.cs.high()

        self.miso = Pin(miso, Pin.IN)
        self.mosi = Pin(mosi, Pin.OUT)

        self.sck = Pin(sck, Pin.OUT)
        self.delay = delay



    def write(self,data):
        self.cs.low()
        pyb.udelay(self.delay)
        self._write(data)
        self.cs.high()

    def read(self,read_addr,nr_bytes):
        buf = bytearray(1)
        buf[0]=read_addr
        self.cs.low()
        pyb.udelay(self.delay)
        self._write(buf)
        result = self._read(nr_bytes)
        self.cs.high()
        return result

    def _read(self,nr_bytes):
        buf = bytearray(nr_bytes)

        for b in range(nr_bytes):
            byte = 0
            for i in range(8):
                self.sck.high()
                pyb.udelay(self.delay)
                read = self.miso.value()
                read = (read << 8 - i)
                byte += read
                self.sck.low()
                pyb.udelay(self.delay)
            buf[b]=byte

        return buf

    def _write(self,data):
        msb = 0b10000000

        for byte in data:
            bits = [(byte<<i&msb)/128 for i in range(8)]
            for b in bits:
                if b:
                    self.mosi.high()
                else:
                    self.mosi.low()
                self.sck.high()
                pyb.udelay(self.delay)
                self.sck.low()
                pyb.udelay(self.delay)

        self.mosi.low()