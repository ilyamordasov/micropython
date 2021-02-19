# CC1101 test file for MicroPython on ESP32
# MIT license; Copyright (c) 2021 Ilya Mordasov

from machine import SPI, Pin
from cc1101 import Defines as defs
import cc1101
import utime


def TX_setDefaultValues():
    print("init CC1101 configuration...")
    # Copy your configuratuion from TI RF Studio

    # Address Config = No address check 
    # Base Frequency = 433.919830 
    # CRC Autoflush = false 
    # CRC Enable = false 
    # Carrier Frequency = 433.919830 
    # Channel Number = 0 
    # Channel Spacing = 199.951172 
    # Data Format = Asynchronous serial mode 
    # Data Rate = 1.19948 
    # Deviation = 5.157471 
    # Device Address = 0 
    # Manchester Enable = false 
    # Modulation Format = ASK/OOK 
    # PA Ramping = false 
    # Packet Length = 255 
    # Packet Length Mode = Infinite packet length mode 
    # Preamble Count = 4 
    # RX Filter BW = 58.035714 
    # Sync Word Qualifier Mode = No preamble/sync 
    # TX Power = 0 
    # Whitening = false 
    # PA table
    radio.writeSingleByte(defs.IOCFG2,0x0B)  #GDO2 Output Pin Configuration
    radio.writeSingleByte(defs.IOCFG0,0x0C)  #GDO0 Output Pin Configuration
    radio.writeSingleByte(defs.FIFOTHR,0x47) #RX FIFO and TX FIFO Thresholds
    radio.writeSingleByte(defs.PKTCTRL0,0x32)#Packet Automation Control
    radio.writeSingleByte(defs.CHANNR,0x03)  #Channel Number
    radio.writeSingleByte(defs.FSCTRL1,0x06) #Frequency Synthesizer Control
    radio.writeSingleByte(defs.FREQ2,0x10)   #Frequency Control Word, High Byte
    radio.writeSingleByte(defs.FREQ1,0xB0)   #Frequency Control Word, Middle Byte
    radio.writeSingleByte(defs.FREQ0,0x71)   #Frequency Control Word, Low Byte
    radio.writeSingleByte(defs.MDMCFG4,0xF5) #Modem Configuration
    radio.writeSingleByte(defs.MDMCFG3,0x83) #Modem Configuration
    radio.writeSingleByte(defs.MDMCFG2,0x30) #Modem Configuration
    radio.writeSingleByte(defs.DEVIATN,0x15) #Modem Deviation Setting
    radio.writeSingleByte(defs.MCSM0,0x18)   #Main Radio Control State Machine Configuration
    radio.writeSingleByte(defs.FOCCFG,0x14)  #Frequency Offset Compensation Configuration
    radio.writeSingleByte(defs.AGCCTRL0,0x92)#AGC Control
    radio.writeSingleByte(defs.WORCTRL,0xFB) #Wake On Radio Control
    radio.writeSingleByte(defs.FREND0,0x11)  #Front End TX Configuration
    radio.writeSingleByte(defs.FSCAL3,0xE9)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.FSCAL2,0x2A)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.FSCAL1,0x00)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.FSCAL0,0x1F)  #Frequency Synthesizer Calibration
    radio.writeSingleByte(defs.TEST2,0x81)   #Various Test Settings
    radio.writeSingleByte(defs.TEST1,0x35)   #Various Test Settings
    radio.writeSingleByte(defs.TEST0,0x09)   #Various Test Settings

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
    print("Received: 0x%x" % code)

def tx_callback(code):
    print("Transmited: 0x%x" % (code))

PA_TABLE = [0x00,0x60,0x00,0x00,0x00,0x00,0x00,0x00]
spi = SPI(1, baudrate=2000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(22), mosi=Pin(23), miso=Pin(21))
radio = cc1101.CC1101(spi=spi, gd0=18)

def initRX():
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

def initTX():
    radio.setCallback(func = tx_callback)
    radio.reset()
    TX_setDefaultValues()
    radio.writeBurst(defs.PATABLE, PA_TABLE)
    radio.sidle()
    radio.selfTest()
    print("CC1101 radio initialized for TX\r\n")
    radio.setTXState()
    utime.sleep(1)
    radio.sendRawData(0x20238989150bce23)