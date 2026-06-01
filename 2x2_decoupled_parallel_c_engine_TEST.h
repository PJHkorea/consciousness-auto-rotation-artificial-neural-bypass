#ifndef _SAFE_CRANIAL_CORE_H
#define _SAFE_CRANIAL_CORE_H

#include <stdint.h>
#include <string.h> 
#include <math.h>

/* 
 * ==============================================================================
 * [🚨 컴파일러 옵션 및 저발열/초고속 핵심 지침 - 필수 준수]
 * [🚨 Compiler Options & Low-Thermal Core Guidelines - MANDATORY]
 * 
 * 1. 컴파일러 금지 옵션 (-ffast-math / -Ofast 절대 사용 금지!)
 *    - 이 옵션을 켜면 `raw_input != raw_input` (NaN 검출 가드)가 통째로 삭제됩니다.
 *    - 반드시 IEEE 754 표준을 준수하는 `-O2` 또는 `-O3` 표준 최적화만 사용하십시오.
 * 
 * 1. Forbidden Compiler Options (NEVER USE -ffast-math / -Ofast!)
 *    - Enabling these deletes the `raw_input != raw_input` (NaN guard) statement.
 *    - Ensure you strictly use standard compliance optimizations like `-O2` or `-O3`.
 * 
 * 2. 싼 칩(저가형 MCU) 포팅 시 저발열 유지 지침
 *    - 만약 포팅 후 [칩 발열] 또는 [루프 타이밍 밀림]이 발생한다면 아래 사항만 일괄 치환하십시오.
 *      👉 `double` -> `float` / `1e10` -> `1e7f` / 상수를 모두 `f` 리터럴로 일괄 치환
 * 
 * 2. Low-Thermal Guidelines for Low-Cost MCU Porting
 *    - If you experience [overheating] or [timing lag], perform a global replace:
 *      👉 Replace `double` -> `float` / `1e10` -> `1e7f` / Append `f` to constants.
 * 
 * 3. 물리적 위치 불량 및 시스템 전체 고장 진단 기능
 *    - 개별 센서 연속 10회 부활 실패 시: `-1` 리턴 (센서 위치 불량 / 단선 판정)
 *    - 배치 루프 내 동시 2개 이상 채널 고장 시: `-99` 리턴 (전원 붕괴 / 접지 불량 -> E-Stop)
 * 
 * 3. Misplacement & System-Wide Failure Diagnostics
 *    - Single channel fails 10 revivals: returns `-1` (Sensor Misplacement).
 *    - Multi-channels (>= 2) fail concurrently: returns `-99` (Power Rail Collapse -> E-Stop).
 * ==============================================================================
 */

/* ──────────────────────────────────────────────────────────────────────────
 * [설정 상수 정의 / Environment Constants Definition]
 * ────────────────────────────────────────────────────────────────────────── */
// 노이즈 감지 후 사멸 대기 사이클 수 / Dead-time ticks before revival
#define COOL_DOWN_TICKS      500     

// 하드웨어 노이즈 임계값 (float 전환 시 1e7f) / Hardware noise upper bound
#define INPUT_NOISE_LIMIT    1e10    

// 안전 나눗셈을 위한 최소 분모 임계값 / Zero-division prevention margin
#define EPSILON_GUARD        1e-7    

// 고장으로 판단할 연속 재사멸 횟수 / Consecutive failure limit for fault
#define MAX_FAIL_THRESHOLD   10      

#define HPNT_SATURATION_NODE 3.4641016151377545

/* ──────────────────────────────────────────────────────────────────────────
 * [행렬 프리 SoA 구조체 정의 - 가비지 컬렉션 원천 차단]
 * [Matrix-Free SoA Structure - Zero Runtime Garbage Collection]
 * ────────────────────────────────────────────────────────────────────────── */
typedef struct {
    /* [Matrix-Free SoA Parallel Memory Subspaces / 행렬 제거형 평행 메모리 소공간] */
    double* __restrict p00;
    double* __restrict p01;
    double* __restrict p11;
    double* __restrict x0;
    double* __restrict x1;
    
    /* [Stable Backups for Kinematic Actuator Continuity / 제어 연속성을 위한 안정 백업] */
    double* __restrict b_p00;
    double* __restrict b_p01;
    double* __restrict b_p11;
    double* __restrict b_x0;
    double* __restrict b_x1;
    double* __restrict b_out_state;
    
    /* [제어 및 고장 진단 플래그 배열 / Control & Diagnostic Flag Arrays] */
    int32_t* __restrict is_initialized; // 초기화 여부 플래그 / Initialization state
    int32_t* __restrict is_alive;       // 활성화 여부 (1=정상, 0=격리) / Status (1=Alive, 0=Isolated)
    uint32_t* __restrict dead_time;     // 격리 후 경과 시간 / Cooldown elapsed tick counter
    int32_t* __restrict fail_count;     // 연속 부활 실패 카운터 / Consecutive failure tracker
} HPNTMultiChannelState;

#endif /* _SAFE_CRANIAL_CORE_H (1부 끝 / Continued in Part 2) */
/* ──────────────────────────────────────────────────────────────────────────
 * [코어 루프 1단계: 격리 제어 및 시스템 예측 연산]
 * [Core Loop Phase 1: Isolation Control & System Prediction]
 * ────────────────────────────────────────────────────────────────────────── */
/**
 * @brief  단일 센서 채널의 상태 전개 및 실시간 노이즈 격리 처리
 *         Executes state expansion and real-time noise isolation per channel.
 * @return  1: 트리거 활성화 / Trigger Activated
 *          0: 정상 처리 또는 현재 노이즈 격리 대기 중 / Normal operation or isolated
 *         -1: 🚨 10회 연속 부활 즉시 재사멸 (위치 불량 고장) / Hardware Fault
 */
static inline int hpnt_execute_channel_step_indexed(
    int ch,
    const double* __restrict input_signals,
    HPNTMultiChannelState* __restrict states,
    const double cos_t,
    const double sin_t,
    const double q_noise,
    const double r_noise,
    const double lambda_val,
    const double theta_gate,
    double* __restrict out_probabilities
) {
    // 0. 정적 메모리 초기화 / Static Memory Initialization
    if (!states->is_initialized[ch]) {
        states->b_p00[ch] = states->p00[ch]; 
        states->b_p01[ch] = states->p01[ch]; 
        states->b_p11[ch] = states->p11[ch];
        states->b_x0[ch] = states->x0[ch];   
        states->b_x1[ch] = states->x1[ch];   
        states->b_out_state[ch] = 0.0;
        states->is_alive[ch] = 1;
        states->dead_time[ch] = 0;
        states->fail_count[ch] = 0;
        states->is_initialized[ch] = 1;
    }

    // ─── [규칙 1] 격리(사멸) 상태 검사 및 복구 (발열 스파이크 차단) ───
    // ─── [Rule 1] Isolation Status Check & Cooldown Recovery ───
    if (!states->is_alive[ch]) {
        states->dead_time[ch]++;
        if (states->dead_time[ch] > COOL_DOWN_TICKS) {
            
            // 부활 진입 시 실패 카운터 우선 누적 / Increment fault tracker
            states->fail_count[ch]++; 
            
            // 연속 10번 부활 즉시 죽었다면 -> 하드웨어 센서 부착 위치 불량 고장 판정
            // If it fails 10 times consecutively right after revival -> Fault Detected
            if (states->fail_count[ch] >= MAX_FAIL_THRESHOLD) {
                out_probabilities[ch] = 0.0;
                return -1; // 🚩 하드웨어 고장 알람 신호 송출
            }

            // 이번 루프는 안전 기저선 '부팅'만 수행하고 탈출 (부하 분산 -> 저발열)
            // This loop cycle ONLY resets baseline to bypass heavy math (Low thermal)
            states->x0[ch] = 0.0;   states->x1[ch] = 0.0;
            states->p00[ch] = 10.0; states->p11[ch] = 10.0; states->p01[ch] = 0.0;
            states->b_p00[ch] = 10.0; states->b_p11[ch] = 10.0; states->b_p01[ch] = 0.0;
            states->b_x0[ch] = 0.0;   states->b_x1[ch] = 0.0;
            states->b_out_state[ch] = 0.0;
            
            states->is_alive[ch] = 1;
            states->dead_time[ch] = 0;
            out_probabilities[ch] = 0.0;
            return 0; 
        } else {
            // 격리 기간 중에는 연산을 전면 중지하여 물리 발열 차단
            out_probabilities[ch] = 0.0; 
            return 0; 
        }
    }

    // ─── [규칙 2] 입력 신호 실시간 노이즈 격리 ───
    // ─── [Rule 2] Real-Time Input Signal Noise Isolation ───
    double raw_input = input_signals[ch];
    // NaN 검출 및 하드 바운더리 검증 통합 (지워지지 않는 안전 가드)
    if (raw_input != raw_input || 
        raw_input > INPUT_NOISE_LIMIT || 
        raw_input < -INPUT_NOISE_LIMIT) {
        states->is_alive[ch] = 0; // 즉시 사멸 / Kill channel instantly
        states->dead_time[ch] = 0;
        out_probabilities[ch] = 0.0;
        return 0; // 하단 연산 진입 전 차단 / Short-circuit
    }

    // 노이즈 가드를 정상 통과한 '진짜 정상 신호'이므로 연속 실패 카운트 리셋
    states->fail_count[ch] = 0; 

    // 1. Matrix-Free 스칼라 회전 전개 / Subspace State Rotation
    double x0_pred = cos_t * states->x0[ch] - sin_t * states->x1[ch];
    double x1_pred = sin_t * states->x0[ch] + cos_t * states->x1[ch];

    double cos_sq  = cos_t * cos_t;
    double sin_sq  = sin_t * sin_t;
    double cos_sin = cos_t * sin_t;

    // 2. Prior Error Covariance Scalar Expansion / 오차 공분산 전개
    double p00_m = (cos_sq * states->p00[ch]) - 
                   (2.0 * cos_sin * states->p01[ch]) + 
                   (sin_sq * states->p11[ch]) + q_noise;
    double p01_m = (cos_sin * (states->p00[ch] - states->p11[ch])) + 
                   ((cos_sq - sin_sq) * states->p01[ch]);
    double p11_m = (sin_sq * states->p00[ch]) + 
                   (2.0 * cos_sin * states->p01[ch]) + 
                   (cos_sq * states->p11[ch]) + q_noise;

    if (p00_m < 1e-9) p00_m = 1e-9;
    if (p11_m < 1e-9) p11_m = 1e-9;

    double p_prod_m   = p00_m * p11_m;
    double p01_m_sq   = p01_m * p01_m;
    if (p01_m_sq > p_prod_m) {
        p01_m = p01_m * 0.95; 
    }

    // 3. Innovation Covariance Singularity Guard (저가형 칩 나눗셈 예외 가드)
    double innov_cov = p00_m + r_noise;
    if (innov_cov <= EPSILON_GUARD) { 
        states->x0[ch] = x0_pred; states->x1[ch] = x1_pred;
        states->p00[ch] = p00_m;  states->p01[ch] = p01_m; states->p11[ch] = p11_m;
        out_probabilities[ch] = states->b_out_state[ch];
        return (out_probabilities[ch] > 0.75) ? 1 : 0;
    }
    
    double S_inv = 1.0 / innov_cov;
    double k0 = p00_m * S_inv;
    double k1 = p01_m * S_inv;
    double one_minus_k0 = 1.0 - k0;

    // 4. Symmetric Joseph Form Covariance Update
    double p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise);
    double p01_new = one_minus_k0 * (p01_m - k1 * p00_m) + (k0 * k1 * r_noise);
    double p11_new = p11_m - (2.0 * k1 * p01_m) + (k0 * k1 * p01_m) + 
                     (k1 * k1 * p00_m) + (k1 * k1 * r_noise);

    if (p00_new < 1e-9) p00_new = 1e-9;
    if (p11_new < 1e-9) p11_new = 1e-9;

    double p_prod = p00_new * p11_new;
    double p01_new_sq = p01_new * p01_new;
    if (p01_new_sq > p_prod) {
        p01_new = p01_new * 0.95;
    }

    // 5. Posterior State Update / 사후 상태 업데이트
    double innovation = raw_input - x0_pred;
    double x0_new = x0_pred + k0 * innovation;
    double x1_new = x1_pred + k1 * innovation;

    // 최종 연산 내부 오염 발생 시 방어선 / Internal mathematical pollution guard
    if (x0_new != x0_new || x1_new != x1_new || p00_new != p00_new || 
        x0_new > INPUT_NOISE_LIMIT || x0_new < -INPUT_NOISE_LIMIT) {
        states->is_alive[ch] = 0; 
        states->dead_time[ch] = 0;
        out_probabilities[ch] = 0.0;
        return 0;
    }

// 2-1부 마침. 하단에서 2-2부(확률 매핑 및 배치 루프)로 이어집니다.
    /* ──────────────────────────────────────────────────────────────────────────
     * [코어 루프 2단계: 확률 변환 및 상태 커밋]
     * [Core Loop Phase 2: Probability Mapping & State Commit]
     * ────────────────────────────────────────────────────────────────────────── */
    // 6. Zero-Baseline Hyper-Sigmoid Mapping via Padé Approximant (제곱 도메인 수축 가드)
    // 6. Zero-Baseline Hyper-Sigmoid Mapping via Padé Approximant (Bypasses heavy sqrt)
    double energy = (x0_new * x0_new) + (x1_new * x1_new);
    double scaled_energy = lambda_val * energy;
    double raw_prob = 0.0;

    if (scaled_energy > 0.0 && scaled_energy == scaled_energy) { 
        double x = scaled_energy;
        if (x >= HPNT_SATURATION_NODE) {
            raw_prob = 1.0;
        } else {
            double num = 6.928203230275509 * x;
            double den = 12.0 + (x * x);
            raw_prob = num / den;
            if (raw_prob > 1.0) raw_prob = 1.0;
        }
    }

    // 7. Dynamic Actuator Interface Linear Space Mapping / 액추에이터 인터페이스 매핑
    double local_theta = (theta_gate < 0.999) ? theta_gate : 0.999;
    if (raw_prob < local_theta) {
        out_probabilities[ch] = 0.0;
    } else {
        out_probabilities[ch] = (raw_prob - local_theta) / (1.0 - local_theta);
    }

    // 데이터 최종 메모리 할당 커밋 / Commit mathematical transitions into memory arrays
    states->p00[ch] = p00_new;  states->p01[ch] = p01_new;  states->p11[ch] = p11_new;
    states->x0[ch]  = x0_new;   states->x1[ch]  = x1_new;
    
    states->b_p00[ch] = p00_new; states->b_p01[ch] = p01_new; states->b_p11[ch] = p11_new;
    states->b_x0[ch]  = x0_new;  states->b_x1[ch]  = x1_new;
    states->b_out_state[ch] = out_probabilities[ch];

    return (out_probabilities[ch] > 0.75) ? 1 : 0;
}

/* ──────────────────────────────────────────────────────────────────────────
 * [배치 파이프라인: 다채널 수집 및 시스템 통합 진단 함수]
 * [Batch Pipeline: Multi-Channel Execution & System-Wide Diagnosis]
 * ────────────────────────────────────────────────────────────────────────── */
/**
 * @brief   정해진 개수의 센서 채널을 일괄 병렬 처리하며, 전원 단/접지 붕괴를 진단함
 *          Processes multi-channels in parallel and diagnoses common power rail/GND failure.
 * @return  0: 시스템 정상 작동 / System Healthy
 *         -99: 🚨 전원/접지 공통 파괴로 인한 긴급 셧다운 필요 / Power Rail Collapse or GND Fault -> System E-Stop
 */
static inline int hpnt_process_multichannel_batch(
    int num_channels,
    const double* __restrict input_signals,
    HPNTMultiChannelState* __restrict states,
    const double* __restrict cos_t_array,
    const double* __restrict sin_t_array,
    const double q_noise,
    const double r_noise,
    const double lambda_val,
    const double theta_gate,
    double* __restrict out_probabilities,
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
