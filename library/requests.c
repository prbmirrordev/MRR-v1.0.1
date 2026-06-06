#include "requests.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#endif

int mrr_requests_init() {
#ifdef _WIN32
    WSADATA wsaData;
    return WSAStartup(MAKEWORD(2, 2), &wsaData) == 0 ? 1 : 0;
#else
    return 1;
#endif
}

void mrr_requests_cleanup() {
#ifdef _WIN32
    WSACleanup();
#endif
}

static void parse_url(const char* url, char* host, char* path, int* port) {
    *port = 80;
    strcpy(path, "/");
    const char* host_start = url;
    
    if (strncmp(url, "http://", 7) == 0) {
        host_start = url + 7;
    } else if (strncmp(url, "https://", 8) == 0) {
        host_start = url + 8;
        *port = 443;
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

static MRR_HttpResponse* send_http_request(const char* host, int port, const char* request_str) {
    MRR_HttpResponse* resp = (MRR_HttpResponse*)calloc(1, sizeof(MRR_HttpResponse));
    
    struct hostent* server = gethostbyname(host);
    if (server == NULL) {
        resp->error = 1;
        return resp;
    }
    
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        resp->error = 1;
        return resp;
    }
    
    struct sockaddr_in serv_addr;
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    memcpy(&serv_addr.sin_addr.s_addr, server->h_addr, server->h_length);
    serv_addr.sin_port = htons(port);
    
    if (connect(sockfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
        resp->error = 1;
        return resp;
    }
    
    send(sockfd, request_str, strlen(request_str), 0);
    
    int buffer_size = 4096;
    int total_read = 0;
    char* response_data = (char*)malloc(buffer_size);
    response_data[0] = '\0';
    
    char chunk[1024];
    int bytes_read;
    while ((bytes_read = recv(sockfd, chunk, sizeof(chunk) - 1, 0)) > 0) {
        chunk[bytes_read] = '\0';
        if (total_read + bytes_read >= buffer_size) {
            buffer_size *= 2;
            response_data = (char*)realloc(response_data, buffer_size);
        }
        memcpy(response_data + total_read, chunk, bytes_read);
        total_read += bytes_read;
        response_data[total_read] = '\0';
    }
    
#ifdef _WIN32
    closesocket(sockfd);
#else
    close(sockfd);
#endif
    
    resp->raw_response = response_data;
    
    if (strncmp(response_data, "HTTP/", 5) == 0) {
        char* space = strchr(response_data, ' ');
        if (space) {
            resp->status_code = atoi(space + 1);
        }
    }
    
    return resp;
}

MRR_HttpResponse* mrr_requests_get(const char* url) {
    char host[256] = {0};
    char path[1024] = {0};
    int port = 80;
    
    parse_url(url, host, path, &port);
    
    char request[2048];
    snprintf(request, sizeof(request),
             "GET %s HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Connection: close\r\n"
             "User-Agent: MRR-Requests/1.0\r\n"
             "\r\n", path, host);
             
    return send_http_request(host, port, request);
}

MRR_HttpResponse* mrr_requests_post(const char* url, const char* data, const char* content_type) {
    char host[256] = {0};
    char path[1024] = {0};
    int port = 80;
    
    parse_url(url, host, path, &port);
    
    if (!content_type) content_type = "application/x-www-form-urlencoded";
    int data_len = data ? strlen(data) : 0;
    
    char* request = (char*)malloc(2048 + data_len);
    snprintf(request, 2048 + data_len,
             "POST %s HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Connection: close\r\n"
             "User-Agent: MRR-Requests/1.0\r\n"
             "Content-Type: %s\r\n"
             "Content-Length: %d\r\n"
             "\r\n"
             "%s", path, host, content_type, data_len, data ? data : "");
             
    MRR_HttpResponse* resp = send_http_request(host, port, request);
    free(request);
    return resp;
}

void mrr_requests_free_response(MRR_HttpResponse* resp) {
    if (resp) {
        if (resp->raw_response) free(resp->raw_response);
        free(resp);
    }
}
