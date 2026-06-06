/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Portswinger Network Library — L7 Implementation            ║
 * ║                                                                  ║
 * ║  Cross-platform ağ I/O:                                         ║
 * ║    Windows: Winsock2                                            ║
 * ║    Linux:   POSIX Sockets                                       ║
 * ║                                                                  ║
 * ║  Gelecek TLS desteği için OpenSSL veya WinHTTP fallback          ║
 * ║  kullanılabilir, şimdilik raw TCP üzerinden HTTP.               ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

#include "portswinger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#ifdef _WIN32
    #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <unistd.h>
    #include <sys/types.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <netdb.h>
    #define closesocket close
#endif

static thread_local char g_last_error[512] = {0};

static void set_error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vsnprintf(g_last_error, sizeof(g_last_error), fmt, args);
    va_end(args);
}

const char* mrr_net_get_last_error(void) {
    return g_last_error;
}

/* ═══════════════════════════════════════════════════════════
 * Core Initialization
 * ═══════════════════════════════════════════════════════════ */

int mrr_net_init(void) {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        set_error("WSAStartup failed: %d", WSAGetLastError());
        return MRR_NET_ERR_INIT_FAILED;
    }
#endif
    return MRR_NET_OK;
}

void mrr_net_cleanup(void) {
#ifdef _WIN32
    WSACleanup();
#endif
}

/* ═══════════════════════════════════════════════════════════
 * Standard Sockets
 * ═══════════════════════════════════════════════════════════ */

int mrr_socket_create(int domain, int type, int protocol) {
    int fd = socket(domain, type, protocol);
    if (fd < 0) {
#ifdef _WIN32
        set_error("socket creation failed: %d", WSAGetLastError());
#else
        set_error("socket creation failed");
#endif
        return -1;
    }
    return fd;
}

int mrr_socket_connect(int fd, const char* host, int port) {
    if (fd < 0 || !host) return MRR_NET_ERR_INVALID_PARAM;

    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%d", port);

    if (getaddrinfo(host, port_str, &hints, &res) != 0) {
        set_error("DNS resolution failed for %s", host);
        return MRR_NET_ERR_DNS;
    }

    if (connect(fd, res->ai_addr, res->ai_addrlen) < 0) {
        freeaddrinfo(res);
        set_error("Connection failed to %s:%d", host, port);
        return MRR_NET_ERR_CONNECT;
    }

    freeaddrinfo(res);
    return MRR_NET_OK;
}

void mrr_socket_close(int fd) {
    if (fd >= 0) closesocket(fd);
}

/* ═══════════════════════════════════════════════════════════
 * HTTP Client (Basit L7 Abstraction)
 * ═══════════════════════════════════════════════════════════ */

static void parse_url(const char* url, char* host, char* path, int* port, int* is_https) {
    *port = 80;
    *is_https = 0;
    strcpy(path, "/");
    const char* host_start = url;
    
    if (strncmp(url, "http://", 7) == 0) {
        host_start = url + 7;
    } else if (strncmp(url, "https://", 8) == 0) {
        host_start = url + 8;
        *port = 443;
        *is_https = 1;
    }
    
    const char* path_start = strchr(host_start, '/');
    if (path_start) {
        int host_len = path_start - host_start;
        strncpy(host, host_start, host_len);
        host[host_len] = '\0';
        strcpy(path, path_start);
    } else {
        strcpy(host, host_start);
    }
    
    char* port_sep = strchr(host, ':');
    if (port_sep) {
        *port_sep = '\0';
        *port = atoi(port_sep + 1);
    }
}

MRR_HttpResponse* mrr_http_request(const char* method, const char* url, 
                                   const char* body, const char* headers) {
    MRR_HttpResponse* resp = (MRR_HttpResponse*)calloc(1, sizeof(MRR_HttpResponse));
    
    char host[256] = {0};
    char path[1024] = {0};
    int port = 80;
    int is_https = 0;
    
    parse_url(url, host, path, &port, &is_https);
    
    /* İleride C++ TLS implementasyonu eklenebilir, şimdilik sadece köprü var */
    if (is_https) {
        resp->error_message = strdup("HTTPS not fully implemented in C backend yet, use Python fallback");
        return resp;
    }

    int sockfd = mrr_socket_create(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        resp->error_message = strdup("Socket creation failed");
        return resp;
    }
    
    if (mrr_socket_connect(sockfd, host, port) != MRR_NET_OK) {
        resp->error_message = strdup("Connection failed");
        mrr_socket_close(sockfd);
        return resp;
    }
    
    int body_len = body ? strlen(body) : 0;
    char request[4096];
    
    snprintf(request, sizeof(request),
             "%s %s HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Connection: close\r\n"
             "User-Agent: MRR-Portswinger/1.0\r\n", 
             method ? method : "GET", path, host);
             
    if (headers) {
        strncat(request, headers, sizeof(request) - strlen(request) - 1);
    }
    
    if (body_len > 0) {
        char content_len[64];
        snprintf(content_len, sizeof(content_len), "Content-Length: %d\r\n\r\n", body_len);
        strncat(request, content_len, sizeof(request) - strlen(request) - 1);
        strncat(request, body, sizeof(request) - strlen(request) - 1);
    } else {
        strncat(request, "\r\n", sizeof(request) - strlen(request) - 1);
    }
    
    send(sockfd, request, strlen(request), 0);
    
    size_t buffer_size = 8192;
    size_t total_read = 0;
    char* response_data = (char*)malloc(buffer_size);
    response_data[0] = '\0';
    
    char chunk[1024];
    int bytes_read;
    while ((bytes_read = recv(sockfd, chunk, sizeof(chunk) - 1, 0)) > 0) {
        if (total_read + bytes_read + 1 >= buffer_size) {
            buffer_size *= 2;
            response_data = (char*)realloc(response_data, buffer_size);
        }
        memcpy(response_data + total_read, chunk, bytes_read);
        total_read += bytes_read;
        response_data[total_read] = '\0';
    }
    
    mrr_socket_close(sockfd);
    
    if (strncmp(response_data, "HTTP/", 5) == 0) {
        char* space = strchr(response_data, ' ');
        if (space) {
            resp->status_code = atoi(space + 1);
        }
    }
    
    resp->body = response_data;
    resp->body_size = total_read;
    return resp;
}

void mrr_http_free_response(MRR_HttpResponse* resp) {
    if (resp) {
        if (resp->body) free(resp->body);
        if (resp->headers) free(resp->headers);
        if (resp->error_message) free(resp->error_message);
        free(resp);
    }
}
