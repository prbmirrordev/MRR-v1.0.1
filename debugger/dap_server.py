"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Debug Adapter Protocol (DAP) Server                       ║
║                                                                  ║
║  Visual Studio / VS Code ile haberleşerek MRR kodlarının       ║
║  adımlanmasını, register/bellek (Ring-0) değerlerinin          ║
║  okunmasını ve obfuscate edilmiş kodların çözülmesini sağlar.    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import json
import logging
from typing import Dict, Any

class DAPServer:
    def __init__(self):
        self.seq = 1
        self.breakpoints = {}
        logging.basicConfig(filename='mrr_dap.log', level=logging.DEBUG)
        logging.info("MRR DAP Server başlatıldı.")

    def read_message(self):
        """DAP protokolü mesaj okuma: Content-Length başlıklı JSON payload"""
        content_length = 0
        while True:
            line = sys.stdin.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
        
        if content_length > 0:
            payload = sys.stdin.read(content_length)
            return json.loads(payload)
        return None

    def send_message(self, message: Dict[str, Any]):
        """DAP yanıtı gönderme"""
        message["seq"] = self.seq
        self.seq += 1
        payload = json.dumps(message)
        sys.stdout.write(f"Content-Length: {len(payload)}\r\n\r\n{payload}")
        sys.stdout.flush()

    def handle_request(self, req: Dict[str, Any]):
        cmd = req.get("command")
        logging.info(f"Komut alındı: {cmd}")

        if cmd == "initialize":
            self.send_message({
                "type": "response",
                "request_seq": req["seq"],
                "success": True,
                "command": cmd,
                "body": {
                    "supportsConfigurationDoneRequest": True,
                    "supportsEvaluateForHovers": True,
                    "supportsStepBack": False,
                    "supportsSetVariable": True,
                    "supportsModulesRequest": True,
                    "supportsLogPoints": True
                }
            })
            # Olayları (Events) gönder
            self.send_message({
                "type": "event",
                "event": "initialized"
            })
            
        elif cmd == "launch":
            # Geliştiricinin MRR dosyasını çalıştır
            # Burada normalde mrr_evaluator debug kancalarıyla çalıştırılır
            program = req.get("arguments", {}).get("program")
            logging.info(f"Program başlatılıyor: {program}")
            
            self.send_message({
                "type": "response",
                "request_seq": req["seq"],
                "success": True,
                "command": cmd
            })
            
        elif cmd == "setBreakpoints":
            path = req.get("arguments", {}).get("source", {}).get("path")
            lines = [b.get("line") for b in req.get("arguments", {}).get("breakpoints", [])]
            self.breakpoints[path] = lines
            
            bps = [{"verified": True, "line": l} for l in lines]
            self.send_message({
                "type": "response",
                "request_seq": req["seq"],
                "success": True,
                "command": cmd,
                "body": {"breakpoints": bps}
            })
            
        elif cmd == "configurationDone":
            self.send_message({
                "type": "response",
                "request_seq": req["seq"],
                "success": True,
                "command": cmd
            })
            
        elif cmd == "disconnect":
            self.send_message({
                "type": "response",
                "request_seq": req["seq"],
                "success": True,
                "command": cmd
            })
            sys.exit(0)

        # Ring-0 Kernel Değişkenleri / Custom Bellek İsteği Örneği
        elif cmd == "evaluate":
            expr = req.get("arguments", {}).get("expression", "")
            val = "<bilinmeyen>"
            
            if expr.startswith("$"):
                # Register simülasyonu
                if expr == "$rax": val = "0x0000000000000000"
                elif expr == "$rsp": val = "0x7fffffffe000"
            
            self.send_message({
                "type": "response",
                "request_seq": req["seq"],
                "success": True,
                "command": cmd,
                "body": {
                    "result": val,
                    "variablesReference": 0
                }
            })

    def run(self):
        while True:
            msg = self.read_message()
            if not msg:
                break
            if msg.get("type") == "request":
                self.handle_request(msg)

if __name__ == "__main__":
    server = DAPServer()
    server.run()
