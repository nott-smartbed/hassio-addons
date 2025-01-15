import requests
import library.constants as Constants
import math
import json

class Utils:
    def calculate_altitude(self, pressure):
        return Constants.ALTITUDE_SCALING_FACTOR * (1 - (pressure / Constants.SEA_LEVEL_PRESSURE) ** (Constants.PRESSURE_EXPONENT))

    def calculate_absolute_humidity(self, temperature, relative_humidity):
        T = temperature
        RH = relative_humidity / 100.0 # convert % to decimal fraction
        Mw = Constants.MOLAR_MASS_WATER
        R = Constants.UNIVERSAL_GAS_CONSTANT
        es = Constants.SATURATION_VAPOR_CONSTANT * math.exp((Constants.TEMP_EXPONENTIAL_NUMERATOR * T) / (T + Constants.TEMP_EXPONENTIAL_DENOMINATOR)) * 100
        absolute_humidity = (es * RH * Mw) / (R * (T + Constants.C_TO_K_CONVERSION)) * 1000
        return absolute_humidity

    def calculate_dew_point(self, temperature, relative_humidity):
        T = temperature
        RH = relative_humidity
        gamma = math.log(RH / 100.0) + (Constants.TEMP_EXPONENTIAL_NUMERATOR * T) / (T + Constants.TEMP_EXPONENTIAL_DENOMINATOR)
        dew_point = (Constants.TEMP_EXPONENTIAL_DENOMINATOR * gamma) / (Constants.TEMP_EXPONENTIAL_NUMERATOR - gamma)
        return dew_point
    
    def process_sht31_data(self, data):
            temp_raw = (data[0] << 8) + data[1]
            humidity_raw = (data[3] << 8) + data[4]
            temperature = -45 + (175 * temp_raw / 65535.0)
            humidity = (100 * humidity_raw / 65535.0)
            return temperature, humidity
    
    def get_states(self, url, headers):        
        try:
            print(headers)
            response = requests.get(f'{url}/states', headers=headers)
            response.raise_for_status()  # Raises an exception for HTTP error codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Home Assistant: {e}")
             