/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Portswinger Network Library — L7 / Standard Sockets        ║
 * ║                                                                  ║
 * ║  HTTP(S), Async I/O, ve standart TCP/UDP soket işlemleri.       ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

#ifndef MRR_PORTSWINGER_H
#define MRR_PORTSWINGER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════════════════════════════════════
 * Hata Kodları
 * ═══════════════════════════════════════════════════════════ */
#define MRR_NET_OK                  0
#define MRR_NET_ERR_INIT_FAILED    -1
#define MRR_NET_ERR_SOCKET         -2
#define MRR_NET_ERR_CONNECT        -3
#define MRR_NET_ERR_DNS            -4
#define MRR_NET_ERR_SEND           -5
#define MRR_NET_ERR_RECV           -6
#define MRR_NET_ERR_TLS            -7
#define MRR_NET_ERR_INVALID_PARAM  -8

/* ═══════════════════════════════════════════════════════════
 * Veri Yapıları
 * ═══════════════════════════════════════════════════════════ */

typedef struct {
    int status_code;
    char* body;
    size_t body_size;
    char* headers;
    char* error_message;
} MRR_HttpResponse;

/* ═══════════════════════════════════════════════════════════
 * Ağ Çekirdeği
 * ═══════════════════════════════════════════════════════════ */

int mrr_net_init(void);
void mrr_net_cleanup(void);

/* ═══════════════════════════════════════════════════════════
 * Standart Soketler
 * ═══════════════════════════════════════════════════════════ */

int mrr_socket_create(int domain, int type, int protocol);
int mrr_socket_connect(int fd, const char* host, int port);
int mrr_socket_bind(int fd, const char* host, int port);
int mrr_socket_listen(int fd, int backlog);
int mrr_socket_accept(int fd, char* out_ip, int* out_port);
int mrr_socket_send(int fd, const void* data, size_t size);
int mrr_socket_recv(int fd, void* buffer, size_t size);
void mrr_socket_close(int fd);

/* ═══════════════════════════════════════════════════════════
 * HTTP/HTTPS İstemcisi
 * ═══════════════════════════════════════════════════════════ */

MRR_HttpResponse* mrr_http_request(const char* method, const char* url, 
                                   const char* body, const char* headers);
void mrr_http_free_response(MRR_HttpResponse* resp);

/* ═══════════════════════════════════════════════════════════
 * Yardımcı Fonksiyonlar
 * ═══════════════════════════════════════════════════════════ */

const char* mrr_net_get_last_error(void);

#ifdef __cplusplus
}
#endif

#endif /* MRR_PORTSWINGER_H */
