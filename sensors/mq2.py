#MQ-2烟雾传感器
from machine import ADC, Pin
import config

adc = ADC(Pin(config.MQ2_PIN))
adc.atten(ADC.ATTN_11DB)


def read():
    """读取MQ-2 ADC原始值，不是经过标定的ppm。"""
    try:
        return adc.read()
    except Exception as e:
        print("MQ-2读取失败：", e)
        return 0
