#ifndef MRR_DATETIME_H
#define MRR_DATETIME_H

#ifdef __cplusplus
extern "C" {
#endif

// Get current Unix timestamp (seconds)
long long mrr_datetime_now_timestamp();

// Get formatted current date/time (e.g., "YYYY-MM-DD HH:MM:SS")
char* mrr_datetime_now_str();

// Format a specific timestamp
char* mrr_datetime_format(long long timestamp, const char* format);

// Sleep for given milliseconds
void mrr_datetime_sleep_ms(int ms);

#ifdef __cplusplus
}
#endif

#endif // MRR_DATETIME_H
