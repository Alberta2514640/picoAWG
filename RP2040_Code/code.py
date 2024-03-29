import time
import board
import digitalio
import supervisor
from ledTask import toggle_leds,setup_leds
from AD5391Task import AD5391
from sine_wave_generator import SineWaveGenerator
from square_wave_generator import SquareWaveGenerator
# Set up the GPIO pins for the LEDs


setup_leds()

# Initialize AD5391
ad5391 = AD5391()
# Write DAC RAW Function (To Try and Activate the Internal Reference by setting the control register)
# Writing Control Register
# REG1=REG0=0
# A3-A0 = 1100
# DB13-DB0 Contains CR13 - CR0
# This Setup gives the following
# A/~B = 0
# R/~W = 0
# 00 (Always 0)
# A3-A0 = 1100 (Control Register)
# REG1-REG0 = 00 (Special Functions)
# DB13 - DB12 = Doesn't apply to AD5391
# CR11 = 1 Power Down Status. Configures the Amplifier Behavior in Power Down
# CR10 = 0 REF Select (Sets the Internal Reference 1/2,5V 0/1.25V)
# CR9 = 1 Current Boost Control (1 Maximizes the bias current to the output amplifier while in increasing power consumption)
# CR8 = 1 Internal / External Reference (1 Uses Internal Reference)
# CR7 = 1 Enable Channel Monitor Function (1 allows channels to be routed to the output)
# CR6 = 0 Enable Thermal Monitor Function
# CR5-CR2 = Don't CARE
# CR1-CR0 = Toggle Function Enable

sine_gen = SineWaveGenerator(channel=1, period=1, amplitude=4095, dac=ad5391)
square_gen = SquareWaveGenerator(channel=0, period=1, amplitude=4095, dac=ad5391)

def process_command(command):
    if command == "info":
        response = "This is a Basic 16 Channel Arbitrary Waveform Generator v0.01"
    elif command == "read_mon_out":
        mon_out_value = ad5391.read_mon_out()
        response = f"MON_OUT value: {mon_out_value}"
    elif command == "read_mon_out_voltage":
        mon_out_voltage = ad5391.read_mon_out_voltage()
        response = f"MON_OUT voltage: {mon_out_voltage:.4f} V"
    elif command == "read_busy_pin":
        busy_state = ad5391.read_busy_pin()
        response = f"BUSY pin state (False Means Busy): {busy_state}"
    else:
        cmd_parts = command.split(' ')
        if cmd_parts[0] == "set_ldac_pin":
            if len(cmd_parts) != 2:
                response = "Usage: set_ldac_pin [True|False]"
            else:
                state = cmd_parts[1].lower() == "true"
                ad5391.set_ldac_pin(state)
                response = f"LDAC pin state set to: {state}"
        elif cmd_parts[0] == "write_dac":
            if len(cmd_parts) < 3:
                response = "Usage: write_dac channel value [toggle_mode] [ab_select] [reg_select]"
            else:
                channel = int(cmd_parts[1])
                value = int(cmd_parts[2])
                toggle_mode = cmd_parts[3].lower() == "true" if len(cmd_parts) > 3 else False
                ab_select = cmd_parts[4].lower() == "true" if len(cmd_parts) > 4 else False
                reg_select = int(cmd_parts[5]) if len(cmd_parts) > 5 else 0

                ad5391.write_dac(channel, value, toggle_mode, ab_select, reg_select)
                response = f"Value {value} written to channel {channel} with toggle_mode={toggle_mode}, ab_select={ab_select}, reg_select={reg_select}"
        else:
            response = "Unknown command"

    return response


ad5391.monitor_channel(0)

next_toggle = time.monotonic() + 1

while True:
    now = time.monotonic()
    if now >= next_toggle:
        toggle_leds()
        next_toggle = now + 0.05
        control_register_value = ad5391.read_register(0b0001, 0b11)
        ad5391.write_dac_raw(0b0_0_00_1100_00_101111_0000_00_00)
        print(((control_register_value & 0x003FFF)>>2,))
    sine_gen.progress()
    square_gen.progress()


    if supervisor.runtime.serial_bytes_available:
        command = input().strip()
        response = process_command(command)
        print(response)
