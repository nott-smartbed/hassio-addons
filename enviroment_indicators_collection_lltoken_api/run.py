import time
import json
import requests
from library import constant
from library.bmp280_driver import BMP280  # Thay thế thư viện cũ bằng bmp280_driver
from smbus2 import SMBus
from Adafruit_BMP.BMP085 import BMP085  # BMP180
from library.DFRobot_Oxygen import DFRobot_Oxygen_IIC
from library.SHT4x import SHT4x  # Import thư viện SHT4x

options = {
    "base_url": "http://192.168.137.140:8123/api/states",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkNGU2NDc0ZWM2ODU0OThlYmE1ZTIzYTMxOWUzMDY2MCIsImlhdCI6MTczNjMwNjI4MSwiZXhwIjoyMDUxNjY2MjgxfQ.BjyBI6G40FnMKlOMPIVN10rRnt4B3lseJj6-BDOCYOA",
    "bmp180": True,
    "addr-sht": "0x44",
    "addr-oxy": "0x73",
    "sht45": True,
    "sht31": True,
    "oxygen": True,
    "bmp280": True
}

class SensorManager:
    def __init__(self):
        self.options = options
        self.ha_base_url = self.options.get("base_url", constant.DEFAULT_BASE_URL)
        self.ha_token = self.options.get("token", constant.DEFAULT_TOKEN)
        # self.validate_config()
        self.headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json",
        }
        self.bus = SMBus(constant.DEFAULT_BUS)
        if self.options.get(constant.BMP180_OPTION, False):
            self.bmp180 = BMP085(busnum=constant.DEFAULT_BUS)
        # if self.options.get("bmp280", False):
        #     self.bmp280 = BMP280(i2c_addr=0x77, i2c_dev=self.bus)
        #     self.bmp280.setup(
        #         mode="normal",                   #normal, sleep, forced
        #         temperature_oversampling=16,     
        #         pressure_oversampling=16,        
        #         temperature_standby=500          # ms
        #     )
        if self.options.get(constant.OXYGEN_OPTION, False):
            self.oxygen_sensor = DFRobot_Oxygen_IIC(constant.DEFAULT_BUS, int(self.options.get(constant.OXYGEN_SENSOR_ADDRESS, constant.OXYGEN_DEFAULT_PIN), 16))
        if self.options.get(constant.SHT31_OPTION, False):
            self.sht31_address = int(self.options.get(constant.SHT31_SENSOR_ADDRESS, constant.SHT31_DEFAULT_PIN), 16)
            self.read_temp_hum_cmd = [0x2C, 0x06]
        if self.options.get(constant.SHT45_OPTION, False):  # SHT45
            self.sht45_sensor = SHT4x(bus=constant.DEFAULT_BUS, address=constant.SHT45_DEFAULT_PIN, mode=constant.SHT45_DEFAULT_MODE)  # Khởi tạo cảm biến SHT45

    def load_options(self, file_path):
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading options: {e}")
            return {}

    def validate_config(self):
        if self.ha_base_url == constant.DEFAULT_BASE_URL or self.ha_token == constant.DEFAULT_TOKEN:
            print("Error: Missing required configuration in options.json.")
            exit(1)

    def read_sht31(self):
        try:
            self.bus.write_i2c_block_data(self.sht31_address, self.read_temp_hum_cmd[0], self.read_temp_hum_cmd[1:])
            time.sleep(0.5)
            data = self.bus.read_i2c_block_data(self.sht31_address, 0x00, 6)
            temp_raw = (data[0] << 8) + data[1]
            humidity_raw = (data[3] << 8) + data[4]
            temperature = -45 + (175 * temp_raw / 65535.0)
            humidity = (100 * humidity_raw / 65535.0)
            print(temperature)
            print(humidity)
            return temperature, humidity
        except Exception as e:
            print(f"Error reading from SHT31: {e}")
            return None, None

    def read_sht45(self):
        try:
            self.sht45_sensor.update()
            temperature = self.sht45_sensor.temperature
            humidity = self.sht45_sensor.humidity
            return temperature, humidity
        except Exception as e:
            print(f"Error reading from SHT45: {e}")
            return None, None

    def read_bmp280(self):
        try:
            temperature = self.bmp280.get_temperature()
            pressure = self.bmp280.get_pressure()
            altitude = self.bmp280.get_altitude(qnh=1013.25)
            return temperature, pressure, altitude
        except Exception as e:
            print(f"Error reading BMP280: {e}")
            return None, None, None

    def post_to_home_assistant(self, url, payload):
        try:
            print(url, payload)
            response = requests.post(url, json=json.dumps(payload), headers=self.headers)
            response.raise_for_status()  # Kích hoạt ngoại lệ nếu có lỗi HTTP
            print(f"Data posted to {url}: {payload}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting to Home Assistant: {e}")

    def generate_header(self, unit, friendly_name, sensor_name, value):
        return {
                    "url": f"{self.ha_base_url}/sensor.{sensor_name}",
                    "payload": {
                        "state": round(value, constant.ROUND_VALUE),
                        "attributes": {
                            "unit_of_measurement": {unit},
                            "friendly_name": {friendly_name},
                        },
                    },
                }
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
            print(f'founded devices {devices}')
        except FileNotFoundError:
            print(f"I2C bus {bus_number} not found. Ensure the correct bus number.")
        return devices

    def run(self):
        while True:
            sensor_data = []

            # if self.options.get(constant.OXYGEN_OPTION, False):
            #     oxygen_concentration = self.oxygen_sensor.get_oxygen_data(collect_num=20)
            #     oxygen_sensor_data = self.generate_header("%", "Oxygen", "Oxygen_concentration", oxygen_concentration)
            #     sensor_data.append(oxygen_sensor_data)
            #     print(f"Oxygen concentration: {oxygen_concentration:.2f}%")

            # if self.options.get(constant.SHT45_OPTION, False):
            #     temperature, humidity = self.read_sht45()
            #     if temperature is not None and humidity is not None:
            #         temperature_sensor_data = self.generate_header("°C", "Temperature", "sht45_temperature", temperature)
            #         humidity_sensor_data = self.generate_header("%", "Humidity", "sht45_humidity", humidity)
            #         sensor_data.append(temperature_sensor_data)
            #         sensor_data.append(humidity_sensor_data)
            #         print(f"SHT45 Temperature: {temperature:.2f} °C")
            #         print(f"SHT45 Humidity: {humidity:.2f} %")

            # if self.options.get(constant.SHT31_OPTION, False):
            #     temperature, humidity = self.read_sht31()
            #     if temperature is not None and humidity is not None:
            #         temperature_sensor_data = self.generate_header("°C", "Temperature", "sht45_temperature", temperature)
            #         humidity_sensor_data = self.generate_header("%", "Humidity", "sht45_humidity", humidity)
            #         sensor_data.append(temperature_sensor_data)
            #         sensor_data.append(humidity_sensor_data)
            #         print(f"SHT31 Temperature: {temperature:.2f} °C")
            #         print(f"SHT31 Humidity: {humidity:.2f} %")

            if self.options.get(constant.BMP180_OPTION, False):
                pressure = self.bmp180.read_pressure()
                if pressure is not None:
                    pressure_sensor_data = self.generate_header("hPa", "BMP180 Pressure", "bmp180_pressure", pressure)
                    sensor_data.append(pressure_sensor_data)
                print(f"BMP180 Pressure: {pressure / 100:.2f} hPa")

            # if self.options.get("bmp280", False):
            #     temperature, pressure, altitude = self.read_bmp280()
            #     if temperature is not None and pressure is not None and altitude is not None:
            #         sensor_data.append(
            #             {
            #                 "url": f"{self.ha_base_url}/sensor.bmp280_temperature",
            #                 "payload": {
            #                     "state": round(temperature, 2),
            #                     "attributes": {
            #                         "unit_of_measurement": "°C",
            #                         "friendly_name": "BMP280 Temperature",
            #                     },
            #                 },
            #             }
            #         )
            #         sensor_data.append(
            #             {
            #                 "url": f"{self.ha_base_url}/sensor.bmp280_pressure",
            #                 "payload": {
            #                     "state": round(pressure, 2),
            #                     "attributes": {
            #                         "unit_of_measurement": "hPa",
            #                         "friendly_name": "BMP280 Pressure",
            #                     },
            #                 },
            #             }
            #         )
            #         sensor_data.append(
            #             {
            #                 "url": f"{self.ha_base_url}/sensor.bmp280_altitude",
            #                 "payload": {
            #                     "state": round(altitude, 2),
            #                     "attributes": {
            #                         "unit_of_measurement": "m",
            #                         "friendly_name": "BMP280 Altitude",
            #                     },
            #                 },
            #             }
            #         )
            #         print(f"BMP280 Temperature: {temperature:.2f} °C")
            #         print(f"BMP280 Pressure: {pressure:.2f} hPa")
            #         print(f"BMP280 Altitude: {altitude:.2f} m")

            for data in sensor_data:
                self.post_to_home_assistant(data["url"], data["payload"])

            time.sleep(10)

if __name__ == "__main__":
    print("Starting sensor manager...")
    sensor_manager = SensorManager()
    sensor_manager.run()

