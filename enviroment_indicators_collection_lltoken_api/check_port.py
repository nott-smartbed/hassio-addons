from smbus2 import SMBus

# Assuming the function is part of a class named `I2CScanner`
class I2CScanner:
    def i2c_detect(self, bus_number):
        devices = []
        try:
            print("device checking...")
            with SMBus(bus_number) as bus:
                for address in range(0x03, 0x78):
                    try:
                        bus.write_quick(address)
                        devices.append(hex(address))
                    except OSError:
                        pass
            print(f"founded devices: {devices}")
        except FileNotFoundError:
            print(f"I2C bus {bus_number} not found. Ensure the correct bus number.")
        return devices

# Create an instance of the class
scanner = I2CScanner()

# Call the function for bus number 5
detected_devices = scanner.i2c_detect(bus_number=5)

# Print the results
print("Detected devices on bus 5:", detected_devices)
