#光敏电阻传感器
from machine import ADC, Pin
import config

adc = ADC(Pin(config.LIGHT_PIN))
adc.atten(ADC.ATTN_11DB)


def read():
    """读取相对光照强度，返回0~100%。"""
    try:
        raw = adc.read()

        intensity = 100 - (
            (raw - config.LIGHT_MIN_RAW) /
            (config.LIGHT_MAX_RAW - config.LIGHT_MIN_RAW)
        ) * 100

        return max(0.0, min(100.0, round(intensity, 1)))
    except Exception as e:
        print("光照失败：", e)
        return 0.0
