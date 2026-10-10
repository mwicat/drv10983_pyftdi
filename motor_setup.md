## Main settings

### Start-up current

Duty cycle applied is derived from the calculated value for Ulimit and Vcc:

Ulimit = Ilimit * Rm + Speed * Kt

where:
Ilimit = current limit (OpenLCurr)
Rm = resistance of motor (Rm)
Speed = open loop speed (Op2ClsThrOp2ClsThr)
Kt = motor velocity constant

Essentially:

Ulimit = Umotor + Ubemf

### Resistance of motor (Rm)

Measure resistance from phase to phase, then divide by 2 to get R ph_ct

Rmdig = Rph_ct / 0.00967

DRV10983_MOTOR_PARAM_1 = Motor Param1[6:0] = Rm

### Acceleration Current Limit

DRV10983_SYS_OPT_6 = SysOpt6[7:4] = SWiLimitThr

Acceleration current limit threshold
0000 = No acceleration current limit
0001 = 0.2-A current limit
xxxx = n × 0.2 A current limit

## Kt - motor velocity constant

To find out what is Kt expressed in mV/Hz, you need to hook up two of
motor connections to oscilloscope probe. On connection goes to probe signal
hook, and the other one to ground. Then, you need to rotate the motor by hand
and measure the voltage. The voltage should be in mV range. Then, you need to
calculate the Kt value using the formula:

If you are able to measure frequency of the produced signal (for example using
cursor scope feature), you can calculate Kt using the formula:

Kt [mV/Hz] = V / f

Where:

- V is the voltage max amplitude measured in mV
- f is the signal frequency measured in Hz

If you want, you can also measure the frequency of the produced signal using
tachometer and convert RPM count together with voltage from scope measurement
to Kt value using the formula:

Kt [mv/Hz] = V / (RPM/60 * pp)

Where:

- V is the voltage measured in mV
- RPM is the number of revolutions per minute
- pp is the number of pole pairs
- 60 is the conversion factor to get from minutes to seconds

## Lock detection - Abnormal Kt

Uses Kt setting:

MotorKt1[7:0] = MotorKt[15:8]
MotorKt2[7:0] = MotorKt[7:0]

16-bit value indicating the motor measured velocity constant. Always read the
MotorKt1 first.
Ktc (V/Hz)= {MotorKt1:MotorKt2} / 2 /1442
{MotorKt1:MotorKt2} corresponding to 2 × Ktph_dig

DRV10983_SYS_OPT_5 = SysOpt5[6] = LockEn = 1 to enable

Note: Uses Kt to calculate current

## Lock detection - current limit threshold

DRV10983_SYS_OPT_5 = SysOpt5[4] = LockEn = 1 to enable

DRV10983_SYS_OPT_6 = SysOpt6[3:1] = HWiLimitThr
Lock detection current limit threshold
(n + 1) × 0.4 A

Note: Uses Rm to calculate current

## Open loop mode

Set DRV10983_SYS_OPT_9[0] = CLoopDis = 1 to set open loop mode (no transfer to
closed loop).

### Current

Current in open loop mode is set by DRV10983_SYS_OPT_2 = OpenLCurr variable.

From datasheet:

Open loop current setting.
00 = 0.2 A
01 = 0.4 A
10 = 0.8 A
11 = 1.6 A

### Speed

Open loop speed is set by Op2ClsThr variable.

Speed is set by DRV10983_SYS_OPT_4 = Op2ClsThr[7:3] bits.

From datasheet:

Open to closed loop threshold
0xxxx = Range 0: n × 0.8 Hz
00000 = N/A
00001 = 0.8 Hz
00111 = 5.6 Hz
01111 = 12 Hz
1xxxx = Range 1: (n + 1) × 12.8 Hz
10000 = 12.8 Hz
10001 = 25.6 Hz
10111 = 192 Hz
11111 = 204.8 Hz

For example:

00111000 = 7 * 0.8 = 5.6 Hz
^^^^^

Final motor speed in RPM will be 5.6 Hz x number of pole pairs (8) * 60 = 42 RPM

## Closed loop mode

Set DRV10983_SYS_OPT_9[0] = 0 to set closed loop mode

To transfer from open loop to closed loop, the motor needs to reach speed
Op2ClsThr (see open loop speed).

### Speed

Speed command determines PWM duty cycle (0-100%) which in turn is derived from Vcc

#### Speed over I2C

Set DRV10983_SPEED_CTRL_2 = SpeedCtrl2[7] = OverRide = 1 to control speed by
writing to the register

Speed control is 9-bit value, SpeedCtrl1 contains 8 bits of LSB and
SpeedCtrl2 contains 1 bit of MSB:

- SpeedCtrl1[7:0] = SpdCtrl[7:0] = LSB
- SpeedCtrl2[8] = SpdCtrl[8] = MSB

Note: You need to set MSB (SpeedCtrl2) first

