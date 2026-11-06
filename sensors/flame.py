#火焰传感器
from machine import Pin
import utime
import config

sensor = Pin(config.FLAME_PIN, Pin.IN, Pin.PULL_UP)


def read():
    """连续读取3次，多数为0则认为检测到火焰。"""
    values = []
    for _ in range(3):
        values.append(sensor.value())
        utime.sleep_ms(10)

    return values.count(0) >= 2
