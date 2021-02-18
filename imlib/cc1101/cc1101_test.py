from machine import SPI, Pin
from cc1101 import Defines as defs
import cc1101
import utime

def RX_setValues():
    radio.writeSingleByte(defs.IOCFG2,0x0D)  #GDO2 Output Pin Configuration
    radio.writeSingleByte(defs.IOCFG0,0x0D)  #GDO0 Output Pin Configuration
    radio.writeSingleByte(defs.FIFOTHR,0x47) #RX FIFO and TX FIFO Thresholds
    radio.writeSingleByte(defs.PKTCTRL0,0x32)#Packet Automation Control
    radio.writeSingleByte(defs.FSCTRL1,0x06) #Frequency Synthesizer Control
    radio.writeSingleByte(defs.FREQ2,0x10)   #Frequency Control Word, High Byte
    radio.writeSingleByte(defs.FREQ1,0xB0)   #Frequency Control Word, Middle Byte
    radio.writeSingleByte(defs.FREQ0,0x71)   #Frequency Control Word, Low Byte
    radio.writeSingleByte(defs.MDMCFG4,0xF5) #Modem Configuration
    radio.writeSingleByte(defs.MDMCFG3,0x83) #Modem Configuration
    radio.writeSingleByte(defs.MDMCFG2,0x30) #0xB0) #Modem Configuration
    radio.writeSingleByte(defs.DEVIATN,0x15) #Modem Deviation Setting
    radio.writeSingleByte(defs.MCSM0,0x18)   #Main Radio Control State Machine Configuration
    radio.writeSingleByte(defs.FOCCFG,0x14) #0x16)  #Frequency Offset Compensation Configuration

    #
    radio.writeSingleByte(defs.AGCCTRL0,0x92)   #AGC Control
    #

    radio.writeSingleByte(defs.WORCTRL,0xFB) #Wake On Radio Control
    radio.writeSingleByte(defs.FREND0,0x11)  #Front End TX Configuration
    radio.writeSingleByte(defs.FSCAL3,0xE9)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.FSCAL2,0x2A)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.FSCAL1,0x00)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.FSCAL0,0x1F)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.TEST2,0x81)   #Various Test Settings
    radio.writeSingleByte(defs.TEST1,0x35)   #Various Test Settings
    radio.writeSingleByte(defs.TEST0,0x09)   #Various Test Settings

def rx_callback(code):
    print("Received: %d" % code)

PA_TABLE = [0x00,0x60,0x00,0x00,0x00,0x00,0x00,0x00]
spi = SPI(1, baudrate=2000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(22), mosi=Pin(23), miso=Pin(21))
radio = cc1101.CC1101(spi=spi, gd0=18)
radio.setCallback(func = rx_callback)
radio.reset()
RX_setValues()
radio.writeBurst(defs.PATABLE, PA_TABLE)
radio.sidle()
radio.selfTest()
print("CC1101 radio initialized for RX\r\n")
radio.setRXState()
radio.readGDO0(length = 10)
#radio.readGDO2()