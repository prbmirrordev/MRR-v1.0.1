#include "json.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

MRR_JsonNode* mrr_json_loads(const char* json_str) {
    // This is a minimal stub for a JSON parser.
    // A full JSON parser in C is extensive.
    // For MRR integration, this parses a very basic root object or string.
    if (!json_str) return NULL;
    
    MRR_JsonNode* root = (MRR_JsonNode*)calloc(1, sizeof(MRR_JsonNode));
    root->type = 3; // Default to string representation for stub
    root->string_val = strdup(json_str);
    return root;
}

char* mrr_json_dumps(MRR_JsonNode* node) {
    if (!node) return strdup("null");
    
    if (node->type == 3 && node->string_val) {
        // Very basic dump
        char* out = (char*)malloc(strlen(node->string_val) + 3);
        sprintf(out, "\"%s\"", node->string_val);
        return out;
    }
    
    return strdup("{}");
}

void mrr_json_free(MRR_JsonNode* node) {
    if (!node) return;
    if (node->key) free(node->key);
    if (node->string_val) free(node->string_val);
    
    mrr_json_free(node->child);
    mrr_json_free(node->next);
    
    free(node);
}
