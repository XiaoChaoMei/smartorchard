# ESP32 AP热点 + HTTP网页配网
# 手机连接热点后，浏览器访问 http://192.168.10.1
import network
import socket
import utime
import ujson
import machine
import config

AP_SSID = config.AP_SSID
AP_PASSWORD = config.AP_PASSWORD
AP_IP = "192.168.10.1"
CONFIG_FILE = "net/wifi_config.json"


def _html_page(message=""):
    msg = ""
    if message:
        msg = '<p style="color:#176b3a;">{}</p>'.format(message)
    html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>智慧果园 Wi-Fi 配网</title>
<style>
body{font-family:Arial,sans-serif;background:#f2f6f3;margin:0;padding:22px}
main{max-width:440px;margin:30px auto;background:white;padding:24px;border-radius:16px;box-shadow:0 4px 18px #0001}
h2{color:#246b45}label{display:block;margin-top:16px}
input{box-sizing:border-box;width:100%;padding:12px;margin-top:7px;border:1px solid #bbb;border-radius:8px;font-size:16px}
button{width:100%;padding:13px;margin-top:22px;background:#247a4b;color:white;border:0;border-radius:8px;font-size:17px}
small{color:#666;line-height:1.6}
</style></head>
<body><main>
<h2>智慧果园 Wi-Fi 配置</h2>
<p>输入 ESP32 需要连接的路由器 Wi-Fi 信息。</p>
{msg}
<form method="POST" action="/save">
<label>Wi-Fi 名称（SSID）</label>
<input name="ssid" maxlength="64" required placeholder="输入 Wi-Fi 名称">
<label>Wi-Fi 密码</label>
<input name="password" type="password" maxlength="128" placeholder="输入 Wi-Fi 密码">
<button type="submit">保存并重启连接</button>
</form>
<p><small>保存后 ESP32 将重启并尝试连接该 Wi-Fi。若连接失败，将再次开启此配网热点。</small></p>
</main></body></html>"""
    return html.replace("{msg}", msg)


def _decode_form(data):
    # 简单解析 application/x-www-form-urlencoded
    result = {}
    for item in data.split("&"):
        if "=" in item:
            key, value = item.split("=", 1)
            value = value.replace("+", " ")
            # 解码 %xx
            out = ""
            i = 0
            while i < len(value):
                if value[i] == "%" and i + 2 < len(value):
                    try:
                        out += chr(int(value[i + 1:i + 3], 16))
                        i += 3
                        continue
                    except Exception:
                        pass
                out += value[i]
                i += 1
            result[out if False else key] = out if False else value
    # 进行一次百分号解码并转换UTF-8字节
    decoded = {}
    for key, value in result.items():
        raw = bytearray()
        i = 0
        while i < len(value):
            if value[i] == "%" and i + 2 < len(value):
                try:
                    raw.append(int(value[i+1:i+3], 16)); i += 3; continue
                except Exception:
                    pass
            raw.extend(value[i].encode("utf-8"))
            i += 1
        try:
            decoded[key] = raw.decode("utf-8")
        except Exception:
            decoded[key] = value
    return decoded


def _send(conn, status, body, content_type="text/html; charset=utf-8"):
    payload = body.encode("utf-8")
    header = "HTTP/1.1 {}\r\nContent-Type: {}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n".format(
        status, content_type, len(payload))
    conn.send(header.encode("utf-8"))
    conn.send(payload)


def _dns_server():
    """简易DNS劫持：将收到的域名查询统一解析到本机门户地址。"""
    try:
        import _thread
        dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        dns.bind(("0.0.0.0", 53))
        print("DNS门户服务已启动（UDP 53）")
        while True:
            try:
                packet, client = dns.recvfrom(512)
                if len(packet) < 17:
                    continue
                # 取第一个问题段；不解析域名内容，统一返回门户IPv4地址
                pos = 12
                while pos < len(packet) and packet[pos] != 0:
                    size = packet[pos]
                    if size & 0xC0 == 0xC0:
                        break
                    pos += size + 1
                if pos + 5 > len(packet):
                    continue
                question_end = pos + 5
                question = packet[12:question_end]
                # 标准响应 + 权威回答；单问题、单A记录
                header = packet[:2] + b"\x81\x80" + packet[4:6] + b"\x00\x01\x00\x00\x00\x00"
                answer = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\xc0\xa8\x0a\x01"
                dns.sendto(header + question + answer, client)
            except Exception as e:
                print("DNS处理异常：", e)
    except Exception as e:
        print("DNS服务启动失败：", e)


def start_dns_thread():
    try:
        import _thread
        _thread.start_new_thread(_dns_server, ())
        utime.sleep_ms(200)
    except Exception as e:
        print("无法启动DNS线程：", e)


def start_config_portal():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    try:
        ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)
    except Exception:
        # 兼容部分旧版MicroPython
        ap.config(essid=AP_SSID, password=AP_PASSWORD)

    # 等待AP启动
    for _ in range(10):
        if ap.active():
            break
        utime.sleep_ms(200)

    try:
        ap.ifconfig((AP_IP, "255.255.255.0", AP_IP, AP_IP))
    except Exception as e:
        print("设置热点IP失败，使用默认配置：", e)

    print("")
    print("========== Wi-Fi 配网模式 ==========")
    print("热点名称：{}".format(AP_SSID))
    print("热点密码：{}".format(AP_PASSWORD))
    print("手机连接热点后访问：http://{}".format(AP_IP))
    start_dns_thread()
    print("DNS已尝试启动；手机若未自动弹窗，请访问 http://192.168.10.1")
    print("等待手机提交 Wi-Fi 配置...")
    print("====================================")

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(2)
    server.settimeout(1)

    while True:
        try:
            conn, remote = server.accept()
        except OSError:
            continue

        try:
            conn.settimeout(3)
            request = conn.recv(2048)
            if not request:
                conn.close()
                continue

            try:
                request_text = request.decode("utf-8")
            except Exception:
                request_text = str(request)

            first_line = request_text.split("\r\n")[0]
            print("配网页面请求：{}".format(first_line))

            if first_line.startswith("POST /save"):
                body = request_text.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in request_text else ""
                # 若请求体超过首包，尝试按Content-Length补收
                content_length = 0
                for line in request_text.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        try:
                            content_length = int(line.split(":", 1)[1].strip())
                        except Exception:
                            pass
                while len(body.encode("utf-8")) < content_length:
                    chunk = conn.recv(512)
                    if not chunk:
                        break
                    body += chunk.decode("utf-8")

                form = _decode_form(body)
                ssid = form.get("ssid", "").strip()
                password = form.get("password", "")
                if not ssid:
                    _send(conn, "400 Bad Request", _html_page("Wi-Fi 名称不能为空。"))
                else:
                    try:
                        with open(CONFIG_FILE, "w") as f:
                            f.write(ujson.dumps({"ssid": ssid, "password": password}))
                        _send(conn, "200 OK", """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
                        <meta name="viewport" content="width=device-width,initial-scale=1">
                        <body style="font-family:Arial;padding:30px"><h2>配置已保存</h2>
                        <p>ESP32 即将重启并尝试连接 Wi-Fi，请稍候。</p></body></html>""")
                        print("Wi-Fi配置已保存，准备重启（密码不输出）")
                        utime.sleep(2)
                        conn.close()
                        server.close()
                        machine.reset()
                    except Exception as e:
                        print("保存Wi-Fi配置失败：", e)
                        _send(conn, "500 Internal Server Error", _html_page("保存失败，请重试。"))
            else:
                _send(conn, "200 OK", _html_page())
        except Exception as e:
            print("配网HTTP处理异常：", e)
        finally:
            try:
                conn.close()
            except Exception:
                pass

