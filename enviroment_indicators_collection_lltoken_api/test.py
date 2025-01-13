import smbus2
import time
import math

# Địa chỉ I2C của các cảm biến
SHT31_SENSOR_ADDRESS = 0x44
OXYGEN_SENSOR_ADDRESS = 0x73
BMP180_SENSOR_ADDRESS = 0x77

# Lệnh yêu cầu đo của cảm biến SHT31
CMD_MEASURE_HIGHREP = [0x2C, 0x06]

# Hàm đọc cảm biến nhiệt độ và độ ẩm SHT31
def read_temperature_and_humidity():
    bus = smbus2.SMBus(3)
    try:
        bus.write_i2c_block_data(SHT31_SENSOR_ADDRESS, CMD_MEASURE_HIGHREP[0], [CMD_MEASURE_HIGHREP[1]])
        time.sleep(0.5)
        data = bus.read_i2c_block_data(SHT31_SENSOR_ADDRESS, 0, 6)

        temperature = -45 + (175 * (data[0] * 256 + data[1]) / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0

        return temperature, humidity
    except Exception as e:
        print(f"Error reading from SHT31 sensor: {e}")
        return None, None
    finally:
        bus.close()

# Hàm đọc cảm biến oxy
def read_oxygen_concentration():
    bus = smbus2.SMBus(3)
    try:
        data = bus.read_i2c_block_data(OXYGEN_SENSOR_ADDRESS, 0, 3)
        oxygen_concentration = (data[1] << 8 | data[2]) / 10.0
        return oxygen_concentration
    except Exception as e:
        print(f"Error reading from oxygen sensor: {e}")
        return None
    finally:
        bus.close()

# Hàm tính điểm sương
def calculate_dew_point(temp, hum):
    if temp is None or hum is None:
        return None
    a, b = 17.67, 243.5
    alpha = math.log(hum / 100) + (a * temp) / (b + temp)
    return (b * alpha) / (a - alpha)

# Hàm đọc cảm biến BMP180 (áp suất và nhiệt độ)
def read_bmp180():
    bus = smbus2.SMBus(3)
    try:
        # Đọc hệ số hiệu chỉnh từ BMP180
        calib = bus.read_i2c_block_data(BMP180_SENSOR_ADDRESS, 0xAA, 22)
        ac1 = (calib[0] << 8) + calib[1]
        ac2 = (calib[2] << 8) + calib[3]
        ac3 = (calib[4] << 8) + calib[5]
        ac4 = (calib[6] << 8) + calib[7]
        ac5 = (calib[8] << 8) + calib[9]
        ac6 = (calib[10] << 8) + calib[11]
        b1 = (calib[12] << 8) + calib[13]
        b2 = (calib[14] << 8) + calib[15]
        mb = (calib[16] << 8) + calib[17]
        mc = (calib[18] << 8) + calib[19]
        md = (calib[20] << 8) + calib[21]

        # Đọc nhiệt độ thô
        bus.write_byte_data(BMP180_SENSOR_ADDRESS, 0xF4, 0x2E)
        time.sleep(0.005)
        ut = (bus.read_byte_data(BMP180_SENSOR_ADDRESS, 0xF6) << 8) + bus.read_byte_data(BMP180_SENSOR_ADDRESS, 0xF7)

        # Đọc áp suất thô
        bus.write_byte_data(BMP180_SENSOR_ADDRESS, 0xF4, 0x34)
        time.sleep(0.005)
        up = (bus.read_byte_data(BMP180_SENSOR_ADDRESS, 0xF6) << 8) + bus.read_byte_data(BMP180_SENSOR_ADDRESS, 0xF7)

        # Tính toán nhiệt độ
        x1 = (ut - ac6) * ac5 / 32768
        x2 = mc * 2048 / (x1 + md)
        b5 = x1 + x2
        temperature = (b5 + 8) / 16 / 10

        # Tính toán áp suất
        b6 = b5 - 4000
        x1 = (b2 * (b6 * b6 / 4096)) / 2048
        x2 = ac2 * b6 / 2048
        x3 = x1 + x2
        b3 = (((ac1 * 4 + x3) * 2) + 2) / 4
        x1 = ac3 * b6 / 8192
        x2 = (b1 * (b6 * b6 / 4096)) / 65536
        x3 = ((x1 + x2) + 2) / 4
        b4 = ac4 * (x3 + 32768) / 32768
        b7 = (up - b3) * 25000
        pressure = (b7 * 2) / b4

        return temperature, pressure / 100  # Trả về áp suất tính theo hPa
    except Exception as e:
        print(f"Error reading from BMP180 sensor: {e}")
        return None, None
    finally:
        bus.close()

# Vòng lặp chính
if __name__ == "__main__":
    while True:
        temp_sht, hum_sht = read_temperature_and_humidity()
        oxygen = read_oxygen_concentration()
        temp_bmp, pressure = read_bmp180()
        dew_point = calculate_dew_point(temp_sht, hum_sht) if temp_sht and hum_sht else None

        # In ra kết quả
        if temp_sht is not None and hum_sht is not None:
            print(f"SHT31 - Nhiệt độ: {temp_sht:.2f}°C, Độ ẩm: {hum_sht:.2f}%, Điểm sương: {dew_point:.2f}°C")
        else:
            print("Không đọc được dữ liệu từ cảm biến SHT31.")

        if oxygen is not None:
            print(f"Oxy - Nồng độ oxy: {oxygen:.2f}%")
        else:
            print("Không đọc được dữ liệu từ cảm biến oxy.")

        if temp_bmp is not None and pressure is not None:
            print(f"BMP180 - Nhiệt độ: {temp_bmp:.2f}°C, Áp suất: {pressure:.2f} hPa")
        else:
            print("Không đọc được dữ liệu từ cảm biến BMP180.")

        time.sleep(5)  # Đo lường mỗi 5 giây
