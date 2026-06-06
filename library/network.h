#ifndef MRR_NETWORK_H
#define MRR_NETWORK_H

#ifdef __cplusplus
extern "C" {
#endif

// Initialize network stack
int mrr_net_init();
void mrr_net_cleanup();

// Sockets
int mrr_net_create_socket();
int mrr_net_connect(int sock, const char* ip, int port);
int mrr_net_bind(int sock, const char* ip, int port);
int mrr_net_listen(int sock, int backlog);
int mrr_net_accept(int sock);
int mrr_net_send(int sock, const char* data, int len);
int mrr_net_recv(int sock, char* buffer, int len);
void mrr_net_close(int sock);

// Port database (auto-generated)
const char* mrr_net_get_port_service_name(int port);
const char* mrr_net_get_port_description(int port);
int mrr_net_is_known_port(int port);

// High level www requests
char* mrr_net_fetch_www(const char* url);

#ifdef __cplusplus
}
#endif

#endif // MRR_NETWORK_H
