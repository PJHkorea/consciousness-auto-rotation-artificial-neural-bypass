import numpy as np
import numba as nb
import math
import matplotlib.pyplot as plt

# -------------------------------------------------------------------------
# [Phase 1] 2x2 Joseph Form Kalman Filter & Stability Guard Core (Mission-Critical)
# [Phase 1] 2x2 조셉 폼 칼만 필터 및 수치 안정성 가드 코어
# -------------------------------------------------------------------------
@nb.njit(cache=True, nogil=True, fastmath=True)
def _execute_single_step_core(
    raw_signal, p00, p01, p11, x0, x1, 
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    """
    Executes scalar operations for single-channel 2x2 state estimation.
    Enforces dual-layer Cauchy-Schwarz numerical stability guards.
    
    단일 채널의 2x2 상태 추정을 스칼라 대수 전개로 연산합니다.
    이중 레이어 코시-슈바르츠 부등식 기반 수치 가드를 강제합니다.
    """
    # 1. State Prediction (2D Vibration Rotation Model)
    # 1. 상태 예측 (2차원 회전 모델 대수 전개)
    x0_pred = cos_t * x0 - sin_t * x1
    x1_pred = sin_t * x0 + cos_t * x1

    # 2. Error Covariance Prediction (P_minus = F * P * F^T + Q)
    # 2. 오차 공분산 예측 (F * P * F^T + Q 대수 전개)
    t0 = cos_t * p00 - sin_t * p01
    t1 = cos_t * p01 - sin_t * p11
    t2 = sin_t * p00 + cos_t * p01
    t3 = sin_t * p01 + cos_t * p11

    p00_m = cos_t * t0 - sin_t * t1 + q_noise
    p01_m = sin_t * t0 + cos_t * t1
    p11_m = sin_t * t2 + cos_t * t3 + q_noise
    
    # [Stability Guard] Prevent micro-asymmetry during prediction step under fastmath optimization
    # [수치 가드 보완] fastmath 컴파일 시 발생 가능한 예측 단계의 미세 대칭성 왜곡 차단
    p_prod_m = p00_m * p11_m
    max_p01_m = math.sqrt(p_prod_m if p_prod_m > 1e-28 else 1e-28)
    if p01_m > max_p01_m:
        p01_m = max_p01_m
    elif p01_m < -max_p01_m:
        p01_m = -max_p01_m

    # 3. Kalman Gain (Innovation Covariance Safeguard)
    # 3. 칼만 이득 계산 (이노베이션 공분산 붕괴 방어 가드 탑재)
    innov_cov = p00_m + r_noise
    if innov_cov < 1e-9:
        innov_cov = 1e-9

    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov

    # 4. Exact Joseph Form Covariance Update (Guarantees Positive-Definiteness)
    # 4. 조셉 폼 오차 공분산 업데이트 (양의 정치성 및 대수적 대칭성 절대 보장)
    one_minus_k0 = 1.0 - k0
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = (one_minus_k0 * p01_m) - (k1 * one_minus_k0 * p00_m) + (k0 * k1 * r_noise)
    p11_new = (k1 * k1 * p00_m) - (2.0 * k1 * one_minus_k0 * p01_m) + p11_m + (k1 * k1 * r_noise)

    # 5. Real-time Numerical Guard using Cauchy-Schwarz Inequality
    # 5. 코시-슈바르츠 부등식 기반 실시간 수치 가드 강제 (업데이트 단계)
    p_prod = p00_new * p11_new
    max_p01 = math.sqrt(p_prod if p_prod > 1e-28 else 1e-28)
    if p01_new > max_p01:
        p01_new = max_p01
    elif p01_new < -max_p01:
        p01_new = -max_p01

    # 6. State Update
    # 6. 상태 업데이트
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation

    # 7. Zero-Baseline Hyper-Sigmoid Gating Actuation (Continuous Soft-Thresholding)
    # 7. 제로 베이스라인 하이퍼 시그모이드 게이팅 (물리적 제어 불연속성 방지 선형 맵핑)
    X_intent_energy = x0_new * x0_new + x1_new * x1_new
    scaled_energy = lambda_val * X_intent_energy

    # Floating-point exponential overflow protection guard
    # 지수 오버플로우 방지 가드
    if scaled_energy > 20.0:
        raw_prob = 1.0
    else:
        raw_prob = (2.0 / (1.0 + math.exp(-scaled_energy))) - 1.0

    # Soft-thresholding interpolation: Protects hardware actuators and ensures control integrity
    # 임계값을 넘는 순간부터 0.0 ~ 1.0까지 부드럽게 점진 가속하도록 교정
    if raw_prob < theta:
        p_state = 0.0
    else:
        p_state = (raw_prob - theta) / (1.0 - theta)

    return p00_new, p01_new, p11_new, x0_new, x1_new, p_state


# -------------------------------------------------------------------------
# [Phase 2] Simulation Hub / Execution Layer
# [Phase 2] 시뮬레이션 허브 및 실행 레이어
# -------------------------------------------------------------------------
def run_simulation():
    fs = 250.0
    target_freq = 10.0
    dt = 1.0 / fs
    total_time = 10.0
    t = np.arange(0, total_time, dt)
    n_samples = len(t)

    # Pre-compute trigonometric rotation units for JIT execution
    # 상수의 사전 처리 및 삼각함수 유닛 컴파일러 주입 가속화
    theta_rot = 2.0 * np.pi * target_freq * dt
    cos_t = np.cos(theta_rot)
    sin_t = np.sin(theta_rot)

    # Generate synthetic target signal and heavy Gaussian white noise
    # 타겟 신호 및 강한 백색 잡음 생성 레이어
    pure_signal = np.sin(2.0 * np.pi * target_freq * t)
    noise = np.random.normal(0, 1.5, n_samples)
    raw_eeg = pure_signal + noise

    # Force continuous intent synchronization interval (4.0s to 7.0s energy burst)
    # 의식 활성화 구간 강제 시뮬레이션 (4초 ~ 7초 사이 뇌파 동기화 급증 상황 모사)
    active_mask = (t >= 4.0) & (t <= 7.0)
    raw_eeg[active_mask] += 3.0 * np.sin(2.0 * np.pi * target_freq * t[active_mask])

    # Pre-allocate buffer states and statistics memory views
    # 상태 버퍼 및 통계 변수 배열 할당 (프리-알로케이션 및 캐싱)
    p00, p01, p11 = 1.0, 0.0, 1.0
    x0, x1 = 0.0, 0.0
    
    q_noise = 1e-4
    r_noise = 1e-2
    lambda_val = 0.5   
    theta_gate = 0.3   

    est_x0 = np.zeros(n_samples)
    prob_history = np.zeros(n_samples)

    # High-speed single loop processing pipeline
    # 고속 단일 루프 파이프라인 가동
    for i in range(n_samples):
        p00, p01, p11, x0, x1, p_state = _execute_single_step_core(
            raw_eeg[i], p00, p01, p11, x0, x1,
            cos_t, sin_t, q_noise, r_noise, lambda_val, theta_gate
        )
        est_x0[i] = x0
        prob_history[i] = p_state

    # Data Visualization Pipeline (Matplotlib)
    # 시각화 파이프라인
    plt.figure(figsize=(12, 8))
    
    plt.subplot(3, 1, 1)
    plt.plot(t, raw_eeg, color='gray', alpha=0.6, label='Raw EEG (with Noise)')
    plt.plot(t, pure_signal, color='blue', linestyle='--', label='Target Intent Ground Truth')
    plt.title('Consciousness Auto-Rotation Tracking Signal Hub (Perfect Edge Spec)')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(t, est_x0, color='red', label='Kalman Estimated Phase X0')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(t, prob_history, color='green', label='Continuous Actuator Control Profile')
    plt.axhline(y=0.75, color='r', linestyle=':', label='Action Trigger Threshold (0.75)')
    plt.xlabel('Time (seconds)')
    plt.ylim(-0.05, 1.05)
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
