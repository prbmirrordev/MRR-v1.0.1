#ifndef MRR_JSON_H
#define MRR_JSON_H

#ifdef __cplusplus
extern "C" {
#endif

// A minimal json node representation
typedef struct MRR_JsonNode {
    int type; // 0: null, 1: int, 2: float, 3: string, 4: array, 5: object
    char* key;
    char* string_val;
    long long int_val;
    double float_val;
    
    struct MRR_JsonNode* child;
    struct MRR_JsonNode* next;
} MRR_JsonNode;

// Parse a JSON string
MRR_JsonNode* mrr_json_loads(const char* json_str);

// Convert a JSON node back to string
char* mrr_json_dumps(MRR_JsonNode* node);

// Free the JSON tree
void mrr_json_free(MRR_JsonNode* node);

#ifdef __cplusplus
}
#endif

#endif // MRR_JSON_H
