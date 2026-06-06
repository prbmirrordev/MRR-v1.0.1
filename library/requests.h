#ifndef MRR_REQUESTS_H
#define MRR_REQUESTS_H

#ifdef __cplusplus
extern "C" {
#endif

// A simple structure to hold an HTTP response returned by requests
typedef struct {
    int status_code;
    char* headers;
    char* body;
    char* raw_response;
    int error;
} MRR_HttpResponse;

// Initialize the networking subsystem (e.g. WSAStartup on Windows)
int mrr_requests_init();

// Cleanup the networking subsystem
void mrr_requests_cleanup();

// Perform an HTTP GET request
MRR_HttpResponse* mrr_requests_get(const char* url);

// Perform an HTTP POST request
MRR_HttpResponse* mrr_requests_post(const char* url, const char* data, const char* content_type);

// Free the response object
void mrr_requests_free_response(MRR_HttpResponse* resp);

#ifdef __cplusplus
}
#endif

#endif // MRR_REQUESTS_H
