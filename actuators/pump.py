from machine import Pin
import config

relay = Pin(config.PUMP_PIN, Pin.OUT)
relay.off()

_state = False


def on(reason="未指定原因"):
    global _state
    relay.on()
    _state = True
    print("【水泵 ON】原因：{}".format(reason))


def off(reason="未指定原因"):
    global _state
    relay.off()
    _state = False
    print("【水泵 OFF】原因：{}".format(reason))


def is_on():
    return _state
