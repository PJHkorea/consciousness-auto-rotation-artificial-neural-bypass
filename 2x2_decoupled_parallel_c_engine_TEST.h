#ifndef _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H
#define _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H

#include <math.h>
#include <float.h> // 수치 안정성 상수를 위한 표준 헤더 추가

/* =========================================================================
* 🛡 SYSTEM CORE SPECIFICATION & EVALUATION DECLARATION
* =========================================================================
* LICENSE: GNU GPLv3 (Strong Reciprocal Copyleft)
* DISCLAIMER: SAFETY-ENHANCED STABLE EVALUATION VERSION.
* ========================================================================= */

#if defined(__GNUC__) || defined(__clang__)
#define HPNT_ABS(x) __builtin_fabs(x)
#else
#define HPNT_ABS(x) fabs(x)
#endif

typedef struct {
    double p00; /* Prior error covariance element [0,0] */
    double p01; /* Symmetric error covariance element [0,1] / [1,0] */
    double p11; /* Prior error covariance element [1,1] */
    double x0;  /* State vector element [0] (Signal Amplitude / Intent) */
    double x1;  /* State vector element [1] (Signal Velocity / Phase) */
} HPNTChannelState;

/**
 * @brief HPNT 2x2 Decoupled Scalar Pipeline Single-Sample Execution Core (안정성 강화 버전)
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
    /* [안정성 가드] 연산 실패 시 역학적 충격을 방지하기 위해 이전의 안전한 상태를 백업 */
    HPNTChannelState last_known_good = *state;

    /* -------------------------------------------------------------------------
    * 1. State Prediction (Linear Vector Rotation in 2D Plane)
    * ------------------------------------------------------------------------- */
    double x0_pred = cos_t * state->x0 - sin_t * state->x1;
    double x1_pred = sin_t * state->x0 + cos_t * state->x1;

    double cos_sq = cos_t * cos_t;
    double sin_sq = sin_t * sin_t;
    double cos_sin = cos_t * sin_t;

    /* -------------------------------------------------------------------------
    * 2. Error Covariance Prediction (Scalar Expanded Formulation)
    * ------------------------------------------------------------------------- */
    double p00_m = (cos_sq * state->p00) - (2.0 * cos_sin * state->p01) + (sin_sq * state->p11) + q_noise;
    double p01_m = (cos_sin * (state->p00 - state->p11)) + ((cos_sq - sin_sq) * state->p01);
    double p11_m = (sin_sq * state->p00) + (2.0 * cos_sin * state->p01) + (cos_sq * state->p11) + q_noise;

    /* -------------------------------------------------------------------------
    * 3. Pre-Update Cauchy-Schwarz Guard (Prevents Negative Matrix Singularity)
    * ------------------------------------------------------------------------- */
    double p_prod_m = p00_m * p11_m;
    double max_p01_m = sqrt(p_prod_m > 1e-28 ? p_prod_m : 1e-28);
    if (p01_m > max_p01_m) p01_m = max_p01_m;
    else if (p01_m < -max_p01_m) p01_m = -max_p01_m;

    /* -------------------------------------------------------------------------
    * 4. Kalman Gain Calculation & Zero-Division Avoidance Boundary
    * ------------------------------------------------------------------------- */
    double innov_cov = p00_m + r_noise;
    if (innov_cov < 1e-12) innov_cov = 1e-12;
    
    double k0 = p00_m / innov_cov;
    double k1 = p01_m / innov_cov;
    double one_minus_k0 = 1.0 - k0;

    /* -------------------------------------------------------------------------
    * 5. Exact Scalar Joseph Form Covariance Update
    * ------------------------------------------------------------------------- */
    double p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise);
    double p01_new = one_minus_k0 * (p01_m - k1 * p00_m) + (k0 * k1 * r_noise);
    double p11_new = p11_m - (2.0 * k1 * p01_m) + (k1 * k1 * p00_m) + (k1 * k1 * r_noise);

    if (p00_new < 1e-14) p00_new = 1e-14;
    if (p11_new < 1e-14) p11_new = 1e-14;

    /* -------------------------------------------------------------------------
    * 6. Post-Update Cauchy-Schwarz Runtime Stability Guard
    * ------------------------------------------------------------------------- */
    double p_prod = p00_new * p11_new;
    double max_p01 = sqrt(p_prod > 1e-28 ? p_prod : 1e-28);
    if (p01_new > max_p01) p01_new = max_p01;
    else if (p01_new < -max_p01) p01_new = -max_p01;

    /* -------------------------------------------------------------------------
    * 7. State Update (Innovation Reflection)
    * ------------------------------------------------------------------------- */
    double innovation = raw_signal - x0_pred;
    double x0_new = x0_pred + k0 * innovation;
    double x1_new = x1_pred + k1 * innovation;

    /* -------------------------------------------------------------------------
    * 8. Failsafe Hold Logic (NaN & Numerical Overflow Hard Truncation)
    * ------------------------------------------------------------------------- */
    if ((x0_new != x0_new) || (x1_new != x1_new) ||
        HPNT_ABS(x0_new) > 1e10 || HPNT_ABS(x1_new) > 1e10 ||
        p00_new > 1e10 || p11_new > 1e10) {
        
        /* 🛡️ 하드웨어 급정지 저크(Jerk) 방지: 0.0 리셋 대신 마지막 검증된 안전 데이터(Hold) 복구 */
        *state = last_known_good;
        *out_p_state = 0.0;
        return 0;
    }

    /* 검증된 상태만 메모리에 반영 */
    state->p00 = p00_new;
    state->p01 = p01_new;
    state->p11 = p11_new;
    state->x0 = x0_new;
    state->x1 = x1_new;

    /* -------------------------------------------------------------------------
    * 9. Zero-Baseline Hyper-Sigmoid Gating Probability Compression
    * ------------------------------------------------------------------------- */
    double energy = x0_new * x0_new + x1_new * x1_new;
    double scaled_energy = lambda_val * energy;
    double raw_prob = 0.0;

    if (scaled_energy > 9.0) {
        raw_prob = 1.0;
    } else if (scaled_energy > 1e-12) {
        double x = scaled_energy;
        double x2 = x * x;
        double num = 12.0 - 6.0 * x + x2;
        double den = 12.0 + 6.0 * x + x2;

        /* 🛡️ 머신 앱실론 기반의 유동적 분모 제로 크래시 가드 적용 */
        if (den < DBL_EPSILON) den = DBL_EPSILON;
        
        double fast_exp = num / den;
        if (fast_exp < 0.0) fast_exp = 0.0; 
        raw_prob = (2.0 / (1.0 + fast_exp)) - 1.0;
    }

    /* -------------------------------------------------------------------------
    * 10. Safe Gating Mechanism Outward Mapping
    * ------------------------------------------------------------------------- */
    double local_theta = theta_gate < 0.999 ? theta_gate : 0.999;
    if (raw_prob < local_theta) {
        *out_p_state = 0.0;
    } else {
        *out_p_state = (raw_prob - local_theta) / (1.0 - local_theta);
    }

    return (*out_p_state > 0.75) ? 1 : 0;
}

/**
 * @brief Decoupled Massive Parallel Execution Kernel
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
    for (int ch = 0; ch < num_channels; ++ch) {
        out_triggers[ch] = hpnt_execute_channel_step(
            input_signals[ch],
            &states[ch],
            cos_t_array[ch],
            sin_t_array[ch],
            q_noise,
            r_noise,
            lambda_val,
            theta_gate,
            &out_probabilities[ch]
        );
    }
}

#endif /* _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H */
