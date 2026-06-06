"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR GUI Engine — Modern Web/Qt Tabanlı Arayüz Motoru          ║
║                                                                  ║
║  Bu modül MRR dili içerisindeki `add.code "gui"` çağrısı ile    ║
║  tetiklenir. PyQt6 ve QtWebEngine (Chromium tabanlı)             ║
║  kullanarak MRR kodlarının içine gömülen HTML/CSS/JS             ║
║  kodlarını doğrudan yerel bir pencerede görüntüler.              ║
║                                                                  ║
║  Özellikler:                                                    ║
║    - Frontend (JS) <-> Backend (MRR) arası çift yönlü RPC       ║
║    - Çapraz platform masaüstü penceresi (Windows, Linux, macOS)  ║
║    - MRR değişkenlerine Javascript içinden anında erişim        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import json
import threading
from typing import Dict, Any, Callable

# PyQt6 bağımlılıkları (Loader tarafından otomatik kurulur)
try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl
except ImportError:
    print("[MRR GUI] ⚠ PyQt6 ve PyQt6-WebEngine kurulu değil.")
    print("[MRR GUI] ⚠ Loader üzerinden veya 'pip install PyQt6 PyQt6-WebEngine' komutuyla kurun.")
    # GUI özelliği olmadan çalışmaya devam edebilmesi için sınıfları mock'layalım
    QObject = object
    def pyqtSlot(*args, **kwargs): return lambda f: f
    def pyqtSignal(*args, **kwargs): pass


class MRRWebChannelHandler(QObject):
    """
    Frontend (JS) ile Backend (MRR) arasında haberleşmeyi sağlayan
    QtWebChannel nesnesi.
    JS tarafında `qwebchannel.js` ile entegre olur.
    """
    # JS'den Backend'e gönderilecek mesaj sinyali
    message_received = pyqtSignal(str)

    def __init__(self, mrr_callbacks: Dict[str, Callable]):
        super().__init__()
        self.callbacks = mrr_callbacks

    @pyqtSlot(str, result=str)
    def call_mrr_function(self, payload: str) -> str:
        """JS tarafından çağrıldığında çalışır."""
        try:
            data = json.loads(payload)
            func_name = data.get("function")
            args = data.get("args", [])
            
            if func_name in self.callbacks:
                # MRR fonksiyonunu çağır
                result = self.callbacks[func_name](args)
                return json.dumps({"status": "success", "result": result})
            else:
                return json.dumps({"status": "error", "error": f"Fonksiyon bulunamadı: {func_name}"})
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})


class MRRGUIWindow(QMainWindow):
    """
    Ana GUI Penceresi. 
    İçerisinde Chromium tabanlı bir WebView barındırır.
    """
    def __init__(self, html_content: str, mrr_callbacks: Dict[str, Callable], title: str = "MRR Uygulaması"):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1024, 768)

        # Web view oluştur
        self.browser = QWebEngineView()
        
        # Web Channel Kurulumu
        self.channel = QWebChannel()
        self.handler = MRRWebChannelHandler(mrr_callbacks)
        self.channel.registerObject("mrrBackend", self.handler)
        self.browser.page().setWebChannel(self.channel)

        # QtWebChannel JS kütüphanesini HTML'e otomatik enjekte et
        html_with_bridge = self._inject_webchannel_js(html_content)
        self.browser.setHtml(html_with_bridge)

        self.setCentralWidget(self.browser)

    def _inject_webchannel_js(self, html: str) -> str:
        """
        Geliştiricinin HTML'i içerisine QWebChannel script'ini ve 
        MRR bridge API'sini otomatik gömer.
        """
        script = """
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script>
            // MRR Bridge API'si
            var MRR = {
                backend: null,
                init: function(callback) {
                    new QWebChannel(qt.webChannelTransport, function(channel) {
                        MRR.backend = channel.objects.mrrBackend;
                        if(callback) callback();
                    });
                },
                call: function(func_name, args, callback) {
                    if(!MRR.backend) {
                        console.error("MRR Backend henüz hazır değil!");
                        return;
                    }
                    var payload = JSON.stringify({function: func_name, args: args});
                    MRR.backend.call_mrr_function(payload, function(response) {
                        var parsed = JSON.parse(response);
                        if(callback) callback(parsed);
                    });
                }
            };
            
            // Otomatik başlat
            window.onload = function() {
                MRR.init();
            };
        </script>
        """
        # Head etiketinden hemen sonra script'i enjekte et
        if "<head>" in html:
            return html.replace("<head>", f"<head>\n{script}")
        elif "<html>" in html:
            return html.replace("<html>", f"<html>\n{script}")
        else:
            return script + html


class GUIEngine:
    """
    MRR Yorumlayıcısının `add.code "gui"` modülü ile 
    etkileşime girdiği ana köprü sınıfı.
    """
    def __init__(self):
        self.app = None
        self.callbacks = {}

    def register_function(self, name: str, func: Callable):
        """MRR'deki bir fonksiyonu JS'e (Frontend) açar."""
        self.callbacks[name] = func

    def render(self, html_content: str, title: str = "MRR Uygulaması"):
        """Verilen HTML'i Chromium tabanlı yeni bir masaüstü penceresinde açar."""
        # Qt nesneleri ana thread'de başlatılmalıdır
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        self.window = MRRGUIWindow(html_content, self.callbacks, title)
        self.window.show()
        
        # Uygulama döngüsünü başlat (bu çağrı bloke edicidir)
        self.app.exec()

def create_gui_module():
    """
    FFI üzerinden yüklenecek olan modül nesnesini döndürür.
    Bu modül, MRR evaluator tarafında `gui.render` şeklinde kullanılacak.
    """
    engine = GUIEngine()
    
    # MRR arayüzünü (API) oluşturuyoruz
    class GUIMrrInterface:
        def render(self, *args):
            # args[0] is self, args[1] is the argument list passed from MRR CallExpr
            mrr_args = args[0] if len(args) == 1 else args[1]
            html = str(mrr_args[0])
            title = str(mrr_args[1]) if len(mrr_args) > 1 else "MRR Uygulaması"
            engine.render(html, title)
            return None
            
        def register(self, *args):
            mrr_args = args[0] if len(args) == 1 else args[1]
            name = str(mrr_args[0])
            func = mrr_args[1] # Bu bir MRRFunction veya Python callable'ı olacak
            
            # Fonksiyon çağrıldığında parametreleri tek argüman listesi olarak ileten bir wrapper
            def wrapper(js_args):
                if callable(func):
                    return func(*js_args)
                else:
                    return None
            
            engine.register_function(name, wrapper)
            return True

    return GUIMrrInterface()
