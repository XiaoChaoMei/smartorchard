import utime
import config

from sensors import soil, dht11, mq2, rain, pir, flame, light, rcwl, hcsr04
from actuators import pump, buzzer, led
from net import wifi, mqtt


pump_mode = "auto"
last_sensor_data = None
last_intrusion = None
last_fire = None
last_led_state = False
soil_low_threshold = config.SOIL_LOW_THRESHOLD

# 驱鸟状态
bird_confirm_count = 0
bird_clear_count = 0
bird_target_detected = False


def print_control_rules():
    print("")
    print("========== 当前系统控制规则 ==========")
    print("1.  土壤湿度 < 当前设置阈值 → 自动启动水泵")
    print("2.  土壤湿度 > 85%  → 自动停止水泵")
    print("3.  土壤湿度 55%~85% → 水泵保持当前状态")
    print("4.  MQTT pump=on    → 手动启动水泵")
    print("5.  MQTT pump=off   → 手动停止水泵")
    print("6.  MQTT pump=auto  → 恢复自动控制")
    print("7.  检测到火焰      → 蜂鸣器启动")
    print("8.  未检测到火焰    → 蜂鸣器关闭")
    print("9.  检测到人员且光照不足 → LED补光灯开启")
    print("10. 检测到人员且光照充足 → LED补光灯关闭")
    print("11. 未检测到人员         → LED补光灯关闭")
    print("11. 雨滴传感器     → 仅检测/上传雨情，不控制水泵")
    print("12. MQ-2 > 800     → 上传“气体超标”，不联动执行器")
    print("13. RCWL检测移动   → 使用HC-SR04确认距离")
    print("14. 雷达+距离连续满足 → 判定为驱鸟目标")
    print("15. LD004/CSB004    → 上传雷达状态和目标距离")
    print("======================================")
    print("")



def handle_pump_command(command):
    global pump_mode

    if command == "on":
        pump_mode = "manual"
        print("【控制模式】切换为手动")
        pump.on("收到P004指令 on")

    elif command == "off":
        pump_mode = "manual"
        print("【控制模式】切换为手动")
        pump.off("收到P004指令 off")

    else:
        print("【水泵控制】未知指令：", command)


def handle_pump_mode(command):
    global pump_mode

    if command == "auto":
        pump_mode = "auto"
        print("【控制模式】恢复自动控制")

    elif command == "manual":
        pump_mode = "manual"
        print("【控制模式】切换为手动")

    else:
        print("【模式控制】未知指令：", command)


def handle_soil_threshold(command):
    global soil_low_threshold
    try:
        value = float(command)
        if value < 30 or value > 80:
            print("【阈值设置失败】范围必须为30~80%")
            return
        soil_low_threshold = value
        print("【自动浇水阈值更新】启动阈值：{}%，停止阈值：{}%".format(soil_low_threshold, config.SOIL_HIGH_THRESHOLD))
    except Exception as e:
        print("【阈值设置失败】无效指令：", command, e)


def control_pump(soil_value):
    if pump_mode == "manual":
        return

    if soil_value < soil_low_threshold and not pump.is_on():
        pump.on("自动浇水：土壤湿度 {:.1f}% < 启动阈值 {:.1f}%".format(soil_value, soil_low_threshold))
    elif soil_value > config.SOIL_HIGH_THRESHOLD and pump.is_on():
        pump.off("自动停止：土壤湿度 {:.1f}% > 停止阈值 {:.1f}%".format(soil_value, config.SOIL_HIGH_THRESHOLD))

    else:
        if pump.is_on():
            print(
                "【水泵保持 ON】土壤湿度 {:.1f}% 在保持区间".format(
                    soil_value
                )
            )
        else:
            print(
                "【水泵保持 OFF】土壤湿度 {:.1f}% 在保持区间".format(
                    soil_value
                )
            )


def read_all_sensors():
    soil_value = soil.read()
    temperature, humidity = dht11.read()
    gas_value = mq2.read()
    is_raining, rain_value, rain_type = rain.read()
    intrusion = pir.read()
    fire = flame.read()
    light_value = light.read()

    # 驱鸟：RCWL-0516检测到移动后，再读取HC-SR04距离。
    radar_detected = rcwl.read()
    if radar_detected:
        ultrasonic_distance = hcsr04.read()
    else:
        ultrasonic_distance = -1

    print(
        "传感器状态：土壤={}%，温度={}℃，湿度={}%，MQ2={}，"
        "人员={}，火焰={}，降雨={}，雨量={}%，雨型={}，光照={}%，"
        "雷达={}，距离={}cm".format(
            soil_value, temperature, humidity, gas_value,
            intrusion, fire, is_raining, rain_value, rain_type,
            light_value, radar_detected, ultrasonic_distance
        )
    )

    return {
        "soil": soil_value,
        "temperature": temperature,
        "humidity": humidity,
        "gas": gas_value,
        "raining": is_raining,
        "rain_value": rain_value,
        "rain_type": rain_type,
        "intrusion": intrusion,
        "fire": fire,
        "light": light_value,
        "radar": radar_detected,
        "ultrasonic_distance": ultrasonic_distance
    }


def update_bird_detection(data):
    """雷达 + 超声波距离二次确认。
    RCWL检测到移动且距离 <= BIRD_DISTANCE_THRESHOLD 才计为一次有效确认。
    连续确认 BIRD_CONFIRM_COUNT 次后，bird_target_detected=True。
    连续不满足 BIRD_CLEAR_COUNT 次后恢复 False。
    """
    global bird_confirm_count, bird_clear_count, bird_target_detected

    radar_detected = data["radar"]
    distance = data["ultrasonic_distance"]

    valid_target = (
        radar_detected
        and distance >= 0
        and distance <= config.BIRD_DISTANCE_THRESHOLD
    )

    if valid_target:
        bird_confirm_count += 1
        bird_clear_count = 0

        if bird_confirm_count >= config.BIRD_CONFIRM_COUNT:
            if not bird_target_detected:
                print(
                    "【驱鸟目标确认】雷达检测到移动，距离 {:.1f}cm".format(
                        distance
                    )
                )
            bird_target_detected = True
    else:
        bird_confirm_count = 0
        bird_clear_count += 1

        if bird_clear_count >= config.BIRD_CLEAR_COUNT:
            if bird_target_detected:
                print("【驱鸟目标解除】目标已离开或距离无效")
            bird_target_detected = False

    data["bird_target"] = bird_target_detected
    return data


def update_outputs(data):
    global last_intrusion, last_fire, last_led_state
    intrusion = data["intrusion"]
    fire = data["fire"]
    light_value = data["light"]

    if not intrusion:
        if last_led_state:
            led.off("未检测到人员")
            last_led_state = False
    elif light_value < config.LIGHT_LED_ON_THRESHOLD:
        if not last_led_state:
            led.on("检测到人员且光照不足：{:.1f}%".format(light_value))
            last_led_state = True
    elif light_value > config.LIGHT_LED_OFF_THRESHOLD:
        if last_led_state:
            led.off("检测到人员但光照充足：{:.1f}%".format(light_value))
            last_led_state = False

    if fire != last_fire:
        buzzer.set_fire(fire)
        last_fire = fire
    last_intrusion = intrusion


def actuator_test():
    print("")
    print("========== 执行器单独测试开始 ==========")

    print("测试1：LED")
    led.on("执行器测试")
    utime.sleep(2)
    led.off("执行器测试")
    utime.sleep(1)

    print("测试2：蜂鸣器")
    buzzer.off("执行器测试")
    utime.sleep(2)
    buzzer.on("执行器测试")
    utime.sleep(1)

    print("测试3：水泵")
    pump.on("执行器测试")
    utime.sleep(2)
    pump.off("执行器测试")

    print("========== 执行器单独测试结束 ==========")
    print("")


def main():
    global last_sensor_data, last_intrusion, last_fire

    print("===== ESP32 IoT系统启动 =====")

    pump.off("系统启动初始化")
    buzzer.on("系统启动初始化")
    led.off("系统启动初始化")

    if config.DEBUG_PRINT_RULES:
        print_control_rules()

    if config.ACTUATOR_TEST_MODE:
        actuator_test()

    rain.calibrate()

    wlan = wifi.connect()
    if not wlan:
        from net import ap_config
        ap_config.start_config_portal()
        # 配网服务通常在 machine.reset() 后结束；此处作为异常兜底
        print("配网服务已退出，程序停止")
        return

    if not mqtt.connect():
        print("MQTT首次连接失败，主循环将继续尝试重连")

    mqtt.set_pump_command_callback(
        handle_pump_command
    )

    mqtt.set_pump_mode_callback(
        handle_pump_mode
    )
    mqtt.set_soil_threshold_callback(handle_soil_threshold)

    last_read_time = utime.ticks_ms()

    while True:
        if not mqtt.is_connected():
            print("MQTT断开，重连...")
            mqtt.connect()
            utime.sleep(1)
            continue

        mqtt.check()

        if utime.ticks_diff(
            utime.ticks_ms(), last_read_time
        ) >= config.DATA_READ_INTERVAL:

            last_sensor_data = read_all_sensors()

            control_pump(last_sensor_data["soil"])
            update_bird_detection(last_sensor_data)
            update_outputs(last_sensor_data)

            last_read_time = utime.ticks_ms()

            mqtt.upload_sensor_data(
                last_sensor_data["light"],
                last_sensor_data["gas"],
                last_sensor_data["fire"],
                last_sensor_data["intrusion"],
                last_sensor_data["rain_value"],
                last_sensor_data["rain_type"],
                last_sensor_data["raining"],
                last_sensor_data["temperature"],
                last_sensor_data["humidity"],
                last_sensor_data["soil"],
                pump.is_on(),
                pump_mode == "auto",
                last_sensor_data["radar"],
                last_sensor_data["ultrasonic_distance"]
            )

        utime.sleep_ms(config.LOOP_DELAY_MS)


if __name__ == "__main__":
    main()

