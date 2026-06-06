import sys
import json
import logging

class LspProtocol:
    """Handles JSON-RPC parsing for Language Server Protocol."""
    
    def __init__(self, stdin=sys.stdin.buffer, stdout=sys.stdout.buffer):
        self.stdin = stdin
        self.stdout = stdout

    def read_message(self):
        """Reads the next message from stdin."""
        content_length = 0
        while True:
            line = self.stdin.readline()
            if not line:
                return None
            line = line.decode('utf-8').strip()
            if not line:
                break
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
        
        if content_length == 0:
            return None
            
        content = self.stdin.read(content_length)
        if not content:
            return None
            
        try:
            return json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            return None

    def send_message(self, message):
        """Sends a JSON-RPC message to stdout."""
        if 'jsonrpc' not in message:
            message['jsonrpc'] = '2.0'
            
        content = json.dumps(message, ensure_ascii=False).encode('utf-8')
        header = f"Content-Length: {len(content)}\r\n\r\n".encode('utf-8')
        
        self.stdout.write(header)
        self.stdout.write(content)
        self.stdout.flush()

    def send_notification(self, method, params):
        self.send_message({
            "method": method,
            "params": params
        })

    def send_response(self, id, result):
        self.send_message({
            "id": id,
            "result": result
        })

    def send_error(self, id, code, message):
        self.send_message({
            "id": id,
            "error": {
                "code": code,
                "message": message
            }
        })
