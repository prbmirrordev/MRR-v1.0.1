#include "datetime.h"
#include <time.h>
#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

long long mrr_datetime_now_timestamp() {
    return (long long)time(NULL);
}

char* mrr_datetime_now_str() {
    time_t rawtime;
    struct tm* timeinfo;
    char* buffer = (char*)malloc(80);

    time(&rawtime);
    timeinfo = localtime(&rawtime);

    strftime(buffer, 80, "%Y-%m-%d %H:%M:%S", timeinfo);
    return buffer;
}

char* mrr_datetime_format(long long timestamp, const char* format) {
    time_t rawtime = (time_t)timestamp;
    struct tm* timeinfo = localtime(&rawtime);
    char* buffer = (char*)malloc(256);

    strftime(buffer, 256, format, timeinfo);
    return buffer;
}

void mrr_datetime_sleep_ms(int ms) {
#ifdef _WIN32
    Sleep(ms);
#else
    usleep(ms * 1000);
#endif
}
