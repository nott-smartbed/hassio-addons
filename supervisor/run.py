import os
import time
import math
import json
import requests
from library.bmp280_driver import BMP280
from smbus2 import SMBus
from Adafruit_BMP.BMP085 import BMP085
from library.DFRobot_Oxygen import DFRobot_Oxygen_IIC
from library.SHT4x import SHT4x
import library.constants as Constants
from library.utils import Utils

class SensorManager:
    def __init__(self, options_path="/data/options.json"):
        self.options = self.load_options(options_path)
        self.ha_base_url = "http://supervisor/core/api"
        self.ha_token = os.getenv("SUPERVISOR_TOKEN")
        self.utils = Utils()
        # self.validate_config()
        self.headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json",
        }
        self.bus = SMBus(Constants.DEFAULT_BUS)

        if self.options.get(Constants.BMP180, False):
            self.bmp180 = BMP085(busnum=Constants.DEFAULT_BUS)

        if self.options.get(Constants.BMP280, False):
            self.bmp280 = BMP280(i2c_addr=Constants.DEFAULT_BMP280_SENSOR_ADDRESS, i2c_dev=Constants.DEFAULT_BUS)
            self.bmp280.setup(
                mode=Constants.NORMAL,
                temperature_oversampling=16,
                pressure_oversampling=16,
                temperature_standby=500
            )

        if self.options.get(Constants.OXYGEN, False):
            self.oxygen_sensor = DFRobot_Oxygen_IIC(Constants.DEFAULT_BUS, Constants.DEFAULT_OXYGEN_SENSOR_ADDRESS)

        if self.options.get(Constants.SHT31, False):
            self.sht31_address = Constants.DEFAULT_SHT31_SENSOR_ADDRESS
            self.read_temp_hum_cmd = [0x2C, 0x06]

        # sht31 and sht45 using the same port
        if self.options.get(Constants.SHT45, False):
            self.sht45_sensor = SHT4x(bus=self.bus, address=Constants.DEFAULT_SHT45_SENSOR_ADDRESS, mode=Constants.HIGH)

    def load_options(self, file_path):
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading options: {e}")
            return {}

    def validate_config(self):
        if not self.ha_token:
            print("Error: Supervisor token is missing.")
            exit(1)

    def post_to_home_assistant(self, sensor_name, value, unit, friendly_name):
        url = f"{self.ha_base_url}/states/sensor.{sensor_name}"
        payload = {
            "state": value,
            "attributes": {
                "unit_of_measurement": unit,
                "friendly_name": friendly_name,
            },
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            print(f"Data posted to {sensor_name}: {value}{unit}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting to Home Assistant: {e}")

    def read_sht31(self):
        try:
            self.bus.write_i2c_block_data(self.sht31_address, self.read_temp_hum_cmd[0], self.read_temp_hum_cmd[1:])
            time.sleep(0.5)
            data = self.bus.read_i2c_block_data(self.sht31_address, 0x00, 6)
            temperature, humidity = self.utils.process_sht31_data(data)
            return temperature, humidity
        except Exception as e:
            print(f"Error reading SHT31: {e}")
            return None, None

    def read_sht45(self):
        try:
            self.sht45_sensor.update()
            temperature = self.sht45_sensor.temperature
            humidity = self.sht45_sensor.humidity
            return temperature, humidity
        except Exception as e:
            print(f"Error reading SHT45: {e}")
            return None, None

    def read_oxygen(self):
        try:
            oxygen_concentration = self.oxygen_sensor.get_oxygen_data(collect_num=20)
            return oxygen_concentration
        except Exception as e:
            print(f"Error reading Oxygen sensor: {e}")
            return None

    def run(self):
        while True:
            if self.options.get(Constants.BMP180, False):
                try:
                    pressure = self.bmp180.read_pressure()
                    print(pressure, altitude)
                    self.post_to_home_assistant(Constants.BMP180_PRESSURE_SENSOR_NAME, round(pressure / 100, 2), Constants.PRESSURE_UNIT, Constants.BMP180_PRESSURE_FIENDLY_NAME)
                    self.post_to_home_assistant(Constants.BMP180_ALTITUDE_SENSOR_NAME, round(altitude, 2), Constants.HEIGHT_UNIT, Constants.BMP180_ALTITUDE_FIENDLY_NAME)
                except Exception as e:
                    print(f"Error reading BMP180: {e}")

            if self.options.get(Constants.BMP280, False):
                try:
                    temperature = self.bmp280.get_temperature()
                    pressure = self.bmp280.get_pressure()
                    altitude = self.utils.calculate_altitude(pressure)
                    self.post_to_home_assistant(Constants.BMP280_TEMPERATURE_SENSOR_NAME, round(temperature, 2), Constants.TEMPERATURE_UNIT, Constants.BMP280_TEMPERATURE_FIENDLY_NAME)
                    self.post_to_home_assistant(Constants.BMP280_PRESSURE_SENSOR_NAME, round(pressure, 2), Constants.PRESSURE_UNIT, Constants.BMP280_PRESSURE_FIENDLY_NAME)
                    self.post_to_home_assistant(Constants.BMP280_ALTITUDE_SENSOR_NAME, round(altitude, 2), Constants.HEIGHT_UNIT, Constants.BMP280_ALTITUDE_FIENDLY_NAME)
                except Exception as e:
                    print(f"Error reading BMP280: {e}")

            if self.options.get(Constants.SHT31, False):
                try:
                    temperature, humidity = self.read_sht31()
                    if temperature is not None and humidity is not None:
                        absolute_humidity = self.utils.calculate_absolute_humidity(temperature, humidity)
                        dew_point = self.utils.calculate_dew_point(temperature, humidity)
                        self.post_to_home_assistant(Constants.SHT31_TEMPERATURE_SENSOR_NAME, round(temperature, 2), Constants.TEMPERATURE_UNIT, Constants.SHT31_TEMPERATURE_FIENDLY_NAME)
                        self.post_to_home_assistant(Constants.SHT31_HUMIDITY_SENSOR_NAME, round(humidity, 2), Constants.HUMIDITY_UNIT, Constants.SHT31_ABSOLUTE_HUMIDITY_FIENDLY_NAME)
                        self.post_to_home_assistant(Constants.SHT31_ABSOLUTE_HUMIDITY_SENSOR_NAME, round(absolute_humidity, 2), Constants.ABSOLUTE_HUMIDITY_UNIT, Constants.SHT31_ABSOLUTE_HUMIDITY_FIENDLY_NAME)
                        self.post_to_home_assistant(Constants.SHT31_DEW_POINT_SENSOR_NAME, round(dew_point, 2), Constants.TEMPERATURE_UNIT, Constants.SHT31_DEW_POINT_FIENDLY_NAME)
                except Exception as e:
                    print(f"Error reading SHT31: {e}")

            if self.options.get(Constants.SHT45, False):
                try:
                    temperature, humidity = self.read_sht45()
                    if temperature is not None and humidity is not None:
                        absolute_humidity = self.utils.calculate_absolute_humidity(temperature, humidity)
                        dew_point = self.utils.calculate_dew_point(temperature, humidity)
                        self.post_to_home_assistant(Constants.SHT45_TEMPERATURE_SENSOR_NAME, round(temperature, 2), Constants.TEMPERATURE_UNIT, Constants.SHT45_TEMPERATURE_FIENDLY_NAME)
                        self.post_to_home_assistant(Constants.SHT45_HUMIDITY_SENSOR_NAME, round(humidity, 2), Constants.HUMIDITY_UNIT, Constants.SHT45_ABSOLUTE_HUMIDITY_FIENDLY_NAME)
                        self.post_to_home_assistant(Constants.SHT45_ABSOLUTE_HUMIDITY_SENSOR_NAME, round(absolute_humidity, 2), Constants.ABSOLUTE_HUMIDITY_UNIT, Constants.SHT45_ABSOLUTE_HUMIDITY_FIENDLY_NAME)
                        self.post_to_home_assistant(Constants.SHT45_DEW_POINT_SENSOR_NAME, round(dew_point, 2), Constants.TEMPERATURE_UNIT, Constants.SHT45_DEW_POINT_FIENDLY_NAME)
                except Exception as e:
                    print(f"Error reading SHT45: {e}")

            if self.options.get(Constants.OXYGEN, False):
                try:
                    oxygen_concentration = self.read_oxygen()
                    if oxygen_concentration is not None:
                        self.post_to_home_assistant("oxygen_concentration", round(oxygen_concentration, 2), "%", "Oxygen Concentration")
                except Exception as e:
                    print(f"Error reading Oxygen sensor: {e}")

            time.sleep(10)


if __name__ == "__main__":
    sensor_manager = SensorManager()
    sensor_manager.run()

