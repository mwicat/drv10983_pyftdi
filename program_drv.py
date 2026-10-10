from enum import Enum
import time

from pyftdi.i2c import I2cController

from drv10983_const import *


DEVICE_I2C_ADDR = 0x52
MOTOR_POLE_PAIRS = 5


## Use ftdi_urls.py to find the FTDI device
DEVICE_FTDI_ADDR = 'ftdi://ftdi:232h:1/1'



class FaultCodeEnum(Enum):
    STUCK_IN_CLOSED_LOOP = 5
    STUCK_IN_OPEN_LOOP = 4
    NO_MOTOR = 3
    KT_ABNORMAL = 2
    SPEED_ABNORMAL = 1
    LOCK_DETECTION_CURRENT_LIMIT = 0


class StatusEnum(Enum):
    OverTemp = 7
    Slp_Stdby = 6
    OverCurr = 5
    MtrLck = 4


def write_register(reg_addr: int, reg_value: int) -> None:
    slave.write_to(reg_addr, [reg_value])
    print('ok')


def read_register(reg_addr: int) -> int:
    res = slave.read_from(reg_addr, 1)
    res = int.from_bytes(res)
    print('result: {0:08b}'.format(res))
    return res


def get_supply_voltage() -> float:
    return read_register(DRV10983_SUPPLY_VOLTAGE) * 30 / 256.0


def get_speed() -> float:
    speed1 = read_register(DRV10983_MOTOR_SPEED_1)
    speed2 = read_register(DRV10983_MOTOR_SPEED_2)
    tmp_speed = speed1
    tmp_speed <<= 8
    tmp_speed |= speed2
    return tmp_speed/10.0


def get_speed_rpm() -> float:
    return get_speed() / MOTOR_POLE_PAIRS * 60


def set_speed(speed: int) -> None:  # speed in 0-511
    tmp1 = speed & ((1<<8)-1)   # LSB
    tmp2 = speed >> 8  # MSB
    tmp2 &= 0b00000001  # get first bit (MSB)
    tmp2 |= 0b10000000  # set speed OverRide bit

    write_register(DRV10983_SPEED_CTRL_2, tmp2)
    time.sleep(0.001)
    write_register(DRV10983_SPEED_CTRL_1, tmp1)


def get_kt() -> float:
    velocity_const1 = read_register(DRV10983_MOTOR_KT_1)
    velocity_const2 = read_register(DRV10983_MOTOR_KT_2)
    tmp_velocity_const = velocity_const1
    tmp_velocity_const <<= 8
    tmp_velocity_const |= velocity_const2
    return tmp_velocity_const / 2.0 / 1442


def get_speed_cmd() -> float:
    res = read_register(DRV10983_SPEED_CMD)
    return res * 100 / 255.0


def decode_enum_list[E: type[Enum]](enum_class: E, value: int) -> list[E]:
    codes = []
    for enum_obj in enum_class:
        if value & (1 << enum_obj.value):
            codes.append(enum_obj)
    return codes


def get_fault_code() -> list[type[FaultCodeEnum]]:
    """
    Get fault codes from the DRV10983.
    Note: calling this function will clear the fault codes in the DRV10983.
    """
    res = read_register(DRV10983_FAULT_CODE)
    return decode_enum_list(FaultCodeEnum, res)


def get_status() -> list[type[StatusEnum]]:
    res = read_register(DRV10983_STATUS)
    return decode_enum_list(StatusEnum, res)


i2c = I2cController()
i2c.configure(DEVICE_FTDI_ADDR)

slave = i2c.get_port(DEVICE_I2C_ADDR)

#%% Write section

# init writing to eeprom - Vcc must be at least 22V for writing to work !!!
write_register(DRV10983_EE_CTRL,
               0b01000000)  # set siData = 1

# set params

# [7] DoubleFreq = 0 = driver frequency 25 kHz
# [6:0] Rph_ct = 4.5 ohm
write_register(DRV10983_MOTOR_PARAM_1,
               0b01011111)

# [7] Closed loop adjustment mode = 0 = full cycle adjustment
# [6:0] Kt[6:0] = 58.7 mV/Hz
write_register(DRV10983_MOTOR_PARAM_2,
               0b00111000)

# [7] CtrlAdvMd[7] = 0 (commutation control advance time = fixed time)
# [6:0] TCtrlAdv[6:0] = 0 (advance time = 0us)
write_register(DRV10983_MOTOR_PARAM_3,
               0b00000000)

# [7:6] ISDThr[1:0] = ISD stationary judgment threshold = 00 = 6Hz
# [5:4] IPDAdvcAgl[1:0] = advancing angle after inductive sense = 00 = 30 degrees
# [3] ISDen = initial speed detect = 0 = disabled
# [2] RvsDrEn = reverse drive enable = 0 = disabled
# [1:0] RvsDrThr[1:0] = Reverse drive threshold = 0 = 6.3 Hz
write_register(DRV10983_SYS_OPT_1,
               0b00000000)

# [7:6] OpenLCurr[1:0] = 01 = 0.4A
# [5:3] OpLCurrRt[2:0] = Open loop current ramp-up rate = 010 = 1.5 Vcc/s
# [2:0] BrkDoneThr[2:0] = braking mode setting = 010 = 1.3 s
write_register(DRV10983_SYS_OPT_2,
               0b01010010)

# [7:6] CtrlCoef[1:0] = 11 = 1
# [5:3] StAccel2[2:0] = open loop startup accelerate (second order) 000 = 57 Hz/s2
# [2:0] StAccel[2:0] = open loop startup accelerate (first order) 000 = 76 Hz/s
write_register(DRV10983_SYS_OPT_3,
               0b11000000)

# [7:3] Op2ClsThr[4:0] = 12 Hz
# [2:0] AlignTime[2:0] = 000 = 5.3s
write_register(DRV10983_SYS_OPT_4,
               0b10001000)

# All lock detection disabled
write_register(DRV10983_SYS_OPT_5,
               0b00000000)

# [7:4] SWiLimitThr = no acceleration current limit [3:1]
# [3:1] HWiLimitThr [2:0] = lock detection current limit (2+1)*0.4A = 1.2A
# [0] N/A = N/A
write_register(DRV10983_SYS_OPT_6,
               0b00000100)

# [7] LockEn[5] Stuck in closed loop (no zero cross detected). Enabled when high,
# [6:4] ClsLpAccel[2:0] = 7 = 48Vcc/s,
# [3:0] Deadtime between HS and LS gate drive = 360 ns
write_register(DRV10983_SYS_OPT_7,
               0b00001001)

# [7:4] IPDCurrThr[3:0] = 0  = No IPD (initial position detect), instead Align and Go
# [3] Open loop stuck detect = 0 = disabled
# [2] VregSel = buck regulator voltage select = 0 = 5V
# [1:0] IPDClk = Inductive sense clock = 12 Hz
write_register(DRV10983_SYS_OPT_8,
               0b00000000)

# [7:6] FGOLsel = open loop output select = 0 = FG outputs in both open loop and closed loop
# [5:4] FGCycle[1:0] = 0 = 1pulse output per electrical cycle
# [3:2] KtLckThr[1:0] = 11 = Kt_high = 2Kt, Kt_low = 0.5Kt
# [1] SpdCtrlMd = 0 = analog
# [0] CLoopDis = 0, 0 = closed loop enabled, 1 = closed loop disabled
write_register(DRV10983_SYS_OPT_9,
               0b00001110)

# apply write

# The procedure for programming the EEPROM is as follows. TI recommends to perform the EEPROM
# programming without the motor spinning, power cycle after the EEPROM write, and read back the EEPROM to
# verify the programming is successful.
# 1. Set SIdata = 1.
# 2. Write the desired motor parameters into the corresponding registers (address 0x20:0x2B) (see I
# 2C Serial
# Interface).
# 3. Write 1011 0110 (0xB6) to enProgKey in the DevCtrl register.
# 4. Ensure that VCC is at or above 22 V.
# 5. Write eeWrite = 1 in EECtrl register to start the EEPROM programming.

# enProgKey = 10110110
# 8-bit byte use to enable programming in the EEPROM.
# To program the EEPROM, enProgKey = 1011 0110 (0xB6), followed immediately
# by eeWrite = 1. Otherwise, enProgKey value is reset.
write_register(DRV10983_DEV_CTRL,
               0b10110110)
#
# # [7] sleepDis = 0
# # siData = 1
# # eeWrite = 1
# write_register(DRV10983_EE_CTRL,
#                0b11010001)
#
# set_speed(20)
#
#
#
# # [7:3] Op2ClsThr[4:0] = 12 Hz
# # [2:0] AlignTime[2:0] = 000 = 5.3s
# write_register(DRV10983_SYS_OPT_4,
#                0b10001000)
# set_speed(1000)
#
#
# write_register(DRV10983_SYS_OPT_4,
#                0b01110000)
# set_speed(0)
set_speed(1000)
