import time

PI_AVAILABLE = False
try:
    import Adafruit_DHT
    import RPi.GPIO as GPIO
    PI_AVAILABLE = True
except ImportError:
    print("Adafruit_DHT or RPi.GPIO not available. Running in non-PI mode.")


class SensorService:
    def __init__(self):
        self.simulation_mode = not PI_AVAILABLE
        if not self.simulation_mode:
            # Khởi tạo loại cảm biến và pin
            self.dht_sensor = Adafruit_DHT.DHT11
            self.dht_pin = 4  # GPIO4 (Pin 7)
            self.noise_pin = 17  # GPIO17 (Pin 11) - Giả sử pin cho cảm biến âm thanh analog

            # Khởi tạo GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Thiết lập pin nếu cần
            # GPIO.setup(self.noise_pin, GPIO.IN)
            print("Sensor service initialized")
        else:
            print("Running in simulation mode. No sensors available.")

    def read_dht11(self):
        """Đọc nhiệt độ và độ ẩm từ cảm biến DHT11"""
        if not self.simulation_mode:
            for _ in range(3):  # Thử 3 lần nếu đọc thất bại
                humidity, temperature = Adafruit_DHT.read_retry(
                    self.dht_sensor, self.dht_pin
                )
                if humidity is not None and temperature is not None:
                    return {
                        "temperature": round(temperature, 1),
                        "humidity": round(humidity, 1),
                    }
                time.sleep(2)

            # Trả về giá trị mặc định nếu không đọc được
            return {
                "temperature": 0,
                "humidity": 0,
                "error": "Failed to read from DHT11 sensor",
            }
        else:
            # Mô phỏng dữ liệu cảm biến DHT11 trong chế độ mô phỏng
            import random
            return {
                'temperature': round(random.uniform(18, 30), 1),
                'humidity': round(random.uniform(30, 80), 1)
            }

    def read_noise_level(self):
        """Đọc mức độ tiếng ồn từ cảm biến âm thanh
        Lưu ý: Đây là một ví dụ, bạn cần thay thế bằng code thực tế cho cảm biến âm thanh của mình
        """
        if self.simulation_mode:
            # Mô phỏng dữ liệu cảm biến âm thanh trong chế độ mô phỏng
            import random
            return round(random.uniform(30, 100), 1)
        try:
            # Đây là code mẫu - cần thay thế bằng code thực tế cho cảm biến âm thanh
            # Giả sử bạn đang sử dụng analog sound sensor qua MCP3008 ADC
            # import Adafruit_MCP3008
            # adc = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 0))
            # raw_value = adc.read_adc(0)  # đọc từ kênh 0

            # Mô phỏng đọc giá trị
            raw_value = 300  # giá trị mẫu

            # Chuyển đổi giá trị sang dB (cần hiệu chỉnh theo cảm biến thực tế)
            # Công thức này chỉ là ví dụ
            noise_db = 20 * (raw_value / 1023)

            return round(noise_db, 1)
        except Exception as e:
            print(f"Error reading noise level: {e}")
            return 0

    def read_all_sensors(self):
        """Đọc tất cả các cảm biến và trả về dữ liệu"""
        dht_data = self.read_dht11()
        noise_level = self.read_noise_level()

        return {
            "temperature": dht_data.get("temperature", 0),
            "humidity": dht_data.get("humidity", 0),
            "noise": noise_level,
            "timestamp": time.time(),
        }

    def cleanup(self):
        """Dọn dẹp GPIO khi đóng ứng dụng"""
        GPIO.cleanup()
