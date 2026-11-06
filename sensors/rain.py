#雨水传感器
from machine import ADC, Pin
import utime
import config

adc = ADC(Pin(config.RAIN_PIN))
adc.atten(ADC.ATTN_11DB)

calibrated_dry = 0.0
calibrated_wet = 4095


def calibrate():
    """开机校准一次。校准时请确保雨滴传感器完全干燥。"""
    global calibrated_dry, calibrated_wet

    print("开始校准雨滴传感器，请确保传感器处于干燥状态...")

    values = []
    for _ in range(20):
        values.append(adc.read())
        utime.sleep_ms(20)

    calibrated_dry = sum(values) / len(values)
    calibrated_wet = 4095 if calibrated_dry < 2000 else 0

    print(
        "雨滴传感器校准完成：干燥值={:.1f}，湿润极值={}".format(
            calibrated_dry, calibrated_wet
        )
    )


def read():
    """返回 (is_raining, rain_percent, rain_type)。"""
    try:
        values = []
        for _ in range(10):
            values.append(adc.read())
            utime.sleep_ms(5)

        raw = sum(values) / len(values)

        if abs(raw - calibrated_dry) < config.RAIN_SENSITIVITY:
            return False, 0.0, "无雨"

        if calibrated_wet > calibrated_dry:
            percent = (
                (raw - calibrated_dry) /
                (calibrated_wet - calibrated_dry)
            ) * 100
        else:
            percent = (
                (calibrated_dry - raw) /
                (calibrated_dry - calibrated_wet)
            ) * 100

        percent = max(0.0, min(100.0, round(percent, 1)))

        if percent < 20:
            rain_type = "小雨"
        elif percent < 40:
            rain_type = "中雨"
        elif percent < 70:
            rain_type = "大雨"
        else:
            rain_type = "暴雨"

        return True, percent, rain_type

    except Exception as e:
        print("雨滴传感器读取失败：", e)
        return False, 0.0, "未知"
