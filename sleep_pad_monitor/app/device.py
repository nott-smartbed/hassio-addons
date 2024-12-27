import time
import os
import serial
import device_command as DeviceCommand

# UART Configuration
UART_PORT = os.getenv('UART_PORT', "/dev/tty.usbserial-0001")  # Replace with the actual port of your device
BAUD_RATE = os.getenv('BAUD_RATE', 115200)

def read_uart_data():
    ser = serial.Serial(UART_PORT, BAUD_RATE)
    print(f"Connected to UART device at {UART_PORT} with baud rate {BAUD_RATE}")
    try:
        if not ser.is_open:
            ser.open()
        command = []
        while ser.is_open:
            # Overall data structure: [frame header 0x7D is 1byte]+[frame type symbol 1byte]+[frame length 2byte]+[ID total 10byte ASCII code]+[content:data/response]+[end 0x0D]
            byte_data= ser.read(1)
            hex_data = byte_data.hex().upper()
            if hex_data == '7D':
                command = []
            command.append(hex_data)
            if command[0] == '7D' and command[-1] == '0D':
                try:
                    DeviceCommand.read_client_command(command)
                except Exception as e:
                    print(f"Error: {e}")
                command = []

    except KeyboardInterrupt:
        print("Stopping UART listener...")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        ser.close()

if __name__ == "__main__":
    read_uart_data()
