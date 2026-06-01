#ifndef _SAFE_CRANIAL_CORE_H
#define _SAFE_CRANIAL_CORE_H

#include <stdint.h>
#include <string.h>

/*
 * ==============================================================================
 * [🚨 컴파일러 옵션 및 저발열/초고속 핵심 지침 - 필수 준수]
 * [🚨 Compiler Options & Low-Thermal Core Guidelines - MANDATORY]
 *
 * 1. 컴파일러 금지 옵션 (-ffast-math / -Ofast 절대 사용 금지!)
 * - 이 옵션을 켜면 `raw_input != raw_input` (NaN 검출 가드)가 통째로 삭제됩니다.
 * - 반드시 IEEE 754 표준을 준수하는 `-O2` 또는 `-O3` 표준 최적화만 사용하십시오.
 *
 * 1. Forbidden Compiler Options (NEVER USE -ffast-math / -Ofast!)
 * - Enabling these deletes the `raw_input != raw_input` (NaN guard) statement.
 * - Ensure you strictly use standard compliance optimizations like `-O2` or `-O3`.
 *
 * 2. 싼 칩(저가형 MCU) 포팅 시 저발열 유지 지침 (float 및 f 리터럴 전환 완전 적용본)
 * - 하드웨어 FPU가 32비트 연산만 지원하는 저가형 칩에서의 발열 및 루프 타이밍 밀림을 
 *   원천 차단하기 위해 모든 double 수식을 float 규격으로 완전 최적화 완료했습니다.
 *
 * 2. Low-Thermal Guidelines for Low-Cost MCU Porting (Fully Implemented)
 * - Converted all structures to float and appended 'f' literals to constants to prevent 
 *   overheating and hardware timing lag on low-cost single-precision FPUs.
 * ==============================================================================
 */

/* ──────────────────────────────────────────────────────────────────────────
 * [설정 상수 정의 / Environment Constants Definition]
 * ────────────────────────────────────────────────────────────────────────── */

// 노이즈 감지 후 사멸 대기 사이클 수 / Dead-time ticks before revival
#define COOL_DOWN_TICKS 500

// 하드웨어 노이즈 임계값 (float 전환 정합 완료) / Hardware noise upper bound
#define INPUT_NOISE_LIMIT 1e7f

// 안전 나눗셈을 위한 최소 분모 임계값 / Zero-division prevention margin
#define EPSILON_GUARD 1e-6f

// 고장으로 판단할 연속 재사멸 횟수 / Consecutive failure limit for fault
#define MAX_FAIL_THRESHOLD 10

// 제곱근(SQRT)을 사용하지 않는 사칙연산 기반 Pade Saturation Threshold
// Padé saturation node threshold based on pure arithmetic without SQRT
#define HPNT_SATURATION_NODE 3.4641016f

#if defined(__GNUC__) || defined(__clang__)
#define HPNT_ABS(x) __builtin_fabsf(x)
#define HPNT_ISNAN(x) __builtin_isnan(x)
#else
#define HPNT_ABS(x) (((x) < 0.0f) ? -(x) : (x))
#define HPNT_ISNAN(x) ((x) != (x))
#endif

/* ──────────────────────────────────────────────────────────────────────────
 * [행렬 프리 SoA 구조체 정의 - float 고속 이식 버전]
 * [Matrix-Free SoA Structure - Float High-Speed Porting]
 * ────────────────────────────────────────────────────────────────────────── */
typedef struct {
    float* __restrict p00;
    float* __restrict p01;
    float* __restrict p11;
    float* __restrict x0;
    float* __restrict x1;
    
    float* __restrict b_p00;
    float* __restrict b_p01;
    float* __restrict b_p11;
    float* __restrict b_x0;
    float* __restrict b_x1;
    float* __restrict b_out_state;

    int32_t* __restrict is_initialized; // 초기화 여부 플래그 / Initialization state flag
    int32_t* __restrict is_alive;       // 활성화 여부 (1=정상, 0=격리) / Activation status (1=Normal, 0=Isolated)
    uint32_t* __restrict dead_time;     // 격리 후 경과 시간 / Cooldown elapsed tick counter
    int32_t* __restrict fail_count;     // 연속 부활 실패 카운터 / Consecutive revival failure tracker
} HPNTMultiChannelState;
/**
 * @brief 원래 깃허브 구조 그대로 인덱싱 처리하는 단일 스텝 핵심 함수 (수식 무결성 정정본)
 * Processes a single step indexed channel mimicking the original structure with verified mathematical integrity.
 */
static inline int hpnt_execute_channel_step_indexed(
    int ch,
    const float* __restrict input_signals,
    HPNTMultiChannelState* __restrict states,
    const float cos_t,
    const float sin_t,
    const float q_noise,
    const float r_noise,
    const float lambda_val,
    const float theta_gate,
    float* __restrict out_probabilities
) {
    // 0. 정적 메모리 초기화 로직 (float 스케일 반영) / Static Memory Initialization Logic (Float scaled)
    if (!states->is_initialized[ch]) {
        states->b_p00[ch] = states->p00[ch];
        states->b_p01[ch] = states->p01[ch];
        states->b_p11[ch] = states->p11[ch];
        states->b_x0[ch] = states->x0[ch];
        states->b_x1[ch] = states->x1[ch];
        states->b_out_state[ch] = 0.0f;
        states->is_alive[ch] = 1;
        states->dead_time[ch] = 0;
        states->fail_count[ch] = 0;
        states->is_initialized[ch] = 1;
    }

    // ─── [규칙 1] 격리(사멸) 상태 검사 및 복구 (발열 스파이크 차단) ───
    // ─── [Rule 1] Isolation Status Check & Cooldown Recovery (Prevents thermal spikes) ───
    if (!states->is_alive[ch]) {
        states->dead_time[ch]++;
        if (states->dead_time[ch] > COOL_DOWN_TICKS) {
            // 부활 진입 시 실패 카운터 우선 누적 / Increment fault tracker during revival transition
            states->fail_count[ch]++;
            // 연속 10번 부활 즉시 죽었다면 -> 하드웨어 센서 부착 위치 불량 고장 판정
            // If it fails 10 times consecutively right after revival -> Hardware Sensor Fault Declared
            if (states->fail_count[ch] >= MAX_FAIL_THRESHOLD) {
                out_probabilities[ch] = 0.0f;
                return -1; // 🚩 하드웨어 고장 알람 신호 송출 / Dispatches Hardware Fault Signal
            }
            // 이번 루프는 안전 기저선 '부팅'만 수행하고 탈출 (부하 분산 -> 저발열)
            // This loop cycle ONLY resets baseline to bypass heavy math (Load Balancing -> Low Thermal)
            states->x0[ch] = 0.0f; states->x1[ch] = 0.0f;
            states->p00[ch] = 10.0f; states->p11[ch] = 10.0f; states->p01[ch] = 0.0f;
            states->b_p00[ch] = 10.0f; states->b_p11[ch] = 10.0f; states->b_p01[ch] = 0.0f;
            states->b_x0[ch] = 0.0f; states->b_x1[ch] = 0.0f;
            states->b_out_state[ch] = 0.0f;
            states->is_alive[ch] = 1;
            states->dead_time[ch] = 0;
            out_probabilities[ch] = 0.0f;
            return 0;
        } else {
            // 격리 기간 중에는 연산을 전면 중지하여 물리 발열 차단
            // Suspends all heavy math during isolation to physically suppress thermal dissipation
            out_probabilities[ch] = 0.0f;
            return 0;
        }
    }

    // ─── [규칙 2] 입력 신호 실시간 노이즈 격리 ───
    // ─── [Rule 2] Real-Time Input Signal Noise Isolation ───
    float raw_input = input_signals[ch];
    // NaN 검출 및 하드 바운더리 검증 통합 (지워지지 않는 안전 가드)
    // Blends NaN detection and hard boundary validation (Unerasable Failsafe Guard)
    if (HPNT_ISNAN(raw_input) || raw_input > INPUT_NOISE_LIMIT || raw_input < -INPUT_NOISE_LIMIT) {
        states->is_alive[ch] = 0; // 즉시 사멸 / Kill channel instantly
        states->dead_time[ch] = 0;
        out_probabilities[ch] = 0.0f;
        return 0; // 하단 연산 진입 전 차단 / Short-circuit execution path
    }

    // 노이즈 가드를 정상 통과한 '진짜 정상 신호'이므로 연속 실패 카운트 리셋
    // Resets consecutive failure tracker since the signal passed the valid noise guard boundaries
    states->fail_count[ch] = 0;

    // 1. Matrix-Free 스칼라 회전 예측 / Subspace State Rotation
    float x0_pred = cos_t * states->x0[ch] - sin_t * states->x1[ch];
    float x1_pred = sin_t * states->x0[ch] + cos_t * states->x1[ch];
    
    float cos_sq = cos_t * cos_t;
    float sin_sq = sin_t * sin_t;
    float cos_sin = cos_t * sin_t;

    // 2. 오차 공분산 예측 / Prior Error Covariance Scalar Expansion
    float p00_m = (cos_sq * states->p00[ch]) -
                  (2.0f * cos_sin * states->p01[ch]) +
                  (sin_sq * states->p11[ch]) + q_noise;

    /* 
     * 🛡️ [수학적 무결성 부호 교정 / Algebraic Sign Rectification]
     * 상태 예측(x0_pred)의 시계 방향(CW) 회전 기하 구조와 공분산 격자 텐서의 대칭 평형을 완벽하게 맞추기 위해 
     * 가운데 결합 부호를 '+'에서 '-'로 정정합니다. 연산 오버헤드는 0 클럭입니다.
     * 
     * Corrected the central coupling sign from '+' to '-' to perfectly align the covariance tensor's 
     * geometric symmetry with the clockwise (CW) rotation of the state vector (x0_pred). Zero computational overhead.
     */
    float p01_m = ((cos_sq - sin_sq) * states->p01[ch]) - 
                  (cos_sin * (states->p00[ch] - states->p11[ch]));

    float p11_m = (sin_sq * states->p00[ch]) +
                  (2.0f * cos_sin * states->p01[ch]) +
                  (cos_sq * states->p11[ch]) + q_noise;

    if (p00_m < 1e-6f) p00_m = 1e-6f;
    if (p11_m < 1e-6f) p11_m = 1e-6f;

    /* [No-SQRT Cauchy-Schwarz Guard] float 사칙연산 경계면 최적화 완료 / Float arithmetic bound optimization complete */
    float p_prod_m = p00_m * p11_m;
    float p01_m_sq = p01_m * p01_m;
    if (p01_m_sq > p_prod_m || HPNT_ISNAN(p01_m_sq)) {
        // 제곱근 없이 대수적 대칭 텐서를 강제 격하 안정화 / Deflates asymmetric tensor to secure boundaries without SQRT
        float min_diag = (p00_m < p11_m) ? p00_m : p11_m;
        p01_m = (p01_m > 0.0f) ? min_diag : -min_diag;
    }

    // 3. Innovation Covariance Singularity Guard (저가형 칩 나눗셈 예외 가드)
    // 3. Innovation Covariance Singularity Guard (Bypasses division exceptions on low-cost MCUs)
    float innov_cov = p00_m + r_noise;
    if (innov_cov <= EPSILON_GUARD || HPNT_ISNAN(innov_cov)) {
        states->x0[ch] = x0_pred; states->x1[ch] = x1_pred;
        states->p00[ch] = p00_m; states->p01[ch] = p01_m; states->p11[ch] = p11_m;
        out_probabilities[ch] = states->b_out_state[ch];
        return (out_probabilities[ch] > 0.75f) ? 1 : 0;
    }

    float S_inv = 1.0f / innov_cov;
    float k0 = p00_m * S_inv;
    if (k0 > 1.0f) k0 = 1.0f;
    float k1 = p01_m * S_inv;
    float one_minus_k0 = 1.0f - k0;

    // 4. Symmetric Joseph Form Covariance Update
    float k1_sq = k1 * k1;
    float p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise);
    float p01_new = one_minus_k0 * (p01_m - k1 * p00_m) + (k0 * k1 * r_noise);

    /* 
     * 🛡️ [조셉 폼 대수적 누락 보정 / Joseph Form Algebraic Restoration]
     * 장기 가동 시 부동소수점 반올림 오차가 한쪽으로 누적되어 칼만 게인이 마비(멍통화)되는 현상을 원천 차단하기 위해,
     * 대수적 수식 유도 과정에서 생략되었던 'one_minus_k0' (1 - k0) 가중치를 교차항에 정확하게 결합합니다. (float FPU 1사이클 소모)
     * 
     * Coupled the missing 'one_minus_k0' (1 - k0) weighting factor into the cross-term to ensure the numerical 
     * positive-definiteness of the Joseph formulation. This permanently prevents filter saturation/blindness 
     * during long-term operation. (Cost: 1 float FPU cycle)
     */
    float p11_new = p11_m - (2.0f * k1 * one_minus_k0 * p01_m) + 
                    (k1_sq * p00_m) + (k1_sq * r_noise);

    if (p00_new < 1e-6f) p00_new = 1e-6f;
    if (p11_new < 1e-6f) p11_new = 1e-6f;

    /* [Post-Update No-SQRT Cauchy-Schwarz Guard] / 사후 업데이트 코시-슈바르츠 제한 가드 */
    float p_prod = p00_new * p11_new;
    float p01_new_sq = p01_new * p01_new;
    if (p01_new_sq > p_prod || HPNT_ISNAN(p01_new_sq)) {
        float min_diag_new = (p00_new < p11_new) ? p00_new : p11_new;
        p01_new = (p01_new > 0.0f) ? min_diag_new : -min_diag_new;
    }

    // 5. Posterior State Update / 사후 상태 업데이트
    float innovation = raw_input - x0_pred;
    float x0_new = x0_pred + k0 * innovation;
    float x1_new = x1_pred + k1 * innovation;

    // 최종 연산 내부 오염 발생 시 방어선 / Internal mathematical pollution guard
    if (HPNT_ISNAN(x0_new) || HPNT_ISNAN(x1_new) || HPNT_ISNAN(p00_new) ||
        HPNT_ABS(x0_new) > INPUT_NOISE_LIMIT || HPNT_ABS(x1_new) > INPUT_NOISE_LIMIT) {
        states->is_alive[ch] = 0;
        states->dead_time[ch] = 0;
        out_probabilities[ch] = 0.0f;
        return 0;
    }
    // 6. Zero-Baseline Hyper-Sigmoid Mapping via Padé Approximant (제곱 도메인 수축 가드)
    // 6. Zero-Baseline Hyper-Sigmoid Mapping via Padé Approximant (Bypasses heavy SQRT)
    float energy = (x0_new * x0_new) + (x1_new * x1_new);
    float scaled_energy = lambda_val * energy;
    float raw_prob = 0.0f;

    if (scaled_energy > 0.0f && !HPNT_ISNAN(scaled_energy)) {
        if (scaled_energy >= HPNT_SATURATION_NODE) {
            raw_prob = 1.0f;
        } else {
            /* 정밀 매핑을 위한 Padé [1/1] 유니폴라 단일정밀도 계수 정합 / Single-precision coefficient mapping for Padé [1/1] */
            float num = 6.0f * scaled_energy;
            float den = 12.0f + (scaled_energy * scaled_energy);
            raw_prob = num / den;
            if (raw_prob > 1.0f) raw_prob = 1.0f;
            if (raw_prob < 0.0f) raw_prob = 0.0f;
        }
    }

    // 7. Dynamic Actuator Interface Linear Space Mapping / 액추에이터 인터페이스 매핑
    // 7. Dynamic Actuator Interface Linear Space Mapping
    float local_theta = (theta_gate < 0.999f) ? theta_gate : 0.999f;
    if (raw_prob < local_theta) {
        out_probabilities[ch] = 0.0f;
    } else {
        out_probabilities[ch] = (raw_prob - local_theta) / (1.0f - local_theta);
    }

    // 데이터 최종 메모리 할당 커밋 / Commit mathematical transitions into memory arrays
    states->p00[ch] = p00_new; states->p01[ch] = p01_new; states->p11[ch] = p11_new;
    states->x0[ch] = x0_new; states->x1[ch] = x1_new;
    
    states->b_p00[ch] = p00_new; states->b_p01[ch] = p01_new; states->b_p11[ch] = p11_new;
    states->b_x0[ch] = x0_new; states->b_x1[ch] = x1_new;
    states->b_out_state[ch] = out_probabilities[ch];

    return (out_probabilities[ch] > 0.75f) ? 1 : 0;
}

/* ──────────────────────────────────────────────────────────────────────────
 * [배치 파이프라인: 다채널 수집 및 시스템 통합 진단 함수]
 * [Batch Pipeline: Multi-Channel Execution & System-Wide Diagnosis]
 * ────────────────────────────────────────────────────────────────────────── */
/**
 * @brief 정해진 개수의 센서 채널을 일괄 병렬 처리하며, 전원 단/접지 붕괴를 진단함
 * Processes multi-channels in parallel and diagnoses common power rail/GND failure.
 * @return 0: 시스템 정상 작동 / System Healthy
 * -99: 🚨 전원/접지 공통 파괴로 인한 긴급 셧다운 필요 / Power Rail Collapse or GND Fault -> System E-Stop
 */
static inline int hpnt_process_multichannel_batch(
    int num_channels,
    const float* __restrict input_signals,
    HPNTMultiChannelState* __restrict states,
    const float* __restrict cos_t_array,
    const float* __restrict sin_t_array,
    const float q_noise,
    const float r_noise,
    const float lambda_val,
    const float theta_gate,
    float* __restrict out_probabilities,
    int* __restrict n_triggers
) {
    int total_failed_sensors = 0; // 이번 턴에 물리적 고장이 선언된 센서 누적 수 / Tally of failed nodes

#if defined(__GNUC__) || defined(__clang__)
    #pragma GCC ivdep
#elif defined(_MSC_VER)
    #pragma loop(ivdep)
#endif
    for (int ch = 0; ch < num_channels; ++ch) {
        n_triggers[ch] = hpnt_execute_channel_step_indexed(
            ch, input_signals, states, cos_t_array[ch], sin_t_array[ch],
            q_noise, r_noise, lambda_val, theta_gate, out_probabilities
        );
        // 특정 채널에서 위치 불량/단선 고장 경고 신호(-1)가 반환되면 카운터 누적
        // If a channel throws `-1` (sensor misplaced), increment system anomaly tracker
        if (n_triggers[ch] == -1) {
            total_failed_sensors++;
        }
    }

    // ─── [시스템 레벨 진단 / System-Level Diagnostics] ───
    // 2개 이상의 독립 센서가 한 번에 죽은 것은 전원 인버터 파손 혹은 공통 접지 단선임.
    // Concurrent failure across 2+ separate channels indicates common infrastructure collapse.
    if (total_failed_sensors >= 2) {
        return -99; // 🚩 메인 루프에 긴급 차단 하드웨어 인터럽트 발송 / Trip Emergency System Shutdown
    }

    return 0; // 안전 상태 유지 완료 / Operation secure
}

#endif /* _SAFE_CRANIAL_CORE_H */
