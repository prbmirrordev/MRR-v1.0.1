#ifndef MRR_RESPONSE_H
#define MRR_RESPONSE_H

#include "requests.h" // For MRR_HttpResponse structure

#ifdef __cplusplus
extern "C" {
#endif

// Parse the raw response and separate headers from body
void mrr_response_parse(MRR_HttpResponse* resp);

// Get the HTTP status code
int mrr_response_get_status_code(MRR_HttpResponse* resp);

// Get the body of the response (must call mrr_response_parse first)
const char* mrr_response_get_body(MRR_HttpResponse* resp);

// Get the headers part of the response (must call mrr_response_parse first)
const char* mrr_response_get_headers(MRR_HttpResponse* resp);

// Extract a specific header value
char* mrr_response_get_header_value(MRR_HttpResponse* resp, const char* header_name);

#ifdef __cplusplus
}
#endif

#endif // MRR_RESPONSE_H
