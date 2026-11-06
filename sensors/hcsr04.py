#HC-SR04超声波模块
from machine import Pin, time_pulse_us
import utime
import config


trig = Pin(config.HC_SR04_TRIG_PIN, Pin.OUT)
echo = Pin(config.HC_SR04_ECHO_PIN, Pin.IN)
trig.value(0)


def read():
    """读取 HC-SR04 距离，单位 cm。

    测距失败、超出有效范围时返回 -1。
    """
    try:
        trig.value(0)
        utime.sleep_us(2)

        trig.value(1)
        utime.sleep_us(10)
        trig.value(0)

        duration = time_pulse_us(echo, 1, 30000)
        if duration < 0:
            return -1

        distance = duration * 0.0343 / 2

        if distance < 2 or distance > 400:
            return -1

        return round(distance, 1)

    except Exception as e:
        print("HC-SR04读取失败：", e)
        return -1
