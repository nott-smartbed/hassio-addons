import time
import json
import requests
from library.bmp280_driver import BMP280  # Thay thế thư viện cũ bằng bmp280_driver
from smbus2 import SMBus
from Adafruit_BMP.BMP085 import BMP085  # BMP180
from library.DFRobot_Oxygen import DFRobot_Oxygen_IIC
from library.SHT4x import SHT4x  # Import thư viện SHT4x
from constants import constants

options = {
    "base_url": "http://192.168.31.18:8123/api/states",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkNGU2NDc0ZWM2ODU0OThlYmE1ZTIzYTMxOWUzMDY2MCIsImlhdCI6MTczNjMwNjI4MSwiZXhwIjoyMDUxNjY2MjgxfQ.BjyBI6G40FnMKlOMPIVN10rRnt4B3lseJj6-BDOCYOA",
    "bmp180": True,
    "bmp280": False,
    "oxygen": False,
    "sht31": False,
    "sht45": False,
    "addr-oxy": "0x73",
    "addr-sht": "0x44"
}

class SensorManager:
    def __init__(self, options_path="/data/options.json"):
        self.options = options
        self.ha_base_url = self.options.get(constants.BASE_URL, constants.DEFAULT_BASE_URL)
        self.ha_token = self.options.get(constants.TOKEN, constants.DEFAULT_TOKEN)
        self.validate_config()
        self.headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json",
        }
        self.bus = SMBus(5)

        if self.options.get(constants.BMP180, False):
            self.bmp180 = BMP085(busnum=5)
        if self.options.get(constants.BMP280, False):
            self.bmp280 = BMP280(i2c_addr=0x76, i2c_dev=self.bus)
            self.bmp280.setup(
                mode="normal",          
                temperature_oversampling=16,
                pressure_oversampling=16,
                temperature_standby=500
            )
        if self.options.get(constants.OXYGEN, False):
            self.oxygen_sensor = DFRobot_Oxygen_IIC(5, int(self.options.get(constants.ADDR_OXY, "0x73"), 16))
        if self.options.get(constants.SHT31, False):
            self.sht31_address = int(self.options.get(constants.ADDR_SHT, "0x44"), 16)
            self.read_temp_hum_cmd = [0x2C, 0x06]
        if self.options.get(constants.SHT45, False):  # SHT45
            self.sht45_sensor = SHT4x(bus=5, address=0x44, mode="high")

    def load_options(self, file_path):
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading options: {e}")
            return {}

    def validate_config(self):
        if self.ha_base_url == constants.DEFAULT_BASE_URL or self.ha_token == constants.DEFAULT_TOKEN:
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
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            print(f"Data posted to {url}: {payload}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting to Home Assistant: {e}")

    def generate_header(self, sensor_name, value, unit, friendly_name):
        return  {
                "url": f"{self.ha_base_url}/sensor.{sensor_name}",
                "payload": {
                    "state": round(value, 2),
                    "attributes": {
                        "unit_of_measurement": unit,
                        "friendly_name": friendly_name,
                        },
                    },
                }

    def run(self):
        while True:
            sensor_data = []

            if self.options.get("oxygen", False):
                oxygen_concentration = self.oxygen_sensor.get_oxygen_data(collect_num=20)
                oxygen_push_data = self.generate_header("Oxygen_concentration", oxygen_concentration, "%", "Oxygen")
                sensor_data.append(oxygen_push_data)
                print(f"Oxygen concentration: {oxygen_concentration:.2f}%")

            if self.options.get("sht45", False):
                temperature, humidity = self.read_sht45()
                if temperature is not None and humidity is not None:
                    temperature_push_data = self.generate_header("sht45_temperature", temperature, "°C", "Temperature")
                    humidity_push_data = self.generate_header("sht45_humidity", humidity, "%", "Humidity")
                    sensor_data.append(temperature_push_data)
                    sensor_data.append(humidity_push_data)
                    print(f"SHT45 Temperature: {temperature:.2f} °C")
                    print(f"SHT45 Humidity: {humidity:.2f} %")

            if self.options.get("sht31", False):
                temperature, humidity = self.read_sht31()
                if temperature is not None and humidity is not None:
                    temperature_push_data = self.generate_header("sht45_temperature", temperature, "°C", "Temperature")
                    humidity_push_data = self.generate_header("sht45_humidity", humidity, "%", "Humidity")
                    sensor_data.append(temperature_push_data)
                    sensor_data.append(humidity_push_data)
                    print(f"SHT31 Temperature: {temperature:.2f} °C")
                    print(f"SHT31 Humidity: {humidity:.2f} %")

            if self.options.get("bmp180", False):
                pressure = self.bmp180.read_pressure()
                pressure_push_data = self.generate_header("bmp180_pressure", pressure, "hPa", "Pressure")
                sensor_data.append(pressure_push_data)
                print(f"BMP180 Pressure: {pressure / 100:.2f} hPa")

            if self.options.get("bmp280", False):
                temperature, pressure, altitude = self.read_bmp280()
                if temperature is not None and pressure is not None and altitude is not None:
                    temperature_push_data = self.generate_header("bmp280_temperature", temperature, "°C", "Temperature")
                    pressure_push_data = self.generate_header("bmp280_pressure", pressure, "hPa", "Pressure")
                    altitude_push_data = self.generate_header("bmp280_altitude", altitude, "m", "Altitude")
                    sensor_data.append(temperature_push_data)
                    sensor_data.append(pressure_push_data)
                    sensor_data.append(altitude_push_data)

                    print(f"BMP280 Temperature: {temperature:.2f} °C")
                    print(f"BMP280 Pressure: {pressure:.2f} hPa")
                    print(f"BMP280 Altitude: {altitude:.2f} m")

            for data in sensor_data:
                self.post_to_home_assistant(data["url"], data["payload"])

            time.sleep(10)

if __name__ == "__main__":
    sensor_manager = SensorManager()
    sensor_manager.run()

