/*
 * MRR Runtime — Raw Socket Network Primitives Stub
 * Phase 1: Placeholder
 */

extern "C" {

int mrr_socket_raw(int domain, int protocol) {
    (void)domain; (void)protocol;
    return -1; // Not implemented
}

int mrr_socket_send(int fd, const void* data, unsigned int size) {
    (void)fd; (void)data; (void)size;
    return -1;
}

int mrr_socket_recv(int fd, void* buffer, unsigned int size) {
    (void)fd; (void)buffer; (void)size;
    return -1;
}

} // extern "C"
