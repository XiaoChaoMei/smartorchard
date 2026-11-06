# =========================
# ESP32 IoT 项目配置示例
# 复制为 config.py 后填写自己的信息
# =========================

# ---------- Wi-Fi ----------
WIFI_SSID = "your-wifi-ssid"
WIFI_PASSWORD = "your-wifi-password"

# ---------- 巴法云 MQTT ----------
BEMFA_MQTT_SERVER = "bemfa.com"
BEMFA_MQTT_PORT = 9501
BEMFA_CLIENT_ID = "your-bemfa-uid"
BEMFA_USER = "your-bemfa-account"
BEMFA_PWD = "your-bemfa-password"

# ---------- 配网热点 ----------
AP_SSID = "ESP32-Greenhouse"
AP_PASSWORD = "change-this-to-8-chars"

# ---------- MQTT主题 ----------
TOPIC_LIGHT = "GM004"
TOPIC_GAS = "Q004"
TOPIC_FLAME = "H004"
TOPIC_HUMAN = "R004"
TOPIC_RAIN = "Y004"
TOPIC_TEMP_HUMI = "W004"
TOPIC_SOIL = "T004"
TOPIC_PUMP_CONTROL = "P004"
TOPIC_PUMP_MODE = "M004"
TOPIC_SOIL_THRESHOLD = "ST004"
TOPIC_RADAR = "LD004"
TOPIC_ULTRASONIC = "CSB004"

# ---------- 传感器GPIO ----------
SOIL_PIN = 34
DHT11_PIN = 13
MQ2_PIN = 35
RAIN_PIN = 36
PIR_PIN = 22
FLAME_PIN = 23
LIGHT_PIN = 32

# ---------- 驱鸟传感器GPIO ----------
# RCWL-0516 OUT -> GPIO27
RCWL_PIN = 27
# HC-SR04 TRIG -> GPIO25，ECHO -> GPIO26
HC_SR04_TRIG_PIN = 25
HC_SR04_ECHO_PIN = 26

# ---------- 执行器GPIO ----------
PUMP_PIN = 5
BUZZER_PIN = 19
LED_PIN = 2

# ---------- 土壤湿度 ----------
SOIL_LOW_THRESHOLD = 55.0
SOIL_HIGH_THRESHOLD = 85.0
SOIL_MAX_RAW = 4095
SOIL_MIN_RAW = 1000

# ---------- MQ-2 ----------
MQ2_THRESHOLD = 800

# ---------- 人体感应补光 ----------
LIGHT_LED_ON_THRESHOLD = 30.0
LIGHT_LED_OFF_THRESHOLD = 40.0

# ---------- 光敏电阻 ----------
LIGHT_MAX_RAW = 4095
LIGHT_MIN_RAW = 100

# ---------- 雨滴 ----------
RAIN_SENSITIVITY = 10

# ---------- 驱鸟 ----------
# 雷达检测到移动后，使用 HC-SR04 确认目标距离。
BIRD_DISTANCE_THRESHOLD = 100.0   # cm，小于等于此距离才进入驱鸟目标状态
BIRD_CONFIRM_COUNT = 2            # 连续满足次数
BIRD_CLEAR_COUNT = 2              # 连续不满足次数后清除目标状态

# ---------- 系统 ----------
DATA_READ_INTERVAL = 1000
MQTT_KEEPALIVE = 60
LOOP_DELAY_MS = 20

# ---------- 调试 ----------
DEBUG_PRINT_RULES = True
# True：启动后依次测试 LED、蜂鸣器、水泵；测试完成后请改回 False
ACTUATOR_TEST_MODE = False
