from smbus2 import SMBus

def i2c_detect(bus_number):
    devices = []
    try:
        with SMBus(bus_number) as bus:
            for address in range(0x03, 0x78):  # Valid I2C addresses are 0x03 to 0x77
                try:
                    bus.write_quick(address)
                    devices.append(hex(address))
                except OSError:
                    pass  # Address didn't respond
    except FileNotFoundError:
        print(f"I2C bus {bus_number} not found. Ensure the correct bus number.")
    return devices

# Specify the I2C bus number (e.g., 1 for Raspberry Pi default)
bus_number = 5
detected_devices = i2c_detect(bus_number)

if detected_devices:
    print(f"I2C devices found on bus {bus_number}: {', '.join(detected_devices)}")
else:
    print(f"No I2C devices found on bus {bus_number}.")
