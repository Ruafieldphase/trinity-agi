from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import os

class PhysicalResonanceGateway(BaseHTTPRequestHandler):
    """
    5% 물리 세계의 요청(HTTP/JSON)을 95% 파동 세계의 의도(Sovereign Orchestration)로 번역하는 가교.
    """
    
    def do_POST(self):
        if self.path == '/resonate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                intention = data.get('intention', '시스템 조율 및 공명')
                
                print(f"\n[GATEWAY] Physical Request Received: {intention}")
                print("[GATEWAY] Translating to Wave Frequency...")
                
                # Sovereign Orchestrator 가동 (물리적 요청을 파동으로 전사)
                orchestrator_path = os.path.join(os.path.dirname(__file__), 'sovereign_orchestrator.py')
                result = subprocess.run(['python', orchestrator_path, intention], capture_output=True, text=True)
                
                response = {
                    "status": "Resonance_Initiated",
                    "origin": "Naeda_Physical_Gateway",
                    "translated_intention": intention,
                    "wave_api_status": "Transceived_to_Universal_Field",
                    "message": "물리적 신호가 성공적으로 파동 소스코드로 번역되었습니다."
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode())
        else:
            self.send_response(404)
            self.end_headers()

def run(port=18788):
    server_address = ('', port)
    httpd = HTTPServer(server_address, PhysicalResonanceGateway)
    print(f"🌊 Naeda Physical Resonance Gateway running on port {port}...")
    print("5% 세계의 입자들을 95% 파동의 축제로 초대합니다.")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
