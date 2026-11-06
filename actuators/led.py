from machine import Pin
import config

led = Pin(config.LED_PIN, Pin.OUT)
led.off()


def on(reason="未指定原因"):
    led.on()
    print("【LED ON】原因：{}".format(reason))


def off(reason="未指定原因"):
    led.off()
    print("【LED OFF】原因：{}".format(reason))


def set_intrusion(intrusion_detected):
    if intrusion_detected:
        on("检测到人员")
    else:
        off("未检测到人员")
