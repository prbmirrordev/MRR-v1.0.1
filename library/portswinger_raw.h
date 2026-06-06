/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Portswinger Network Library — Raw Sockets & Packet Craft   ║
 * ║                                                                  ║
 * ║  L2/L3 Ağ erişimi (Raw Sockets).                                ║
 * ║  GÜVENLİK: YALNIZCA exploit/unsafe blokları içinden.            ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

#ifndef MRR_PORTSWINGER_RAW_H
#define MRR_PORTSWINGER_RAW_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════════════════════════════════════
 * Raw Sockets
 * ═══════════════════════════════════════════════════════════ */

int mrr_raw_socket_create(int protocol);
int mrr_raw_socket_send(int fd, const char* ip, const void* packet, size_t size);
void mrr_raw_socket_close(int fd);

/* ═══════════════════════════════════════════════════════════
 * Packet Crafting
 * ═══════════════════════════════════════════════════════════ */

typedef struct {
    uint8_t* buffer;
    size_t size;
} MRR_Packet;

MRR_Packet* mrr_craft_ip_header(const char* src_ip, const char* dst_ip, 
                                uint8_t ttl, uint8_t protocol);

MRR_Packet* mrr_craft_tcp_header(uint16_t src_port, uint16_t dst_port, 
                                 uint32_t seq, uint32_t ack, uint8_t flags);

MRR_Packet* mrr_craft_udp_header(uint16_t src_port, uint16_t dst_port, size_t payload_len);

void mrr_free_packet(MRR_Packet* pkt);

#ifdef __cplusplus
}
#endif

#endif /* MRR_PORTSWINGER_RAW_H */
