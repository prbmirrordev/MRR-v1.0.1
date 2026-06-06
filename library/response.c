#include "response.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void mrr_response_parse(MRR_HttpResponse* resp) {
    if (!resp || !resp->raw_response) return;
    
    // Find the boundary between headers and body: "\r\n\r\n"
    char* boundary = strstr(resp->raw_response, "\r\n\r\n");
    if (boundary) {
        int headers_len = boundary - resp->raw_response;
        resp->headers = (char*)malloc(headers_len + 1);
        strncpy(resp->headers, resp->raw_response, headers_len);
        resp->headers[headers_len] = '\0';
        
        // Body starts right after "\r\n\r\n"
        resp->body = boundary + 4;
    } else {
        resp->headers = NULL;
        resp->body = resp->raw_response;
    }
}

int mrr_response_get_status_code(MRR_HttpResponse* resp) {
    if (resp) return resp->status_code;
    return -1;
}

const char* mrr_response_get_body(MRR_HttpResponse* resp) {
    if (resp && resp->body) return resp->body;
    return "";
}

const char* mrr_response_get_headers(MRR_HttpResponse* resp) {
    if (resp && resp->headers) return resp->headers;
    return "";
}

char* mrr_response_get_header_value(MRR_HttpResponse* resp, const char* header_name) {
    if (!resp || !resp->headers || !header_name) return NULL;
    
    char search_str[256];
    snprintf(search_str, sizeof(search_str), "\n%s:", header_name);
    
    char* pos = strstr(resp->headers, search_str);
    if (!pos) {
        // Check if it's the very first header
        snprintf(search_str, sizeof(search_str), "%s:", header_name);
        if (strncmp(resp->headers, search_str, strlen(search_str)) == 0) {
            pos = resp->headers;
        }
    }
    
    if (pos) {
        pos += strlen(search_str);
        // Skip whitespace
        while (*pos == ' ' || *pos == '\t') pos++;
        
        char* end_pos = strstr(pos, "\r\n");
        if (!end_pos) end_pos = pos + strlen(pos);
        
        int val_len = end_pos - pos;
        char* value = (char*)malloc(val_len + 1);
        strncpy(value, pos, val_len);
        value[val_len] = '\0';
        return value;
    }
    return NULL;
}
