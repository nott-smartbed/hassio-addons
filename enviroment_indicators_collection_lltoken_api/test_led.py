import time
import OPi.GPIO as GPIO

class WS2812:
    def __init__(self, pin, led_count):
        self.pin = pin
        self.led_count = led_count
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)
        self.reset_pulse()

    def reset_pulse(self):
        """Send a reset signal to WS2812 (low for at least 50μs)."""
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(0.00005)  # 50μs

    def send_bit(self, value):
        """Send a single bit to WS2812."""
        if value:  # '1' bit
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.0008)  # 800ns high
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(0.00045)  # 450ns low
        else:  # '0' bit
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(0.0004)  # 400ns high
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(0.00085)  # 850ns low

    def send_byte(self, byte):
        """Send a byte to WS2812."""
        for i in range(8):
            self.send_bit(byte & (1 << (7 - i)))

    def send_color(self, r, g, b):
        """Send RGB color to WS2812 (in GRB order)."""
        self.send_byte(g)  # Green
        self.send_byte(r)  # Red
        self.send_byte(b)  # Blue

    def show(self, colors):
        """Send a list of RGB tuples to the LED strip."""
        for r, g, b in colors:
            self.send_color(r, g, b)
        self.reset_pulse()

    def cleanup(self):
        """Cleanup GPIO."""
        GPIO.cleanup()


# Example usage
if __name__ == "__main__":
    try:
        led_count = 4
        ws = WS2812(pin=15, led_count=led_count)
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]  # RGB colors
        ws.show(colors)
        time.sleep(1)
        ws.show([(0, 0, 0)] * led_count)  # Turn off LEDs
    finally:
        ws.cleanup()
