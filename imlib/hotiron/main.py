#https://github.com/B3AU/micropython

import sys
import utime
sys.path.append("./libs")

from MAX6675 import MAX6675
from PDM import PDM
import TFT
from PID import PID

micropython.alloc_emergency_exception_buf(100)

state = [("OFF", 0), ("PREHEAT", 150), ("REFLOW", 240), ("COOLING", 0)]
state_idx = 0

pdm = PDM()
tc = MAX6675()
tft = TFT()

pdm.set_output(0.7)

def get_temp():
    global tc
    return tc.FIR.get_value() * 0.25

pid = PID(get_temp, pdm.set_output)

def main():
    prev_t = ''
    TFT.clear()
    while True:#sw_state:
        temp, tc_err = tc.read()
        pid.set_point = state[state_idx][1]
        pid.update()
        avg_temp = tc.FIR.get_value() * 0.25
        avg_temp = str(avg_temp)

        if t != prev_t:
            TFT.print('temp_now', avg_temp[:4])
            TFT.print('temp_next', str(state[state_idx][1]))
            TFT.print('time', str(pid.output)[:6])
            TFT.print('percentage', str(pid.P_value)[:5])
            TFT.ptint('state', str(pid.I_value)[:5])
            prev_t = t
        utime.sleep_ms(50)

main()