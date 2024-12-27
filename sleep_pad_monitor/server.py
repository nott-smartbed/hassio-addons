import serial
import os
import src.helper as Helper
import src.server_command as ServerCommand

# UART Configuration
UART_PORT = os.getenv('UART_PORT', "/dev/tty.usbserial-0001")  # Replace with the actual port of your device
BAUD_RATE = os.getenv('BAUD_RATE', 115200)

def create_command(frame_type, id, content):
    # [frame header 0x7D is 1byte]+[frame type symbol 1byte]+[frame length 2byte]+[ID total 10byte ASCII code]+[content:data/response]+[end 0x0D]
    frame_header = '7D'
    end = '0D'
    id = id.ljust(10)[:10] # This ensures the ID is exactly 10 bytes long
    id_hex = [f"{ord(char):02X}" for char in id]
    if content is None:
        content = ['00']
    if isinstance(content, str):
        content = [content]
    frame_length = 15 + len(content)
    frame_length_hex = Helper.int_to_hex(frame_length, 2)
    print(f"frame_header: {frame_header}, frame_type: {frame_type}, frame_length_hex: {frame_length_hex}, id_hex: {id_hex}, content: {content}, end: {end}")
    if not content:
        return Helper.flatten_list([frame_header, frame_type, frame_length_hex, id_hex, end])
    return Helper.flatten_list([frame_header, frame_type, frame_length_hex, id_hex, content, end])

def server_send_command():
    ser = serial.Serial(UART_PORT, BAUD_RATE)
    print(f"Connected to UART device at {UART_PORT} with baud rate {BAUD_RATE}")

    try:
        if not ser.is_open:
            ser.open()
        if ser.is_open:
            [frame_type, content] = ServerCommand.set_working_mode()
            command = create_command(frame_type, 'UNCONFIGED', content)
            print(f"command: {command}")
            for x in command:
                ser.write(bytes.fromhex(x))
            print("Command sent successfully!")
            return ser.close()

    except KeyboardInterrupt:
        print("Stopping UART listener...")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        ser.close()

if __name__ == "__main__":
    server_send_command()