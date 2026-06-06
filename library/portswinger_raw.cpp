/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Portswinger Network Library — Raw Sockets Implementation   ║
 * ║                                                                  ║
 * ║  Raw I/O ve packet crafting (Windows & Linux).                  ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

#include "portswinger_raw.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
    #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
#else
    #include <unistd.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <netinet/ip.h>
    #include <netinet/tcp.h>
    #include <netinet/udp.h>
    #include <arpa/inet.h>
    #define closesocket close
#endif

/* ═══════════════════════════════════════════════════════════
 * Raw Sockets
 * ═══════════════════════════════════════════════════════════ */

int mrr_raw_socket_create(int protocol) {
#ifdef _WIN32
    int fd = socket(AF_INET, SOCK_RAW, protocol);
    if (fd < 0) return -1;
    
    // IP_HDRINCL on Windows needs Administrator privileges
    int optval = 1;
    setsockopt(fd, IPPROTO_IP, IP_HDRINCL, (char*)&optval, sizeof(optval));
    return fd;
#else
    int fd = socket(AF_INET, SOCK_RAW, protocol);
    if (fd < 0) return -1;
    
    int optval = 1;
    setsockopt(fd, IPPROTO_IP, IP_HDRINCL, &optval, sizeof(optval));
    return fd;
#endif
}

int mrr_raw_socket_send(int fd, const char* ip, const void* packet, size_t size) {
    if (fd < 0 || !ip || !packet) return -1;
    
    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_addr.s_addr = inet_addr(ip);
    
    int sent = sendto(fd, (const char*)packet, size, 0, (struct sockaddr*)&dest, sizeof(dest));
    return sent;
}

void mrr_raw_socket_close(int fd) {
    if (fd >= 0) closesocket(fd);
}

/* ═══════════════════════════════════════════════════════════
 * Checksum Helpers
 * ═══════════════════════════════════════════════════════════ */

static uint16_t calculate_checksum(uint16_t* ptr, int nbytes) {
    long sum = 0;
    short answer;
    
    while(nbytes > 1) {
        sum += *ptr++;
        nbytes -= 2;
    }
    if(nbytes == 1) {
        sum += *(unsigned char*)ptr;
    }
    
    sum = (sum >> 16) + (sum & 0xffff);
    sum += (sum >> 16);
    answer = (short)~sum;
    
    return answer;
}

/* ═══════════════════════════════════════════════════════════
 * Packet Crafting
 * ═══════════════════════════════════════════════════════════ */

MRR_Packet* mrr_craft_ip_header(const char* src_ip, const char* dst_ip, 
                                uint8_t ttl, uint8_t protocol) {
    MRR_Packet* pkt = (MRR_Packet*)malloc(sizeof(MRR_Packet));
    pkt->size = 20; // Basic IPv4 header
    pkt->buffer = (uint8_t*)calloc(1, pkt->size);
    
    // Basit IP header construction
    pkt->buffer[0] = 0x45; // Version 4, IHL 5
    pkt->buffer[1] = 0x00; // TOS
    // Total length omitted for now, usually filled by OS or later
    pkt->buffer[4] = 0x54; pkt->buffer[5] = 0x32; // ID
    pkt->buffer[6] = 0x00; pkt->buffer[7] = 0x00; // Flags/Offset
    pkt->buffer[8] = ttl;
    pkt->buffer[9] = protocol;
    
    uint32_t src = inet_addr(src_ip);
    uint32_t dst = inet_addr(dst_ip);
    memcpy(&pkt->buffer[12], &src, 4);
    memcpy(&pkt->buffer[16], &dst, 4);
    
    // Calculate IP Checksum
    uint16_t checksum = calculate_checksum((uint16_t*)pkt->buffer, pkt->size);
    memcpy(&pkt->buffer[10], &checksum, 2);
    
    return pkt;
}

MRR_Packet* mrr_craft_tcp_header(uint16_t src_port, uint16_t dst_port, 
                                 uint32_t seq, uint32_t ack, uint8_t flags) {
    MRR_Packet* pkt = (MRR_Packet*)malloc(sizeof(MRR_Packet));
    pkt->size = 20; // Basic TCP header
    pkt->buffer = (uint8_t*)calloc(1, pkt->size);
    
    uint16_t sp = htons(src_port);
    uint16_t dp = htons(dst_port);
    memcpy(&pkt->buffer[0], &sp, 2);
    memcpy(&pkt->buffer[2], &dp, 2);
    
    uint32_t s = htonl(seq);
    uint32_t a = htonl(ack);
    memcpy(&pkt->buffer[4], &s, 4);
    memcpy(&pkt->buffer[8], &a, 4);
    
    pkt->buffer[12] = 0x50; // Data offset (5 words)
    pkt->buffer[13] = flags;
    
    uint16_t window = htons(5840); // Standard window size
    memcpy(&pkt->buffer[14], &window, 2);
    
    return pkt;
}

MRR_Packet* mrr_craft_udp_header(uint16_t src_port, uint16_t dst_port, size_t payload_len) {
    MRR_Packet* pkt = (MRR_Packet*)malloc(sizeof(MRR_Packet));
    pkt->size = 8;
    pkt->buffer = (uint8_t*)calloc(1, pkt->size);
    
    uint16_t sp = htons(src_port);
    uint16_t dp = htons(dst_port);
    uint16_t len = htons((uint16_t)(8 + payload_len));
    
    memcpy(&pkt->buffer[0], &sp, 2);
    memcpy(&pkt->buffer[2], &dp, 2);
    memcpy(&pkt->buffer[4], &len, 2);
    
    return pkt;
}

void mrr_free_packet(MRR_Packet* pkt) {
    if (pkt) {
        if (pkt->buffer) free(pkt->buffer);
        free(pkt);
    }
}
