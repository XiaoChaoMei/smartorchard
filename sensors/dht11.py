#DHT11温湿度传感器
import dht
from machine import Pin
import utime
import config

sensor = dht.DHT11(Pin(config.DHT11_PIN))


def read():
    """读取温度、湿度，返回 (temperature, humidity)。"""
    for attempt in range(3):
        try:
            sensor.measure()
            temp = round(sensor.temperature(), 1)
            humi = round(sensor.humidity(), 1)
            return temp, humi
        except Exception as e:
            print("DHT11失败（{}）：{}".format(attempt + 1, e))
            utime.sleep_ms(200)

    return 0.0, 0.0
