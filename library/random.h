#ifndef MRR_RANDOM_H
#define MRR_RANDOM_H

#ifdef __cplusplus
extern "C" {
#endif

// Seed the random number generator
void mrr_random_seed(unsigned int seed);

// Generate random float between 0.0 and 1.0
double mrr_random_random();

// Generate random integer between min and max (inclusive)
int mrr_random_randint(int min, int max);

// Generate cryptographically secure random bytes
int mrr_random_secure_bytes(unsigned char* buffer, int length);

#ifdef __cplusplus
}
#endif

#endif // MRR_RANDOM_H
