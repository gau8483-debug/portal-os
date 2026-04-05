import os
import threading
import time
from flask import Flask, redirect
from dnslib import RR, QTYPE, A, DNSRecord
from dnslib.server import DNSServer

# ==========================================
# 1. CẤU HÌNH TRANG ĐÍCH
# ==========================================
TARGET_URL = "https://webmenuos.netlify.app/"

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    print(f"[Web] >>> iPhone dang truy cap: {path}")
    # Sử dụng mã 302 để ép iPhone mở Portal ngay lập tức
    return redirect(TARGET_URL, code=302)

# ==========================================
# 2. DNS RESOLVER (ĐÁNH BẪY DOMAIN)
# ==========================================
class BypassResolver:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.apple_list = [
            "apple.com", "icloud.com", "captive.apple.com", 
            "www.ibook.info", "www.itools.info", "www.appleiphonecell.com",
            "thinkdifferent.us", "itunes.com", "mesu.apple.com", "airport.us"
        ]

    def resolve(self, request, handler):
        reply = request.reply()
        qname = str(request.q.qname).lower().rstrip('.')
        
        # Nếu là domain của Apple, trỏ về IP của Server này
        if any(x in qname for x in self.apple_list):
            print(f"[DNS] Chan Apple: {qname} -> {self.server_ip}")
            reply.add_answer(RR(qname + ".", QTYPE.A, rdata=A(self.server_ip)))
        else:
            # Các tên miền khác (như netlify) thì trả về IP thật để web load được
            import socket
            try:
                real_ip = socket.gethostbyname(qname)
                reply.add_answer(RR(qname + ".", QTYPE.A, rdata=A(real_ip)))
            except:
                reply.add_answer(RR(qname + ".", QTYPE.A, rdata=A(self.server_ip)))
        return reply

def run_dns_server():
    # Lưu ý: Trên Cloud (Koyeb/Render), cổng 53 thường bị chặn.
    # Script này cố gắng chạy, nếu lỗi sẽ thông báo để bạn dùng NextDNS.
    try:
        resolver = BypassResolver("0.0.0.0") 
        dns_server = DNSServer(resolver, port=53, address="0.0.0.0")
        print("[*] DNS Server dang thu khoi dong tai cong 53...")
        dns_server.start()
    except Exception as e:
        print(f"!!! CANH BAO: Khong the mo cong 53 (DNS).")
        print("Hay dung NextDNS de tro apple.com ve link Koyeb cua ban.")

# ==========================================
# 3. KÍCH HOẠT HỆ THỐNG
# ==========================================
if __name__ == '__main__':
    # Koyeb/Render cung cấp cổng qua biến môi trường PORT
    port = int(os.environ.get("PORT", 8000))
    
    print("==========================================")
    print("    HE THONG iDNS PORTAL OS (CLOUD)")
    print(f"    WEB PORT: {port}")
    print("==========================================")

    # Chạy DNS ở luồng riêng
    dns_thread = threading.Thread(target=run_dns_server, daemon=True)
    dns_thread.start()

    # Chạy Web Server Flask (Chính)
    app.run(host='0.0.0.0', port=port)