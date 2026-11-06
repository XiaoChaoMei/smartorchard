#人体红外传感器
from machine import Pin
import utime
import config

sensor = Pin(config.PIR_PIN, Pin.IN)


def read():
    """连续读取3次，多数为1则认为有人。"""
    values = []
    for _ in range(3):
        values.append(sensor.value())
        utime.sleep_ms(10)

    return values.count(1) >= 2
