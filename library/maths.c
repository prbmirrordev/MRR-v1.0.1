#include "maths.h"
#include <math.h>

// Basic Arithmetic
double mrr_math_add(double a, double b) {
    return a + b;
}

double mrr_math_sub(double a, double b) {
    return a - b;
}

double mrr_math_mul(double a, double b) {
    return a * b;
}

double mrr_math_div(double a, double b) {
    if (b == 0.0) return 0.0; // Basic protection against division by zero
    return a / b;
}

double mrr_math_mod(double a, double b) {
    if (b == 0.0) return 0.0;
    return fmod(a, b);
}

// Advanced Arithmetic
double mrr_math_pow(double base, double exp) {
    return pow(base, exp);
}

double mrr_math_sqrt(double x) {
    if (x < 0.0) return -1.0; // Error representation for negative sqrt
    return sqrt(x);
}

double mrr_math_abs(double x) {
    return fabs(x);
}

long long mrr_math_factorial(int n) {
    if (n < 0) return -1;
    if (n == 0 || n == 1) return 1;
    long long result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

// Trigonometry
double mrr_math_sin(double x) {
    return sin(x);
}

double mrr_math_cos(double x) {
    return cos(x);
}

double mrr_math_tan(double x) {
    return tan(x);
}

// Exponential and Logarithmic
double mrr_math_log(double x) {
    if (x <= 0.0) return -1.0;
    return log(x);
}

double mrr_math_log10(double x) {
    if (x <= 0.0) return -1.0;
    return log10(x);
}

double mrr_math_exp(double x) {
    return exp(x);
}

// Rounding
double mrr_math_ceil(double x) {
    return ceil(x);
}

double mrr_math_floor(double x) {
    return floor(x);
}

double mrr_math_round(double x) {
    return round(x);
}

// Utility
double mrr_math_deg_to_rad(double degrees) {
    return degrees * (MRR_PI / 180.0);
}

double mrr_math_rad_to_deg(double radians) {
    return radians * (180.0 / MRR_PI);
}
