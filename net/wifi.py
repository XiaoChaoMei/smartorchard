# Wi-Fi连接与配网配置读取
import network as mp_network
import utime
import ujson
import config

CONFIG_FILE = "net/wifi_config.json"
CONNECT_TIMEOUT = 20


def _load_credentials():
    """优先读取配网页面保存的配置；没有配置文件时使用 config.py 默认值。"""
    try:
        with open(CONFIG_FILE, "r") as f:
            data = ujson.loads(f.read())
        ssid = data.get("ssid", "")
        password = data.get("password", "")
        if ssid:
            return ssid, password
    except Exception:
        pass
    return config.WIFI_SSID, config.WIFI_PASSWORD


def connect(timeout=CONNECT_TIMEOUT):
    wlan = mp_network.WLAN(mp_network.STA_IF)
    wlan.active(True)

    ssid, password = _load_credentials()
    if not ssid:
        print("没有已保存的 Wi-Fi，进入配网模式")
        return None

    if wlan.isconnected():
        print("Wi-Fi已连接：{}".format(wlan.ifconfig()[0]))
        return wlan

    print("尝试连接 Wi-Fi：{}".format(ssid))
    try:
        wlan.disconnect()
    except Exception:
        pass

    wlan.connect(ssid, password)
    for i in range(timeout):
        if wlan.isconnected():
            print("Wi-Fi连接成功：{}".format(wlan.ifconfig()[0]))
            return wlan
        if i % 5 == 0:
            print("等待 Wi-Fi 连接... {}/{}秒".format(i + 1, timeout))
        utime.sleep(1)

    print("Wi-Fi连接超时，准备开启配网热点")
    try:
        wlan.disconnect()
    except Exception:
        pass
    return None
