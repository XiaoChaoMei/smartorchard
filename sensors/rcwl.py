#RCWL-0516 雷达传感器
from machine import Pin
import config


sensor = Pin(config.RCWL_PIN, Pin.IN)


def read():
    """读取 RCWL-0516 雷达状态。

    返回：
        True  = 检测到移动目标
        False = 未检测到移动目标
    """
    return sensor.value() == 1
