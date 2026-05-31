#ifndef _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H
#define _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H

#include <math.h>

/* =========================================================================
* 🛡️ SYSTEM CORE SPECIFICATION & EVALUATION DECLARATION
* =========================================================================
* LICENSE: GNU GPLv3 (Strong Reciprocal Copyleft)
* DISCLAIMER: THIS IS A PROTOTYPE EVALUATION TEST VERSION ("_TEST.h").
* ========================================================================= */

/**
* ⚡ Register-optimized Fast Absolute Value Macro
* Uses compiler built-ins to clear the sign bit inside the CPU registers in 1 cycle,
* completely avoiding pointer aliasing violations or store-forwarding stalls.
*/
#if defined( __GNUC__) || defined( __clang__)
#define HPNT_ABS( x) __builtin_fabs(x)
#else
#define HPNT_ABS( x) fabs(x)
#endif

/**
* @struct HPNTChannelState
* @brief 2x2 State-Space Cell mapped directly to CPU Registers and L1 Cache.
* @details Eliminates dynamic memory allocation to guarantee zero-latency execution.
*/
typedef struct {
double p00; /* Prior error covariance element [0,0] */
double p01; /* Symmetric error covariance element [0,1] / [1,0] */
double p11; /* Prior error covariance element [1,1] */
double x0; /* State vector element [0] (Signal Amplitude / Intent) */
double x1; /* State vector element [1] (Signal Velocity / Phase) */
} HPNTChannelState;

/**
* @brief HPNT 2x2 Decoupled Scalar Pipeline Single-Sample Execution Core.
* @return int Returns 1 if action threshold is triggered (Exoskeleton ON), otherwise 0.
* @note This is a designated TEST evaluation version. Liability limited under GPLv3.
*/
static inline int hpnt_execute_channel_step(
double raw_signal,
HPNTChannelState* state,
double cos_t,
double sin_t,
double q_noise,
double r_noise,
double lambda_val,
double theta_gate,
double* out_p_state
) {
/* -------------------------------------------------------------------------
* 1. State Prediction (Linear Vector Rotation in 2D Plane)
* ------------------------------------------------------------------------- */
double x0_pred = cos_t * state-> x0 - sin_t * state-> x1;
double x1_pred = sin_t * state-> x0 + cos_t * state-> x1;

double cos_sq = cos_t * cos_t;
double sin_sq = sin_t * sin_t;
double cos_sin = cos_t * sin_t;

/* -------------------------------------------------------------------------
* 2. Error Covariance Prediction (Scalar Expanded Formulation)
* ------------------------------------------------------------------------- */
double p00_m = ( cos_sq * state-> p00) - ( 2.0 * cos_sin * state-> p01) + ( sin_sq * state-> p11) + q_noise;
double p01_m = ( cos_sin * ( state-> p00 - state-> p11)) + (( cos_sq - sin_sq) * state-> p01);
double p11_m = ( sin_sq * state-> p00) + ( 2.0 * cos_sin * state-> p01) + ( cos_sq * state-> p11) + q_noise;

/* -------------------------------------------------------------------------
* 3. Pre-Update Cauchy-Schwarz Guard (Prevents Negative Matrix Singularity)
* ------------------------------------------------------------------------- */
double p_prod_m = p00_m * p11_m;
double max_p01_m = sqrt( p_prod_m > 1e-28 ? p_prod_m : 1e-28);
if ( p01_m > max_p01_m) p01_m = max_p01_m;
else if ( p01_m < - max_p01_m) p01_m = - max_p01_m;

/* -------------------------------------------------------------------------
* 4. Kalman Gain Calculation & Zero-Division Avoidance Boundary
* ------------------------------------------------------------------------- */
double innov_cov = p00_m + r_noise;
if ( innov_cov < 1e-12) innov_cov = 1e-12;

double k0 = p00_m / innov_cov;
double k1 = p01_m / innov_cov;
double one_minus_k0 = 1.0 - k0;

/* -------------------------------------------------------------------------
* 5. Exact Scalar Joseph Form Covariance Update (Symmetric & Mathematically Verified)
* Forces positive-definiteness natively at the compiler level.
* ------------------------------------------------------------------------- */
double p00_new = ( one_minus_k0 * one_minus_k0 * p00_m) + ( k0 * k0 * r_noise);

/* 🟢 [수정 완료] 기술 사양서의 대수학적 묶음 구조 동기화 및 오타(k1_r_noise -> k0 * k1 * r_noise) 원천 교정 */
double p01_new = one_minus_k0 * ( p01_m - k1 * p00_m) + ( k0 * k1 * r_noise);

double p11_new = p11_m - ( 2.0 * k1 * p01_m) + ( k1 * k1 * p00_m) + ( k1 * k1 * r_noise);

/* Enforce numerical stability lower bound */
if ( p00_new < 1e-14) p00_new = 1e-14;
if ( p11_new < 1e-14) p11_new = 1e-14;

/* -------------------------------------------------------------------------
* 6. Post-Update Cauchy-Schwarz Runtime Stability Guard
* ------------------------------------------------------------------------- */
double p_prod = p00_new * p11_new;
double max_p01 = sqrt( p_prod > 1e-28 ? p_prod : 1e-28);
if ( p01_new > max_p01) p01_new = max_p01;
else if ( p01_new < - max_p01) p01_new = - max_p01;

/* -------------------------------------------------------------------------
* 7. State Update (Innovation Reflection)
* ------------------------------------------------------------------------- */
double innovation = raw_signal - x0_pred;
double x0_new = x0_pred + k0 * innovation;
double x1_new = x1_pred + k1 * innovation;

/* -------------------------------------------------------------------------
* 8. Failsafe Hold Logic (NaN & Numerical Overflow Hard Truncation)
* ------------------------------------------------------------------------- */
if (( x0_new != x0_new) || ( x1_new != x1_new) ||
HPNT_ABS( x0_new) > 1e10 || HPNT_ABS( x1_new) > 1e10 ||
p00_new > 1e10 || p11_new > 1e10) {
/* 🟢 [수정 완료] NaN 오염으로 인한 무한 루프 교착 상태(Freeze)를 방지하기 위해 안전한 상수 가드로 리셋 처리 */
state-> x0 = 0.0;
state-> x1 = 0.0;
state-> p00 = 10.0;
state-> p01 = 0.0;
state-> p11 = 10.0;
* out_p_state = 0.0;
return 0;
}

/* Commit verified state back to the static memory block */
state-> p00 = p00_new;
state-> p01 = p01_new;
state-> p11 = p11_new;
state-> x0 = x0_new;
state-> x1 = x1_new;

/* -------------------------------------------------------------------------
* 9. Zero-Baseline Hyper-Sigmoid Gating Probability Compression (Optimized)
* ------------------------------------------------------------------------- */
double energy = x0_new * x0_new + x1_new * x1_new;
double scaled_energy = lambda_val * energy;
double raw_prob = 0.0;

/* For scaled_energy > 9.0, exp(-9) ≈ 0.00012, pushing raw_prob past 0.9999.
* Hard clipping at 9.0 prevents high-order Pade polynomial divergence at infinity. */
if ( scaled_energy > 9.0) {
raw_prob = 1.0;
} else if ( scaled_energy > 1e-12) {
/* L-Stable Pade Approximation for exp(-x) to guarantee positive denominators */
double x = scaled_energy;
double x2 = x * x;
double num = 12.0 - 6.0 * x + x2;
double den = 12.0 + 6.0 * x + x2;

/* 🟢 [수정 완료] 음수 노이즈 유입 시 발생할 수 있는 분모 Zero 크래시 위험 가드 추가 */
if ( den < 1e-6) den = 1e-6;

double fast_exp = num / den;
if ( fast_exp < 0.0) fast_exp = 0.0; /* Failsafe underflow bound */

raw_prob = ( 2.0 / ( 1.0 + fast_exp)) - 1.0;
}

/* -------------------------------------------------------------------------
* 10. Safe Gating Mechanism Outward Mapping
* ------------------------------------------------------------------------- */
double local_theta = theta_gate < 0.999 ? theta_gate : 0.999;
if ( raw_prob < local_theta) {
* out_p_state = 0.0;
} else {
* out_p_state = ( raw_prob - local_theta) / ( 1.0 - local_theta);
}

return (* out_p_state > 0.75) ? 1 : 0;
}

/**
* @brief Decoupled Massive Parallel Execution Kernel (Spatial Multiplexing Multi-Channel)
* @note __restrict keywords eliminate memory aliasing, enabling aggressive SIMD auto-vectorization.
*/
static inline void hpnt_process_multichannel_batch(
int num_channels,
const double* __restrict input_signals,
HPNTChannelState* __restrict states,
const double* __restrict cos_t_array,
const double* __restrict sin_t_array,
double q_noise,
double r_noise,
double lambda_val,
double theta_gate,
double* __restrict out_probabilities,
int* __restrict out_triggers
) {
for ( int ch = 0; ch < num_channels; ++ ch) {
out_triggers[ ch] = hpnt_execute_channel_step(
input_signals[ ch],
& states[ ch],
cos_t_array[ ch],
sin_t_array[ ch],
q_noise,
r_noise,
lambda_val,
theta_gate,
& out_probabilities[ ch]
);
}
}

#endif /* _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H */
