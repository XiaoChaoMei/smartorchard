from machine import Pin
import config

buzzer = Pin(config.BUZZER_PIN, Pin.OUT)
buzzer.on()  # 高电平关闭


def on(reason="未指定原因"):
    buzzer.on()
    print("【蜂鸣器 OFF】原因：{}".format(reason))


def off(reason="未指定原因"):
    buzzer.off()
    print("【蜂鸣器 ON】原因：{}".format(reason))


def set_fire(fire_detected):
    if fire_detected:
        off("检测到火焰")
    else:
        on("未检测到火焰")
