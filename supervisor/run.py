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
        self.sensor_states = None
        # self.validate_config()
        self.headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json",
        }
        self.bus = SMBus(Constants.DEFAULT_BUS)

        if self.options.get(Constants.BMP180, False):
            self.bmp180 = BMP085(busnum=Constants.DEFAULT_BUS)

        if self.options.get(Constants.BMP280, False):
            self.bmp280 = BMP280(i2c_addr=0x76, i2c_dev=self.bus)
            self.bmp280.setup(
                mode=Constants.NORMAL,
                temperature_oversampling=16,
                pressure_oversampling=16,
                temperature_standby=500
            )

        if self.options.get(Constants.OXYGEN, False):
            self.oxygen_sensor = DFRobot_Oxygen_IIC(Constants.DEFAULT_BUS, 0x73)

        if self.options.get(Constants.SHT31, False):
            default_sht31_address = hex(Constants.DEFAULT_SHT31_SENSOR_ADDRESS)
            self.sht31_address = int(self.options.get(Constants.ADDR_SHT, default_sht31_address), 16)
            self.read_temp_hum_cmd = [0x2C, 0x06]

        # sht31 and sht45 using the same port
        if self.options.get(Constants.SHT45, False):
            self.sht45_sensor = SHT4x(bus=Constants.DEFAULT_BUS, address=hex(Constants.DEFAULT_SHT45_SENSOR_ADDRESS), mode=Constants.HIGH)

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

    def post_to_home_assistant(self, sensor_name, value, unit, friendly_name, code_name, data_type, state):
        url = f"{self.ha_base_url}/states/sensor.{sensor_name}"
        payload = {
            "state": state,
            "attributes": {
                "data_type": data_type,
                "sensor_code_name": code_name,
                "value": value,
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
            print(f"Error reading from SHT31: {e}")
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
    def find_sensor_state(self, sensor_name):
        if self.sensor_states is not None:
            sensor_current_state = next((obj for obj in self.sensor_states if sensor_name in obj['entity_id']), None)
            print("[SENSOR_CURRENT_STATE]", sensor_current_state)
            if sensor_current_state is not None:
                return sensor_current_state['state']
        return 1
            

    def run(self):
        while True:
            response = self.utils.get_states(self.ha_base_url, self.headers)
            if response is not None:
                filtered_sensor = list(filter(lambda obj: obj['entity_id'].startswith("sensor."), response))
                print('[FILTERD_SENSOR]',filtered_sensor)
                self.result = filtered_sensor
            if self.options.get(Constants.BMP180, False):
                try:
                    pressure = self.bmp180.read_pressure()
                    altitude = self.utils.calculate_altitude(pressure)
                    pressure_sensor_state = self.find_sensor_state(Constants.BMP180_PRESSURE_SENSOR_NAME)
                    altitude_sensor_state = self.find_sensor_state(Constants.BMP180_ALTITUDE_SENSOR_NAME)
                    print(f"BMP180 pressure sensor: {pressure} {Constants.PRESSURE_UNIT}, state: {pressure_sensor_state}")
                    print(f"BMP180 altitude sensor: {altitude} {Constants.ALTITUDE_UNIT}, state: {altitude_sensor_state}")
                    self.post_to_home_assistant(Constants.BMP180_PRESSURE_SENSOR_NAME, round(pressure / 100, 2), Constants.PRESSURE_UNIT, Constants.BMP180_PRESSURE_FRIENDLY_NAME, Constants.BMP180, Constants.PRESSURE, pressure_sensor_state)
                    self.post_to_home_assistant(Constants.BMP180_ALTITUDE_SENSOR_NAME, round(altitude, 2), Constants.ALTITUDE_UNIT, Constants.BMP180_ALTITUDE_FRIENDLY_NAME, Constants.BMP180, Constants.ALTITUDE, altitude_sensor_state)
                except Exception as e:
                    print(f"Error reading BMP180: {e}")

            if self.options.get(Constants.BMP280, False):
                try:
                    temperature = self.bmp280.get_temperature()
                    pressure = self.bmp280.get_pressure()
                    altitude = self.utils.calculate_altitude(pressure)
                    if temperature is not None and pressure is not None and altitude is not None:
                        temperature_sensor_state = self.find_sensor_state(Constants.BMP280_TEMPERATURE_SENSOR_NAME)
                        pressure_sensor_state = self.find_sensor_state(Constants.BMP280_PRESSURE_SENSOR_NAME)
                        altitude_sensor_state = self.find_sensor_state(Constants.BMP280_ALTITUDE_SENSOR_NAME)
                        print(f"BMP280 temperature sensor: {temperature} {Constants.TEMPERATURE_UNIT}, state: {temperature_sensor_state}")
                        print(f"BMP280 pressure sensor: {pressure} {Constants.PRESSURE_UNIT}, state: {pressure_sensor_state}")
                        print(f"BMP280 altitude sensor: {altitude} {Constants.ALTITUDE_UNIT}, state: {altitude_sensor_state}")
                        self.post_to_home_assistant(Constants.BMP280_TEMPERATURE_SENSOR_NAME, round(temperature, 2), Constants.TEMPERATURE_UNIT, Constants.BMP280_TEMPERATURE_FRIENDLY_NAME, Constants.BMP280, Constants.TEMPERATURE, temperature_sensor_state)
                        self.post_to_home_assistant(Constants.BMP280_PRESSURE_SENSOR_NAME, round(pressure, 2), Constants.PRESSURE_UNIT, Constants.BMP280_PRESSURE_FRIENDLY_NAME, Constants.BMP280, Constants.PRESSURE, pressure_sensor_state)
                        self.post_to_home_assistant(Constants.BMP280_ALTITUDE_SENSOR_NAME, round(altitude, 2), Constants.ALTITUDE_UNIT, Constants.BMP280_ALTITUDE_FRIENDLY_NAME, Constants.BMP280, Constants.ALTITUDE, altitude_sensor_state)
                except Exception as e:
                    print(f"Error reading BMP280: {e}")

            if self.options.get(Constants.SHT31, False):
                try:
                    temperature, humidity = self.read_sht31()
                    if temperature is not None and humidity is not None:
                        # calcualte absolute humidity and dew point
                        absolute_humidity = self.utils.calculate_absolute_humidity(temperature, humidity)
                        dew_point = self.utils.calculate_dew_point(temperature, humidity)
                        # get states
                        temperature_sensor_state = self.find_sensor_state(Constants.SHT31_TEMPERATURE_SENSOR_NAME)
                        humidity_sensor_state = self.find_sensor_state(Constants.SHT31_HUMIDITY_SENSOR_NAME)
                        absolute_humidity_sensor_state = self.find_sensor_state(Constants.SHT31_ABSOLUTE_HUMIDITY_SENSOR_NAME)
                        dew_point_sensor_state = self.find_sensor_state(Constants.SHT31_DEW_POINT_SENSOR_NAME)
                        # push data
                        print(f"SHT31 absolute humidity: {absolute_humidity} {Constants.ABSOLUTE_HUMIDITY_UNIT}, state: {absolute_humidity_sensor_state}")
                        print(f"SHT31 dew point : {dew_point} {Constants.TEMPERATURE_UNIT}, state: {dew_point_sensor_state}")
                        print(f"SHT31 temperature: {temperature} {Constants.TEMPERATURE_UNIT}, state: {temperature_sensor_state}")
                        print(f"SHT31 humidity : {humidity} {Constants.HUMIDITY_UNIT}, state: {humidity_sensor_state}")
                        self.post_to_home_assistant(Constants.SHT31_TEMPERATURE_SENSOR_NAME, round(temperature, 2), Constants.TEMPERATURE_UNIT, Constants.SHT31_TEMPERATURE_FRIENDLY_NAME, Constants.SHT31, Constants.TEMPERATURE, temperature_sensor_state)
                        self.post_to_home_assistant(Constants.SHT31_HUMIDITY_SENSOR_NAME, round(humidity, 2), Constants.HUMIDITY_UNIT, Constants.SHT45_HUMIDITY_FRIENDLY_NAME, Constants.SHT31, Constants.HUMIDITY, humidity_sensor_state)
                        self.post_to_home_assistant(Constants.SHT31_ABSOLUTE_HUMIDITY_SENSOR_NAME, round(absolute_humidity, 2), Constants.ABSOLUTE_HUMIDITY_UNIT, Constants.SHT31_ABSOLUTE_HUMIDITY_FRIENDLY_NAME, Constants.SHT31, Constants.ABSOLUTE_HUMIDITY, absolute_humidity_sensor_state)
                        self.post_to_home_assistant(Constants.SHT31_DEW_POINT_SENSOR_NAME, round(dew_point, 2), Constants.TEMPERATURE_UNIT, Constants.SHT31_DEW_POINT_FRIENDLY_NAME, Constants.SHT31, Constants.DEW_POINT, dew_point_sensor_state)
                except Exception as e:
                    print(f"Error reading SHT31: {e}")

            if self.options.get(Constants.SHT45, False):
                try:
                    temperature, humidity = self.read_sht45()
                    if temperature is not None and humidity is not None:
                        # calcualte absolute humidity and dew point
                        absolute_humidity = self.utils.calculate_absolute_humidity(temperature, humidity)
                        dew_point = self.utils.calculate_dew_point(temperature, humidity)
                        #get states
                        temperature_sensor_state = self.find_sensor_state(Constants.SHT45_TEMPERATURE_SENSOR_NAME)
                        humidity_sensor_state = self.find_sensor_state(Constants.SHT45_HUMIDITY_SENSOR_NAME)
                        absolute_humidity_sensor_state = self.find_sensor_state(Constants.SHT45_ABSOLUTE_HUMIDITY_SENSOR_NAME)
                        dew_point_sensor_state = self.find_sensor_state(Constants.SHT45_DEW_POINT_SENSOR_NAME)
                        # push data
                        print(f"SHT45 absolute humidity: {absolute_humidity} {Constants.ABSOLUTE_HUMIDITY_UNIT}, state: {absolute_humidity_sensor_state}")
                        print(f"SHT45 dew point : {dew_point} {Constants.TEMPERATURE_UNIT}, state: {dew_point_sensor_state}")
                        print(f"SHT45 temperature: {temperature} {Constants.TEMPERATURE_UNIT}, state: {temperature_sensor_state}")
                        print(f"SHT45 humidity : {humidity} {Constants.HUMIDITY_UNIT}, state: {humidity_sensor_state}")
                        self.post_to_home_assistant(Constants.SHT45_TEMPERATURE_SENSOR_NAME, round(temperature, 2), Constants.TEMPERATURE_UNIT, Constants.SHT45_TEMPERATURE_FRIENDLY_NAME, Constants.SHT45, Constants.TEMPERATURE, temperature_sensor_state)
                        self.post_to_home_assistant(Constants.SHT45_HUMIDITY_SENSOR_NAME, round(humidity, 2), Constants.HUMIDITY_UNIT, Constants.SHT45_HUMIDITY_FRIENDLY_NAME, Constants.SHT45, Constants.HUMIDITY, humidity_sensor_state)
                        self.post_to_home_assistant(Constants.SHT45_ABSOLUTE_HUMIDITY_SENSOR_NAME, round(absolute_humidity, 2), Constants.ABSOLUTE_HUMIDITY_UNIT, Constants.SHT45_ABSOLUTE_HUMIDITY_FRIENDLY_NAME, Constants.SHT45, Constants.ABSOLUTE_HUMIDITY, absolute_humidity_sensor_state)
                        self.post_to_home_assistant(Constants.SHT45_DEW_POINT_SENSOR_NAME, round(dew_point, 2), Constants.TEMPERATURE_UNIT, Constants.SHT45_DEW_POINT_FRIENDLY_NAME, Constants.SHT45, Constants.DEW_POINT, dew_point_sensor_state)
                except Exception as e:
                    print(f"Error reading SHT45: {e}")

            if self.options.get(Constants.OXYGEN, False):
                try:
                    oxygen_concentration = self.read_oxygen()
                    if oxygen_concentration is not None:
                        oxygen_sensor_state = self.find_sensor_state(Constants.OXYGEN_SENSOR_NAME)
                        print(f"Oxygen concentration : {oxygen_concentration} {Constants.OXYGEN_CONCENTRATION_UNIT}, state: {oxygen_sensor_state}")
                        self.post_to_home_assistant(Constants.OXYGEN_SENSOR_NAME, round(oxygen_concentration, 2), Constants.OXYGEN_CONCENTRATION_UNIT, Constants.OXYGEN_FRIENDLY_NAME, Constants.OXYGEN, Constants.OXYGEN_CONCENTRATION, oxygen_sensor_state)
                except Exception as e:
                    print(f"Error reading Oxygen sensor: {e}")
            time.sleep(10)

if __name__ == "__main__":
    sensor_manager = SensorManager()
    sensor_manager.run()

