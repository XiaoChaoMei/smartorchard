
from umqtt.simple import MQTTClient
import config

_client = None
_subscribed = False

_pump_command_callback = None
_pump_mode_callback = None
_soil_threshold_callback = None


def set_pump_command_callback(callback):
    global _pump_command_callback
    _pump_command_callback = callback


def set_pump_mode_callback(callback):
    global _pump_mode_callback
    _pump_mode_callback = callback


def set_soil_threshold_callback(callback):
    global _soil_threshold_callback
    _soil_threshold_callback = callback


def _callback(topic, msg):
    try:
        topic_str = (
            topic.decode("utf-8")
            if isinstance(topic, bytes)
            else str(topic)
        )

        msg_str = (
            msg.decode("utf-8")
            if isinstance(msg, bytes)
            else str(msg)
        ).strip()

        print(
            "[MQTT RX] {} -> {}".format(
                topic_str, msg_str
            )
        )

        # 水泵开关控制
        if topic_str == config.TOPIC_PUMP_CONTROL:
            if _pump_command_callback:
                _pump_command_callback(msg_str)

        # 水泵模式控制
        elif topic_str == config.TOPIC_PUMP_MODE:
            if _pump_mode_callback:
                _pump_mode_callback(msg_str)

        elif topic_str == config.TOPIC_SOIL_THRESHOLD:
            if _soil_threshold_callback:
                _soil_threshold_callback(msg_str)

        # T004 只用于状态上报，不再作为控制主题

    except Exception as e:
        print("MQTT回调异常：", e)


def connect():
    global _client, _subscribed

    try:
        if _client:
            try:
                _client.disconnect()
            except Exception:
                pass

        _client = MQTTClient(
            client_id=config.BEMFA_CLIENT_ID,
            server=config.BEMFA_MQTT_SERVER,
            port=config.BEMFA_MQTT_PORT,
            user=config.BEMFA_USER,
            password=config.BEMFA_PWD,
            keepalive=config.MQTT_KEEPALIVE,
            ssl=False
        )

        _client.set_callback(_callback)
        _client.connect()
        _subscribed = False

        print("MQTT连接成功")
        return True

    except Exception as e:
        print("MQTT连接失败：", e)
        _client = None
        _subscribed = False
        return False


def subscribe():
    global _subscribed

    if not _client or _subscribed:
        return

    try:
        _client.subscribe(
            config.TOPIC_PUMP_CONTROL
        )
        print(
            "订阅主题：{}".format(
                config.TOPIC_PUMP_CONTROL
            )
        )

        _client.subscribe(
            config.TOPIC_PUMP_MODE
        )
        print(
            "订阅主题：{}".format(
                config.TOPIC_PUMP_MODE
            )
        )

        _client.subscribe(config.TOPIC_SOIL_THRESHOLD)
        print("订阅主题：{}".format(config.TOPIC_SOIL_THRESHOLD))

        _subscribed = True

    except Exception as e:
        print("MQTT订阅失败：", e)
        _subscribed = False


def check():
    if not _client:
        return

    try:
        subscribe()
        _client.check_msg()

    except Exception as e:
        print("MQTT消息检查异常：", e)


def publish(topic, data):
    if not _client:
        return False

    try:
        _client.publish(
            str(topic).encode("utf-8"),
            str(data).encode("utf-8")
        )

        print(
            "上传成功：{} -> {}".format(
                topic, data
            )
        )
        return True

    except Exception as e:
        print(
            "上传失败 {}：{}".format(topic, e)
        )
        return False


def upload_sensor_data(
    light_value, gas_value, fire, intrusion,
    rain_value, rain_type, is_raining,
    temperature, humidity, soil_value,
    pump_on, auto_mode,
    radar_detected, ultrasonic_distance
):
    if not _client:
        print("MQTT未连接，跳过上传")
        return

    publish(
        config.TOPIC_LIGHT,
        "光照强度：{}%".format(light_value)
    )

    gas_status = (
        "超标"
        if gas_value > config.MQ2_THRESHOLD
        else "正常"
    )

    publish(
        config.TOPIC_GAS,
        "气体浓度：{}，状态：{}".format(
            gas_value, gas_status
        )
    )

    publish(
        config.TOPIC_FLAME,
        "检测到火焰" if fire else "无火焰"
    )

    publish(
        config.TOPIC_HUMAN,
        "检测到人员" if intrusion else "无人员"
    )

    publish(
        config.TOPIC_RAIN,
        "降雨量：{}%，雨型：{}，状态：{}".format(
            rain_value,
            rain_type,
            "正在下雨" if is_raining else "无降雨"
        )
    )

    publish(
        config.TOPIC_TEMP_HUMI,
        "温度：{}℃，湿度：{}%".format(
            temperature, humidity
        )
    )

    pump_text = "运行中" if pump_on else "已停止"
    mode_text = "自动" if auto_mode else "手动"

    # T004 只发布状态
    publish(
        config.TOPIC_SOIL,
        "土壤湿度：{}%，水泵：{}，模式：{}".format(
            soil_value,
            pump_text,
            mode_text
        )
    )

    # LD004：RCWL-0516雷达状态
    publish(
        config.TOPIC_RADAR,
        "1" if radar_detected else "0"
    )

    # CSB004：HC-SR04距离，单位cm；-1表示本次没有有效测距
    if ultrasonic_distance >= 0:
        publish(
            config.TOPIC_ULTRASONIC,
            "{:.1f}".format(ultrasonic_distance)
        )
    else:
        publish(
            config.TOPIC_ULTRASONIC,
            "-1"
        )


def is_connected():
    return (
        _client is not None
        and hasattr(_client, "sock")
        and _client.sock is not None
    )


def ping():
    if not _client:
        return False

    try:
        _client.ping()
        return True
    except Exception:
        return False