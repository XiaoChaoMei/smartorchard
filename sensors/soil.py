#土壤湿度传感器
from machine import ADC, Pin
import utime
import config

adc = ADC(Pin(config.SOIL_PIN))
adc.atten(ADC.ATTN_11DB)


def read():
    """读取土壤湿度，返回 0~100%。"""
    try:
        values = []
        for _ in range(10):
            values.append(adc.read())
            utime.sleep_ms(5)

        raw = sum(values) / len(values)

        moisture = 100 - (
            (raw - config.SOIL_MIN_RAW) /
            (config.SOIL_MAX_RAW - config.SOIL_MIN_RAW)
        ) * 100

        return max(0.0, min(100.0, round(moisture, 1)))
    except Exception as e:
        print("土壤湿度失败：", e)
        return 0.0
