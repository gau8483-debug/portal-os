import threading
import http.server
import socketserver
import socket
import time
from dnslib import RR, QTYPE, A, DNSRecord
from dnslib.server import DNSServer

# ==========================================
# 1. TỰ ĐỘNG LẤY IP MÁY TÍNH
# ==========================================
def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

MY_IP = get_my_ip()
TARGET_URL = "https://webmenuos.netlify.app/"

# ==========================================
# 2. WEB SERVER (SỬA LỖI ĐIỀU HƯỚNG 302)
# ==========================================
class PortalHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"\n[Web] >>> iPhone dang truy cap: {self.path}")
        
        # BƯỚC QUAN TRỌNG: Gửi mã 302 để ép iPhone nhảy trang ngay lập tức
        # Thay vì gửi mã 200 (OK) và chờ HTML load
        self.send_response(302) 
        self.send_header("Location", TARGET_URL)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        
        print(f"[Web] <<< Da GUI LENH EP CHUYEN HUONG (302) den {TARGET_URL}")

def run_web_server():
    socketserver.TCPServer.allow_reuse_address = True
    try:
        # Lắng nghe trên cổng 80 (Cổng mặc định của HTTP)
        with socketserver.TCPServer(("0.0.0.0", 80), PortalHandler) as httpd:
            print(f"[*] Web Server dang chay tai: {MY_IP}:80")
            httpd.serve_forever()
    except Exception as e:
        print(f"!!! LOI WEB SERVER: {e} (Chay bang quyen Admin/Sudo)")

# ==========================================
# 3. DNS SERVER (ĐÁNH BẪY DOMAIN APPLE)
# ==========================================
class BypassResolver:
    def resolve(self, request, handler):
        reply = request.reply()
        qname = str(request.q.qname).lower().rstrip('.')
        
        # Danh sách domain iPhone 5s hay gọi để kiểm tra mạng
        apple_list = [
            "apple.com", "icloud.com", "captive.apple.com", 
            "www.ibook.info", "www.itools.info", "www.appleiphonecell.com",
            "thinkdifferent.us", "itunes.com", "mesu.apple.com", "airport.us"
        ]
        
        # Nếu domain nằm trong danh sách Apple hoặc domain lạ, trỏ về IP máy tính
        if any(x in qname for x in apple_list):
            print(f"[DNS] Chan Apple: {qname} -> {MY_IP}")
            reply.add_answer(RR(qname + ".", QTYPE.A, rdata=A(MY_IP)))
        else:
            # Cho phép load các domain khác (như netlify.app)
            try:
                real_ip = socket.gethostbyname(qname)
                reply.add_answer(RR(qname + ".", QTYPE.A, rdata=A(real_ip)))
            except:
                reply.add_answer(RR(qname + ".", QTYPE.A, rdata=A(MY_IP)))
        return reply

if __name__ == '__main__':
    print("==========================================")
    print("    KHOI DONG HE THONG BYPASS 5S")
    print(f"    IP CUA BAN: {MY_IP}")
    print("==========================================")
    
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    resolver = BypassResolver()
    try:
        dns_server = DNSServer(resolver, port=53, address="0.0.0.0")
        print(f"[*] DNS Server dang chay tai: {MY_IP}:53")
        dns_server.start()
    except Exception as e:
        print(f"!!! LOI DNS: {e} (Chay bang quyen Admin/Sudo)")