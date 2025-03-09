from enum import Enum
import time

from pyftdi.i2c import I2cController

from drv10983_const import *


DEVICE_I2C_ADDR = 0x52
MOTOR_POLE_PAIRS = 5
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


def set_speed(motor_speed_hz: int) -> None:
    speed = (motor_speed_hz // 2) & 0x01FF
    tmp1 = speed
    tmp2 = speed >> 8
    tmp2 &= 0x01
    tmp2 |= 0x80  # set speed OverRide bit
    write_register(DRV10983_SPEED_CTRL_2, tmp2)
    time.sleep(0.01)
    write_register(DRV10983_SPEED_CTRL_1, tmp1)


def get_vel_const() -> float:
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
    res = read_register(DRV10983_FAULT_CODE)
    return decode_enum_list(FaultCodeEnum, res)


def get_status() -> list[type[StatusEnum]]:
    res = read_register(DRV10983_STATUS)
    return decode_enum_list(StatusEnum, res)


i2c = I2cController()
i2c.configure(DEVICE_FTDI_ADDR)

slave = i2c.get_port(DEVICE_I2C_ADDR)

# init writing to eeprom - Vcc must be at least 22V for writing to work !!!
write_register(DRV10983_EE_CTRL,
               0b01000000)  # set siData = 1

# set params
write_register(DRV10983_MOTOR_PARAM_1,
               0b00111101)  # Rph_ct = 1 ohm
write_register(DRV10983_MOTOR_PARAM_2,
               0b00111000)  # Kt = 58.7 mV/Hz
write_register(DRV10983_MOTOR_PARAM_3,
               0b00111010)  # CtrlAdvMd TCtrlAdv[6:0]
write_register(DRV10983_SYS_OPT_1,
               0b00000000)  # ISDThr[1:0] IPDAdvcAgl[1:0] ISDen RvsDrEn RvsDrThr[1:0]
write_register(DRV10983_SYS_OPT_2,
               0b11010010)  # 7:6 OpenLCurr[1:0] = 0.2A
write_register(DRV10983_SYS_OPT_3,
               0b11000000)  # 2:0 StAccel[2:0] = 9.2 Hz
write_register(DRV10983_SYS_OPT_4,
               0b00111000)  # 7:3 Op2ClsThr[4:0] = 12 Hz, 2:0 AlignTime[2:0] = 5.3s
write_register(DRV10983_SYS_OPT_5,
               0b00000000)  # 6 LockEn[2] = Abnormal Kt, enabled when high
write_register(DRV10983_SYS_OPT_6,
               0b00001111)  # 3:1 HWiLimitThr [2:0] = 111
write_register(DRV10983_SYS_OPT_7,
               0b01110111)  # 7 LockEn[5] Stuck in closed loop (no zero cross detected). Enabled when high, 6:4 ClsLpAccel[2:0] = 0.77Vcc/s
write_register(DRV10983_SYS_OPT_8,
               0b00000000)
write_register(DRV10983_SYS_OPT_9,
               0b00001100)  # 0 CLoopDis = 0, 1 SpdCtrlMd = 0 = analog

# apply write
write_register(DRV10983_DEV_CTRL,
               0b10110110)  # enProgKey = 10110110
write_register(DRV10983_EE_CTRL,
               0b11010001)  # 7 sleepDis = 0, siData = 1, eeWrite = 1


set_speed(50)
