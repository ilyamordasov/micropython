# CC1101 driver for MicroPython on ESP32
# MIT license; Copyright (c) 2021 Ilya Mordasov

from machine import SPI, Pin
import utime
import urandom
import ubinascii
import math
import esp32
#import ccc1101 as cc1101

class Defines(object):
    # PA table 
    PA_TABLE = bytearray({0x00,0x60,0x00,0x00,0x00,0x00,0x00,0x00})

    # PATABLE & FIFO's
    PATABLE = 0x3E      # PATABLE address
    TXFIFO = 0x3F       # TX FIFO address
    RXFIFO = 0x3F       # RX FIFO address

    # Command strobes
    SRES = 0x30         # Reset CC1101 chip
    SFSTXON = 0x31      # Enable and calibrate frequency synthesizer (if MCSM0.FS_AUTOCAL=1). If in RX (with CCA):
                        # Go to a wait state where only the synthesizer is running (for quick RX / TX turnaround).
    SXOFF = 0x32        # Turn off crystal oscillator
    SCAL = 0x33         # Calibrate frequency synthesizer and turn it off. SCAL can be strobed from IDLE mode without
                        # setting manual calibration mode (MCSM0.FS_AUTOCAL=0)
    SRX = 0x34          # Enable RX. Perform calibration first if coming from IDLE and MCSM0.FS_AUTOCAL=1
    STX = 0x35          # In IDLE state: Enable TX. Perform calibration first if MCSM0.FS_AUTOCAL=1.
                        # If in RX state and CCA is enabled: Only go to TX if channel is clear
    SIDLE = 0x36        # Exit RX / TX, turn off frequency synthesizer and exit Wake-On-Radio mode if applicable
    SWOR = 0x38         # Start automatic RX polling sequence (Wake-on-Radio) as described in Section 19.5 if
                        # WORCTRL.RC_PD=0
    SPWD = 0x39         # Enter power down mode when CSn goes high
    SFRX = 0x3A         # Flush the RX FIFO buffer. Only issue SFRX in IDLE or RXFIFO_OVERFLOW states
    SFTX = 0x3B         # Flush the TX FIFO buffer. Only issue SFTX in IDLE or TXFIFO_UNDERFLOW states
    SWORRST = 0x3C      # Reset real time clock to Event1 value
    SNOP = 0x3D         # No operation. May be used to get access to the chip status byte

    # CC1101 configuration registers
    IOCFG2 = 0x00       # GDO2 Output Pin Configuration
    IOCFG1 = 0x01       # GDO1 Output Pin Configuration
    IOCFG0 = 0x02       # GDO0 Output Pin Configuration
    FIFOTHR = 0x03      # RX FIFO and TX FIFO Thresholds
    SYNC1 = 0x04        # Sync Word, High Byte
    SYNC0 = 0x05        # Sync Word, Low Byte
    PKTLEN = 0x06       # Packet Length
    PKTCTRL1 = 0x07     # Packet Automation Control
    PKTCTRL0 = 0x08     # Packet Automation Control
    ADDR = 0x09         # Device Address
    CHANNR = 0x0A       # Channel Number
    FSCTRL1 = 0x0B      # Frequency Synthesizer Control
    FSCTRL0 = 0x0C      # Frequency Synthesizer Control
    FREQ2 = 0x0D        # Frequency Control Word, High Byte
    FREQ1 = 0x0E        # Frequency Control Word, Middle Byte
    FREQ0 = 0x0F        # Frequency Control Word, Low Byte
    MDMCFG4 = 0x10      # Modem Configuration
    MDMCFG3 = 0x11      # Modem Configuration
    MDMCFG2 = 0x12      # Modem Configuration
    MDMCFG1 = 0x13      # Modem Configuration
    MDMCFG0 = 0x14      # Modem Configuration
    DEVIATN = 0x15      # Modem Deviation Setting
    MCSM2 = 0x16        # Main Radio Control State Machine Configuration
    MCSM1 = 0x17        # Main Radio Control State Machine Configuration
    MCSM0 = 0x18        # Main Radio Control State Machine Configuration
    FOCCFG = 0x19       # Frequency Offset Compensation Configuration
    BSCFG = 0x1A        # Bit Synchronization Configuration
    AGCCTRL2 = 0x1B     # AGC Control
    AGCCTRL1 = 0x1C     # AGC Control
    AGCCTRL0 = 0x1D     # AGC Control
    WOREVT1 = 0x1E      # High Byte Event0 Timeout
    WOREVT0 = 0x1F      # Low Byte Event0 Timeout
    WORCTRL = 0x20      # Wake On Radio Control
    FREND1 = 0x21       # Front End RX Configuration
    FREND0 = 0x22       # Front End TX Configuration
    FSCAL3 = 0x23       # Frequency Synthesizer Calibration
    FSCAL2 = 0x24       # Frequency Synthesizer Calibration
    FSCAL1 = 0x25       # Frequency Synthesizer Calibration
    FSCAL0 = 0x26       # Frequency Synthesizer Calibration
    RCCTRL1 = 0x27      # RC Oscillator Configuration
    RCCTRL0 = 0x28      # RC Oscillator Configuration
    FSTEST = 0x29       # Frequency Synthesizer Calibration Control
    PTEST = 0x2A        # Production Test
    AGCTEST = 0x2B      # AGC Test
    TEST2 = 0x2C        # Various Test Settings
    TEST1 = 0x2D        # Various Test Settings
    TEST0 = 0x2E        # Various Test Settings

    # Status registers
    PARTNUM = 0x30              # Chip ID
    VERSION = 0x31              # Version Number
    FREQEST = 0x32              # Frequency Offset Estimate from Demodulator
    LQI = 0x33                  # Demodulator Estimate for Link Quality
    RSSI = 0x34                 # Received Signal Strength Indication
    MARCSTATE = 0x35            # Main Radio Control State Machine State
    WORTIME1 = 0x36             # High Byte of WOR Time
    WORTIME0 = 0x37             # Low Byte of WOR Time
    PKTSTATUS = 0x38            # Current GDOx Status and Packet Status
    VCO_VC_DAC = 0x39           # Current Setting from PLL Calibration Module
    TXBYTES = 0x3A              # Underflow and Number of Bytes
    RXBYTES = 0x3B              # Overflow and Number of Bytes
    RCCTRL1_STATUS = 0x3C       # Last RC Oscillator Calibration Result
    RCCTRL0_STATUS = 0x3D       # Last RC Oscillator Calibration Result 

class CC1101():
    def __init__(self, spi = None, gd0 = None, gd2 = None, cs = None):
        assert spi is not None, 'You have to init SPI first'
        self.device = spi
        self.so = Pin(21, Pin.IN, Pin.PULL_UP)
        self.gd0 = Pin(18, Pin.OUT) if gd0 == None else Pin(gd0, Pin.OUT)
        self.gd2 = Pin(19, Pin.OUT) if gd2 == None else Pin(gd2, Pin.OUT)
        self.cs = Pin(17, Pin.OUT, value=1) if cs == None else Pin(cs, Pin.OUT)
        self.rmt = None

        self.pulse_t = 0
        self.pulse_w = 0
        self._start_h = 0
        self._arr = []
        self.code = 0
        self._cnt = 0

        # for __grab2()
        self.high_start = 0
        self.low_start = 0
        self.high_us = 0
        self.low_us = 0
        self.period_width = 0
        self.period_diff = 0
        self.grace = 0
        self.last_period = 0

    def dummy(self, p):
        pass
    
    def cc1101_cb(self, value):
        self.txrx_cb(value)
    
    def readGDO2(self, pin = None):
        _pin = Pin(19 if pin is None else pin, Pin.IN)
        _pin.irq(self.dummy, Pin.IRQ_FALLING | Pin.IRQ_RISING)
        readGDO(19 if pin is None else pin, self.cc1101_cb)
        print("Pin GDO2 is installed to INPUT")

    def readGDO0(self, pin = None, length = None):
        _pin = Pin(18 if pin is None else pin, Pin.IN)
        _pin.irq(self.dummy, Pin.IRQ_FALLING | Pin.IRQ_RISING)
        readGDO(18 if pin is None else pin, self.cc1101_cb, 64 if length is None else length)
        print("Pin GDO0 is installed to INPUT")
        #self.gd0.irq(trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING, handler = self.__grab)

    def setCallback(self, func = None):
        self.txrx_cb = func if func is not None else None

    def __test22(self, pin):
        print("IRQ FROM PY %d" % pin)

    def __grab(self, pin, len = 64):
        # if pulse is wide then 0 else 1
        value = pin.value()
        tick = utime.ticks_us()
        if value is 1:
            if self._start_h != 0:
                self.pulse_t = utime.ticks_diff(tick, self._start_h)
                self._start_h = utime.ticks_us() # tick
                if self.pulse_t > 300:
                    if round(self.pulse_w) < round(self.pulse_t / 2):
                        self.code = (self.code << 1) | 0
                    else:
                        self.code = (self.code << 1) | 1
                    self._arr.append([self.pulse_w, self.pulse_t])
            else:
                self._start_h = utime.ticks_us()    
        else:
            if self._start_h != 0:
                self.pulse_w = utime.ticks_diff(utime.ticks_us(), self._start_h)
                self._cnt += 1

        if self._cnt >= len-1:
            self.pulse_t = 0
            self.pulse_w = 0
            self._start_h = 0
            print(self._arr)
            self._arr = []

            self.txrx_cb(self.code)
            
            self.code = 0
            self._cnt = 0

    def __grab2(self, pin, len = 64):
        value = pin.value()
        if value is 1:
            self.high_start = utime.ticks_us()
            self.low_us = utime.ticks_diff(utime.ticks_us(), self.low_start)
        elif value is 0:
            self.low_start = utime.ticks_us()
            self.high_us = utime.ticks_diff(utime.ticks_us(), self.high_start)
            bit = 1 if self.high_us > self.low_us else 0
            self.period_width = self.high_us + self.low_us
            self.period_diff = abs(self.last_period - self.period_width)
            self.grace = self.period_width // 10
            if self.period_diff > self.grace:
                # start new code
                self._cnt = 0
                self.code = bit
            else:
                self._cnt += 1
                self.code <<= 1
                self.code |= 1 if bit else 0
            if self._cnt >= len-1:
                self.txrx_cb(self.code)
            self.last_period = self.period_width

    def _usDelay(self, useconds):
        utime.sleep(useconds / 1000000.0)

    def __marcstate(self, value):
        return ['SLEEP', 'IDLE', 'XOFF', 'VCOON_MC', 'REGON_MC', 'MANCAL', 'VCOON', 'REGON', 'STARTCAL', 'BWBOOST', 'FS_LOCK', 'IFADCON', 'ENDCAL', 'RX', 'RX_END', 'RX_RST', 'TXRX_SWITCH', 'RXFIFO_OVERFLOW', 'FSTXON', 'TX', 'TX_END', 'RXTX_SWITCH', 'TXFIFO_UNDERFLOW'][value]

    def selfTest(self):
        part_number = self.readSingleByte(Defines.PARTNUM)
        component_version = self.readSingleByte(Defines.VERSION)
        marcstate = self.getMRSatetMachineState()

        print("PARTNUM 0x%02X" % part_number)                                           # Waiting for 0
        print("VERSION 0x%02X" % component_version)                                     # Waiting for 0x14
        print("MARCSTATE 0x%02X (%s)" % (marcstate, self.__marcstate(marcstate)))       # Waiting for MARCSTATE

    def readSingleByte(self, address = None):
        assert address is not None, 'You have to point address'
        
        databuffer = bytearray(2)
        self.cs.off()
        self.device.write_readinto(bytearray([address | 0xC0, 0x00]), databuffer)
        self.cs.on()
        return databuffer[1]

    def readBurst(self, address = None, length = None):
        assert address is not None, 'You have to point address'
        assert length is not None, 'You have to point length'
        buff = []
        ret = []
        for x in range(length + 1):
            addr = (address + (x * 8)) | 0xC0
            buff.append(addr)
        ret = self.device.write(bytearray(buff))[1:]
        print("_readBurst | start_address = {:x}, length = {:x}".format(start_address, length))

        return ret

    def writeSingleByte(self, address = None, value = None):
        assert address is not None, 'You have to point address'
        assert value is not None, 'You have to point value'

        self.cs.off()
        self.device.write(bytearray([0x00 | address, value]))
        self.cs.on()

    def writeBurst(self, address = None, data = None):
        assert address is not None, 'You have to point address'
        assert data is not None, 'You have to point data'

        data.insert(0, (0x40 | address))
        self.cs.off()
        self.device.write(bytearray(data))
        self.cs.on()

    def strobe(self, address):
        assert address is not None, 'You have to point address'

        self.cs.off()
        self.device.write(bytearray([address, 0x00]))
        self.cs.on()

    def reset(self):
        self.cs.on()
        utime.sleep_us(5)
        self.cs.off()
        utime.sleep_us(10)
        self.cs.on()
        utime.sleep_us(41)
        self.cs.off()

        # Wait until MISO goes low
        # for  i in range(0,110)
        #     print(self.so.value())
        utime.sleep(1)
        self.cs.on()
        #utime.sleep(2)
        return self.strobe(Defines.SRES)

    def sidle(self):
        self.strobe(Defines.SIDLE)

        while (self.readSingleByte(Defines.MARCSTATE) != 0x01):
            self._usDelay(100)

        self.strobe(Defines.SFTX)
        self._usDelay(100)

    def powerDown(self):
        self.sidle()
        self.strobe(Defines.SPWD)

    def setCarrierFrequency(self, freq=433):
        # Register values extracted from SmartRF Studio 7
        if freq == 433:
            self.writeSingleByte(Defines.FREQ2, 0x10)
            self.writeSingleByte(Defines.FREQ1, 0xA7)
            self.writeSingleByte(Defines.FREQ0, 0x62)
        elif freq == 868:
            self.writeSingleByte(Defines.FREQ2, 0x21)
            self.writeSingleByte(Defines.FREQ1, 0x62)
            self.writeSingleByte(Defines.FREQ0, 0x76)
        else:
            raise Exception("Only 433MHz and 868MHz are currently supported")

    def setChannel(self, channel=0x00):
        self.writeSingleByte(Defines.CHANNR, channel)

    def setSyncWord(self, sync_word="FAFA"):
        assert len(sync_word) == 4

        self.writeSingleByte(Defines.SYNC1, int(sync_word[:2], 16))
        self.writeSingleByte(Defines.SYNC0, int(sync_word[2:], 16))

    def flushRXFifo(self):
        self.strobe(Defines.SFRX)
        self._usDelay(2)

    def flushTXFifo(self):
        self.strobe(Defines.SFTX)
        self._usDelay(2)

    def setTXState(self):
        self.strobe(Defines.STX)
        self._usDelay(2)

    def setRXState(self):
        self.strobe(Defines.SRX)
        self._usDelay(2)

    def getMRSatetMachineState(self):
        return (self.readSingleByte(Defines.MARCSTATE) & 0x1F)

    def getRSSI(self):
        return self.readSingleByte(Defines.RSSI)

    def sendRawData(self, code, low = 400, high = 800, repeat = 2):
        #code1 = (code1 << 16) + 257 * urandom.getrandbits(8)
        self.rmt = esp32.RMT(0, pin = self.gd0, clock_div = 8) if self.rmt is None else self.rmt
        preamble = [650, 250]
        if code is not None:
            pulse_t = [low, high]
            code_b = bin(code)
            for _ in range(0, repeat):
                for _ in range(12):
                    self.rmt.write_pulses((preamble[0]*10, preamble[1]*10), start=1)

                #utime.sleep_ms(2)
                #for _ in range(64 - len(code_b[2:])): self.rmt.write_pulses((pulse_t[1]*10, pulse_t[0]*10), start=1)
                code_arr = [0 for _ in range(64 - len(code_b[2:]))]
                for x in code_b[2:]:
                    code_arr.append(int(x))
                # code_arr.append(1)
                # code_arr.append(1)
                for i in code_arr:
                    pulse_t_tmp = pulse_t[::-1] if i is 0 else pulse_t
                    self.rmt.write_pulses((pulse_t_tmp[0]*10, pulse_t_tmp[1]*10), start=1)
                
                utime.sleep_ms(17)
            self.txrx_cb(code) if self.txrx_cb is not None else None
        else:
            raise Exception("You must point the code")


    def sendPacketData(self, data):
        self.setRXState()
        marcstate = self.getMRSatetMachineState()
        dataToSend = []

        while marcstate != 0x0D:
            print("marcstate = 0x%02X" % marcstate)
            print("waiting for marcstate = 0x0D")

            if marcstate == 0x11:
                self.flushRXFifo()
            marcstate = self.getMRSatetMachineState()
        
        if len(data) == 0:
            print("No data to send")
            return False
        
        data_len = len(data)

        if data_len > self.readSingleByte(Defines.PKTLEN):
            print("Length of data exceeds the configured packet len")
            return False

        # if self.readSingleByte(Defines.PKTCTRL1)[6:] != "00":
        #     dataToSend.append(self.readSingleByte(Defines.ADDR))

        dataToSend.extend(data)
        dataToSend.extend([0] * (self.readSingleByte(Defines.PKTLEN) - len(dataToSend)))

        print("Sending a fixed len packet")
        print("data len = %d" % data_len)
        print("{}".format(dataToSend))

        self.writeBurst(Defines.TXFIFO, dataToSend)
        self._usDelay(2000)
        self.setTXState()
        marcstate = self.getMRSatetMachineState()
        if marcstate not in [0x13, 0x14, 0x15]:
            self.sidle()
            self.flushTXFifo()
            self.setRXState()

            print("sendData | FAIL")
            print("sendData | MARCSTATE: 0x%02X (%s)" % (self.readSingleByte(Defines.MARCSTATE), self.__marcstate(marcstate)))
            return False
        
        remaining_bytes = self.readSingleByte(Defines.TXBYTES) & 0x7F
        while remaining_bytes != 0:
            self._usDelay(1000)
            remaining_bytes = self.readSingleByte(Defines.TXBYTES) & 0x7F
            print("Waiting until all bytes are transmitted, remaining bytes: %d" % remaining_bytes)

        if (self.readSingleByte(Defines.TXBYTES) & 0x7F) == 0:
            print("Packet sent!")
            return True
        else:
            print("{}".format(self.readSingleByte(Defines.TXBYTES) & 0x7F))
            print("sendData | MARCSTATE: 0x%02X" % self.getMRStateMachineState())
            self.sidle()
            self.flushTXFifo()
            utime.sleep(5)
            self.setRXState()
            return False