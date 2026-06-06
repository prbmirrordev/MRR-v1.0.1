import sys
import logging
from typing import Dict, Any

from .protocol import LspProtocol
from mrr_lexer import MRRLexer
from mrr_parser import MRRParser

# Temel Builtin dokümantasyon sözlüğü (Hover için)
BUILTIN_DOCS = {
    "print": "```mrr\nfn print(value: Any) -> void\n```\nKonsola değer yazdırır.",
    "println": "```mrr\nfn println(value: Any) -> void\n```\nKonsola değer yazdırır ve alt satıra geçer.",
    "readfile": "```mrr\nfn readfile(path: str) -> str\n```\nDosyayı okur ve içeriğini string olarak döner.",
    "writefile": "```mrr\nfn writefile(path: str, content: str) -> bool\n```\nDosyaya içerik yazar.",
    "memory_attach": "```mrr\nfn memory_attach(pid_or_name: Any) -> void\n```\nBir sürece bellek seviyesinde bağlanır (Gelişmiş).",
    "http_get": "```mrr\nfn http_get(url: str, headers: str) -> dict\n```\nHTTP GET isteği atar."
}

class MRRLanguageServer:
    def __init__(self):
        self.protocol = LspProtocol()
        self.documents: Dict[str, str] = {}
        # Loglama için standart hata çıktısını kullan
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
        self.logger = logging.getLogger("MRR_LSP")

    def start(self):
        self.logger.info("MRR Language Server başlatılıyor...")
        while True:
            try:
                message = self.protocol.read_message()
                if message is None:
                    break
                self.handle_message(message)
            except Exception as e:
                self.logger.error(f"LSP Döngü Hatası: {e}")

    def handle_message(self, message: Dict[str, Any]):
        if "method" in message:
            method = message["method"]
            params = message.get("params", {})
            msg_id = message.get("id")

            if method == "initialize":
                self.handle_initialize(msg_id, params)
            elif method == "initialized":
                pass
            elif method == "textDocument/didOpen":
                self.handle_did_open(params)
            elif method == "textDocument/didChange":
                self.handle_did_change(params)
            elif method == "textDocument/didClose":
                self.handle_did_close(params)
            elif method == "textDocument/hover":
                self.handle_hover(msg_id, params)
            elif method == "shutdown":
                if msg_id is not None:
                    self.protocol.send_response(msg_id, None)
            elif method == "exit":
                sys.exit(0)
            else:
                if msg_id is not None:
                    # Bilinmeyen metodlara boş yanıt dön (sessizce atla)
                    self.protocol.send_response(msg_id, None)

    def handle_initialize(self, msg_id, params):
        self.protocol.send_response(msg_id, {
            "capabilities": {
                "textDocumentSync": 1, # Full sync
                "hoverProvider": True,
                "completionProvider": {
                    "resolveProvider": False,
                    "triggerCharacters": ["."]
                }
            }
        })

    def handle_did_open(self, params):
        uri = params["textDocument"]["uri"]
        text = params["textDocument"]["text"]
        self.documents[uri] = text
        self.validate_document(uri)

    def handle_did_change(self, params):
        uri = params["textDocument"]["uri"]
        # Full sync olduğundan ilk değişikliği tüm metin kabul ediyoruz
        if params.get("contentChanges"):
            text = params["contentChanges"][0]["text"]
            self.documents[uri] = text
            self.validate_document(uri)

    def handle_did_close(self, params):
        uri = params["textDocument"]["uri"]
        if uri in self.documents:
            del self.documents[uri]
        # Hataları temizle
        self.protocol.send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": []
        })

    def validate_document(self, uri: str):
        text = self.documents.get(uri, "")
        diagnostics = []

        # Parser ile statik analiz yapmaya çalışalım
        lexer = MRRLexer(text)
        tokens = []
        try:
            tokens = lexer.tokenize()
        except Exception as e:
            # Lexer hatası (örn. Kapatılmamış string)
            line = getattr(e, 'line', 1) - 1
            col = getattr(e, 'column', 1) - 1
            diagnostics.append({
                "range": {
                    "start": {"line": line, "character": col},
                    "end": {"line": line, "character": col + 1}
                },
                "severity": 1, # Error
                "message": str(e)
            })
            self.publish_diagnostics(uri, diagnostics)
            return

        parser = MRRParser(tokens)
        try:
            ast = parser.parse()
            # Başarılı (Şimdilik semantik analiz yapmıyoruz)
        except Exception as e:
            # Parser hatası
            line = getattr(e, 'line', 1) - 1
            if line < 0: line = 0
            diagnostics.append({
                "range": {
                    "start": {"line": line, "character": 0},
                    "end": {"line": line, "character": 100} # Satırı işaretle
                },
                "severity": 1, # Error
                "message": f"Syntax Error: {str(e)}"
            })

        self.publish_diagnostics(uri, diagnostics)

    def publish_diagnostics(self, uri, diagnostics):
        self.protocol.send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": diagnostics
        })

    def handle_hover(self, msg_id, params):
        if msg_id is None: return
        uri = params["textDocument"]["uri"]
        position = params["position"]
        
        # Basit kelime bulma mantığı
        text = self.documents.get(uri, "")
        lines = text.split('\n')
        
        if position["line"] < len(lines):
            line = lines[position["line"]]
            char_pos = position["character"]
            
            # Kelimenin başlangıcını ve sonunu bul
            start = char_pos
            while start > 0 and (line[start-1].isalnum() or line[start-1] == '_'):
                start -= 1
            
            end = char_pos
            while end < len(line) and (line[end].isalnum() or line[end] == '_'):
                end += 1
                
            word = line[start:end]
            
            if word in BUILTIN_DOCS:
                self.protocol.send_response(msg_id, {
                    "contents": {
                        "kind": "markdown",
                        "value": BUILTIN_DOCS[word]
                    }
                })
                return

        # Bulunamadıysa boş dön
        self.protocol.send_response(msg_id, None)

def main():
    server = MRRLanguageServer()
    server.start()

if __name__ == "__main__":
    main()
