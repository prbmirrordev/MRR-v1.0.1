#ifndef MRR_MATHS_H
#define MRR_MATHS_H

#ifdef __cplusplus
extern "C" {
#endif

// Constants
#define MRR_PI 3.14159265358979323846
#define MRR_E  2.71828182845904523536

// Basic Arithmetic
double mrr_math_add(double a, double b);
double mrr_math_sub(double a, double b);
double mrr_math_mul(double a, double b);
double mrr_math_div(double a, double b);
double mrr_math_mod(double a, double b);

// Advanced Arithmetic
double mrr_math_pow(double base, double exp);
double mrr_math_sqrt(double x);
double mrr_math_abs(double x);
long long mrr_math_factorial(int n);

// Trigonometry (Radians)
double mrr_math_sin(double x);
double mrr_math_cos(double x);
double mrr_math_tan(double x);

// Exponential and Logarithmic
double mrr_math_log(double x);
double mrr_math_log10(double x);
double mrr_math_exp(double x);

// Rounding
double mrr_math_ceil(double x);
double mrr_math_floor(double x);
double mrr_math_round(double x);

// Utility
double mrr_math_deg_to_rad(double degrees);
double mrr_math_rad_to_deg(double radians);

#ifdef __cplusplus
}
#endif

#endif // MRR_MATHS_H
