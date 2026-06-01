#ifndef _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H
#define _2X2_DECOUPLED_PARALLEL_C_ENGINE_TEST_H

#include <math.h>

#define HPNT_SATURATION_NODE 3.4641016151377545

#if defined(__GNUC__) || defined(__clang__)
#define HPNT_ABS(x) __builtin_fabs(x)
#define HPNT_ISNAN(x) __builtin_isnan(x)
#else
#define HPNT_ABS(x) fabs(x)
#define HPNT_ISNAN(x) isnan(x)
#endif

typedef struct {
    double p00; 
    double p01; 
    double p11; 
    double x0;  
    double x1;  
} HPNTChannelState;

static inline int hpnt_execute_channel_step(
    double raw_signal,
    HPNTChannelState* __restrict state,  
    double cos_t,
    double sin_t,
    double q_noise,
    double r_noise,
    double lambda_val,
    double theta_gate,
    double* __restrict out_p_state       
) {
    /* [Failsafe Register Backup / 불시 안전 레지스터 백업] */
    const double b_p00 = state->p00;
    const double b_p01 = state->p01;
    const double b_p11 = state->p11;
    const double b_x0  = state->x0;
    const double b_x1  = state->x1;

    /* 1. State Prediction / 상태 변수 예측 단계 */
    double x0_pred = cos_t * b_x0 - sin_t * b_x1;
    double x1_pred = sin_t * b_x0 + cos_t * b_x1;
    double cos_sq = cos_t * cos_t;
    double sin_sq = sin_t * sin_t;
    double cos_sin = cos_t * sin_t;

    /* 2. Error Covariance Prediction / 오차 공분산 예측 단계 */
    double p00_m = (cos_sq * b_p00) - (2.0 * cos_sin * b_p01) + (sin_sq * b_p11) + q_noise;
    double p01_m = (cos_sin * (b_p00 - b_p11)) + ((cos_sq - sin_sq) * b_p01);
    double p11_m = (sin_sq * b_p00) + (2.0 * cos_sin * b_p01) + (cos_sq * b_p11) + q_noise;

    /* 3. Pre-Update Cauchy-Schwarz Guard / 업데이트 전 코시-슈바르츠 경계 조건 적용 */
    double p_prod_m = p00_m * p11_m;
    if (!(p_prod_m > 1e-30) || HPNT_ISNAN(p_prod_m)) {
        p_prod_m = 1e-30;
        p01_m = 0.0; 
    }
    double max_p01_m = sqrt(p_prod_m);
    
    if (p01_m > max_p01_m) p01_m = max_p01_m;
    else if (!(p01_m >= -max_p01_m)) p01_m = -max_p01_m; 

    /* 4. Kalman Gain Calculation / 칼만 이득 연산 단계 */
    double innov_cov = p00_m + r_noise;
    if (!(innov_cov >= 1e-12) || HPNT_ISNAN(innov_cov)) innov_cov = 1e-12; 
    double k0 = p00_m / innov_cov;
    double k1 = p01_m / innov_cov;
    double one_minus_k0 = 1.0 - k0;

    /* 5. Exact Scalar Joseph Form Covariance Update / 위상 평형 조셉 형태 공식 기반 공분산 업데이트 */
    double p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise);
    double p01_new = one_minus_k0 * p01_m - one_minus_k0 * k1 * p00_m + (k0 * k1 * r_noise);
    double p11_new = p11_m + (2.0 * k1 * p01_m) + (k1 * k1 * p00_m) + (k1 * k1 * r_noise); 
    
    if (!(p00_new >= 1e-14) || HPNT_ISNAN(p00_new)) p00_new = 1e-14;
    if (!(p11_new >= 1e-14) || HPNT_ISNAN(p11_new)) p11_new = 1e-14;

    /* 6. Post-Update Cauchy-Schwarz Guard / 업데이트 후 코시-슈바르츠 행렬 정정성 가드 */
    double p_prod = p00_new * p11_new;
    if (!(p_prod > 1e-30) || HPNT_ISNAN(p_prod)) {
        p_prod = 1e-30;
        p01_new = 0.0;
    }
    double max_p01 = sqrt(p_prod);
    
    if (p01_new > max_p01) p01_new = max_p01;
    else if (!(p01_new >= -max_p01)) p01_new = -max_p01;

    /* 7. State Update / 추정 상태 변수 업데이트 단계 */
    double innovation = raw_signal - x0_pred;
    double x0_new = x0_pred + k0 * innovation;
    double x1_new = x1_pred + k1 * innovation;

    /* 8. Failsafe Hold Logic / 임계값 상한 돌파 시 상태 홀딩 및 예외 처리 구역 */
    if (HPNT_ISNAN(x0_new) || HPNT_ISNAN(x1_new) ||
        HPNT_ABS(x0_new) > 1e10 || HPNT_ABS(x1_new) > 1e10 ||
        p00_new > 1e10 || p11_new > 1e10) {
        state->p00 = b_p00;
        state->p01 = b_p01;
        state->p11 = b_p11;
        state->x0  = b_x0;
        state->x1  = b_x1;
        *out_p_state = 0.0;
        return 0;
    }

    /* Update Register Data Commit / 확정 연산 데이터 최종 반영 */
    state->p00 = p00_new;
    state->p01 = p01_new;
    state->p11 = p11_new;
    state->x0 = x0_new;
    state->x1 = x1_new;

    /* 9. Zero-Baseline Hyper-Sigmoid Gating (Unity-Mapped Padé Approximant) / 왜곡 없는 단위화 파데 다항식 기반 비선형 압축 */
    double energy = x0_new * x0_new + x1_new * x1_new;
    double scaled_energy = lambda_val * energy;
    double raw_prob = 0.0;

    if (scaled_energy > 0.0 && !HPNT_ISNAN(scaled_energy)) {
        double x = scaled_energy;
        if (!(x < HPNT_SATURATION_NODE)) { 
            raw_prob = 1.0;
        } else {
            /* Rational Polynomial for Exact Unity Mapping / 정점에서 1.0에 도달하는 유리 다항식 매핑 */
            double num = 6.928203230275509 * x;
            double den = 12.0 + (x * x);
            raw_prob = num / den;
            
            if (raw_prob > 1.0) raw_prob = 1.0;
        }
    }

    /* 10. Safe Gating Mechanism Outward Mapping / 기저 노이즈 차단을 위한 선형 확장 정규화 공간 맵핑 */
    double local_theta = theta_gate < 0.999 ? theta_gate : 0.999;
    if (!(raw_prob >= local_theta) || HPNT_ISNAN(raw_prob)) {
        *out_p_state = 0.0;
    } else {
        *out_p_state = (raw_prob - local_theta) / (1.0 - local_theta);
    }

    return (*out_p_state > 0.75) ? 1 : 0;
}

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
    int* __restrict n_triggers
) {
    /* [Enforce SIMD Auto-Vectorization / 컴파일러 파이프라인 병렬 벡터화 강제 명령 구역] */
    #if defined(__GNUC__) || defined(__clang__)
    #pragma GCC ivdep
    #elif defined(_MSC_VER)
    #pragma loop(ivdep)
    #endif
    for (int ch = 0; ch < num_channels; ++ch) {
        n_triggers[ch] = hpnt_execute_channel_step(
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
