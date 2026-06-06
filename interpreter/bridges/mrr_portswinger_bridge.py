"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Portswinger Bridge — Python ↔ C++ Köprüsü                  ║
║                                                                  ║
║  portswinger.dll/so'ya ctypes ile bağlanır.                      ║
║  Evaluator'a builtin HTTP ve Socket fonksiyonları olarak eklenir.║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import ctypes
import ctypes.util
import os
import sys
import socket
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from pathlib import Path


# ═══════════════════════════════════════════════════════════
# C Struct Tanımları (ctypes)
# ═══════════════════════════════════════════════════════════

class MRR_HttpResponse_C(ctypes.Structure):
    _fields_ = [
        ("status_code", ctypes.c_int),
        ("body", ctypes.c_char_p),
        ("body_size", ctypes.c_size_t),
        ("headers", ctypes.c_char_p),
        ("error_message", ctypes.c_char_p),
    ]


# ═══════════════════════════════════════════════════════════
# DLL/SO Yükleyici
# ═══════════════════════════════════════════════════════════

def _load_native_library() -> Optional[ctypes.CDLL]:
    """portswinger native kütüphanesini yükle."""
    lib_dir = Path(__file__).parent.parent.parent / "library"

    if sys.platform == "win32":
        lib_name = "portswinger.dll"
    else:
        lib_name = "libportswinger.so"

    lib_path = lib_dir / lib_name

    if lib_path.exists():
        try:
            return ctypes.CDLL(str(lib_path))
        except OSError as e:
            print(f"[MRR-NET] Native kütüphane yüklenemedi: {e}")
            return None

    # Sistem yolunda ara
    found = ctypes.util.find_library("portswinger")
    if found:
        return ctypes.CDLL(found)

    return None


# ═══════════════════════════════════════════════════════════
# Python Fallback (Sistem kütüphaneleri)
# ═══════════════════════════════════════════════════════════

class PortswingerFallback:
    """
    Native C kütüphanesi yüklenemezse veya (şimdilik) eksik özellikleri
    tamamlamak için Python'ın yerleşik soket/http modüllerini kullanan yedek.
    """
    def __init__(self):
        self.sockets = {}
        self.next_fd = 1000

    def socket_create(self, family: int, type: int, proto: int) -> int:
        try:
            s = socket.socket(family, type, proto)
            fd = self.next_fd
            self.next_fd += 1
            self.sockets[fd] = s
            return fd
        except Exception as e:
            print(f"Fallback socket error: {e}")
            return -1

    def socket_connect(self, fd: int, host: str, port: int) -> int:
        if fd not in self.sockets: return -1
        try:
            self.sockets[fd].connect((host, port))
            return 0
        except Exception:
            return -1

    def socket_send(self, fd: int, data: bytes) -> int:
        if fd not in self.sockets: return -1
        try:
            return self.sockets[fd].send(data)
        except Exception:
            return -1

    def socket_recv(self, fd: int, size: int) -> bytes:
        if fd not in self.sockets: return b""
        try:
            return self.sockets[fd].recv(size)
        except Exception:
            return b""

    def socket_close(self, fd: int):
        if fd in self.sockets:
            try:
                self.sockets[fd].close()
            except Exception:
                pass
            del self.sockets[fd]

    def http_request(self, method: str, url: str, body: Optional[str] = None, headers: Optional[str] = None) -> Dict[str, Any]:
        req_headers = {}
        if headers:
            for line in headers.strip().split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    req_headers[k.strip()] = v.strip()
        
        req_data = body.encode('utf-8') if body else None
        
        try:
            req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method.upper())
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_body = resp.read().decode('utf-8', errors='replace')
                return {
                    "status": resp.status,
                    "body": resp_body,
                    "error": None
                }
        except urllib.error.HTTPError as e:
            return {
                "status": e.code,
                "body": e.read().decode('utf-8', errors='replace'),
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": 0,
                "body": "",
                "error": str(e)
            }


# ═══════════════════════════════════════════════════════════
# Birleşik API
# ═══════════════════════════════════════════════════════════

class Portswinger:
    def __init__(self):
        self._native = _load_native_library()
        self._fallback = PortswingerFallback()
        
        if self._native:
            self._setup_native()
            self._native.mrr_net_init()

    def _setup_native(self):
        lib = self._native
        
        lib.mrr_socket_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.mrr_socket_create.restype = ctypes.c_int
        
        lib.mrr_socket_connect.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        lib.mrr_socket_connect.restype = ctypes.c_int
        
        lib.mrr_socket_send.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
        lib.mrr_socket_send.restype = ctypes.c_int
        
        lib.mrr_socket_recv.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
        lib.mrr_socket_recv.restype = ctypes.c_int
        
        lib.mrr_socket_close.argtypes = [ctypes.c_int]
        lib.mrr_socket_close.restype = None
        
        lib.mrr_http_request.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        lib.mrr_http_request.restype = ctypes.POINTER(MRR_HttpResponse_C)
        
        lib.mrr_http_free_response.argtypes = [ctypes.POINTER(MRR_HttpResponse_C)]
        lib.mrr_http_free_response.restype = None

    def socket_create(self, family: int, type: int, proto: int) -> int:
        if self._native:
            return self._native.mrr_socket_create(family, type, proto)
        return self._fallback.socket_create(family, type, proto)

    def socket_connect(self, fd: int, host: str, port: int) -> int:
        if self._native:
            return self._native.mrr_socket_connect(fd, host.encode(), port)
        return self._fallback.socket_connect(fd, host, port)

    def socket_send(self, fd: int, data: bytes) -> int:
        if self._native:
            return self._native.mrr_socket_send(fd, data, len(data))
        return self._fallback.socket_send(fd, data)

    def socket_recv(self, fd: int, size: int) -> bytes:
        if self._native:
            buf = ctypes.create_string_buffer(size)
            bytes_read = self._native.mrr_socket_recv(fd, buf, size)
            if bytes_read > 0:
                return buf.raw[:bytes_read]
            return b""
        return self._fallback.socket_recv(fd, size)

    def socket_close(self, fd: int):
        if self._native:
            self._native.mrr_socket_close(fd)
        else:
            self._fallback.socket_close(fd)

    def http_request(self, method: str, url: str, body: str = "", headers: str = "") -> Dict[str, Any]:
        # C++ HTTPS desteği tam bitmediğinden, https ise fallback'e git
        if url.startswith("https://") or not self._native:
            return self._fallback.http_request(method, url, body, headers)
            
        m = method.encode()
        u = url.encode()
        b = body.encode() if body else None
        h = headers.encode() if headers else None
        
        resp_ptr = self._native.mrr_http_request(m, u, b, h)
        if not resp_ptr:
            return {"status": 0, "body": "", "error": "Native allocation failed"}
            
        resp = resp_ptr.contents
        result = {
            "status": resp.status_code,
            "body": resp.body.decode('utf-8', errors='replace') if resp.body else "",
            "error": resp.error_message.decode('utf-8', errors='replace') if resp.error_message else None
        }
        
        self._native.mrr_http_free_response(resp_ptr)
        return result

    def cleanup(self):
        if self._native:
            self._native.mrr_net_cleanup()
