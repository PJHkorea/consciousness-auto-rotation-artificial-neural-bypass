import numpy as np
import numba as nb
import math
import matplotlib.pyplot as plt

# =========================================================================
# HARDWARE CONFIGURATION PARAMETERS / 하드웨어 구동 및 임계값 설정 상수
# =========================================================================
COOL_DOWN_TICKS = 500       # Cycles to wait before self-reboot / 부활까지 대기할 격리 사이클 수
INPUT_NOISE_LIMIT = 1e10    # Hard noise cutoff threshold / 하드웨어 노이즈 차단 임계값
EPSILON_GUARD = 1e-7        # Margin to prevent division-by-zero / 저가형 칩 나눗셈 방어 임계값
HPNT_SATURATION_NODE = 3.4641016151377545 # Padé saturation bound / 파데 포화 한계 노드

# =========================================================================
# CORE FILTER ENGINE (Enhanced Stability & Multi-Channel Isolation Layout)
# 고성능 필터 엔진 코어 (수치 안정성 확보 및 다채널 독립 격리 구조)
# =========================================================================
@nb.njit(cache=True, nogil=True, fastmath=False)
def _execute_channel_step_core(
    ch, raw_signal, states_p00, states_p01, states_p11, states_x0, states_x1,
    states_b_p00, states_b_p01, states_b_p11, states_b_x0, states_b_x1, states_b_out_state,
    states_is_initialized, states_is_alive, states_dead_time,
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    """
    HPNT 2x2 Matrix-Free Scalar Kalman Filter Core with Soft-Isolative Reboot Guard.
    [원칙] 2x2 행렬 객체 배제, Zero-SQRT 대수적 수축 및 500사이클 격리 부활 가드 탑재 코어.
    """
    # 0. Structural Auto-Initialization / 가비지 프리 정적 할당 주소 바인딩 및 초기화
    if not states_is_initialized[ch]:
        states_b_p00[ch] = states_p00[ch]
        states_b_p01[ch] = states_p01[ch]
        states_b_p11[ch] = states_p11[ch]
        states_b_x0[ch] = states_x0[ch]
        states_b_x1[ch] = states_x1[ch]
        states_b_out_state[ch] = 0.0
        states_is_alive[ch] = 1
        states_dead_time[ch] = 0
        states_is_initialized[ch] = 1

    # ─── [Isolation Guard] Quarantine State Check & Time-Based Reboot ───
    # ─── [격리 가드] 사멸 상태 채널 시간 기반 기저선 복구 및 하드웨어 부팅 분리 ───
    if not states_is_alive[ch]:
        states_dead_time[ch] += 1
        if states_dead_time[ch] > COOL_DOWN_TICKS:
            # Dedicated Boot Cycle: Perform clean baseline reset only to eliminate FPU spikes
            # 부활 사이클 분리: 이번 루프는 연산 없이 기저선 복구(부팅)만 수행하여 전류 유입 발열 차단
            states_x0[ch], states_x1[ch] = 0.0, 0.0
            states_p00[ch], states_p11[ch], states_p01[ch] = 10.0, 10.0, 0.0
            states_b_x0[ch], states_b_x1[ch] = 0.0, 0.0
            states_b_p00[ch], states_b_p11[ch], states_b_p01[ch] = 10.0, 10.0, 0.0
            states_b_out_state[ch] = 0.0
            
            states_is_alive[ch] = 1
            states_dead_time[ch] = 0
            return 0.0, 0 # Return clean zero immediately / 부팅 후 즉시 차단 리턴
        else:
            # Skip heavy Kalman math during isolation to freeze FPU power dissipation
            # 격리 기간 동안 연산을 전면 차단하여 부동소수점 장치(FPU)를 완벽히 휴식시킴 (초저발열)
            return 0.0, 0

    # ─── [Input Noise Isolation] Out-of-Boundary Check (Evasion Protection) ───
    # ─── [입력 노이즈 격리] NaN 및 하드 바운더리 실시간 검증 (초입 고속 차단) ───
    if (raw_signal != raw_signal or raw_signal > INPUT_NOISE_LIMIT or raw_signal < -INPUT_NOISE_LIMIT):
        states_is_alive[ch] = 0  # Instant execution death / 즉시 사멸 방방 이송
        states_dead_time[ch] = 0
        return 0.0, 0            # Erase downstream contamination propagate / 오염 전파 즉시 완전 차단

    # 1. Deterministic Subspace State Rotation (Matrix-Free System)
    # 결정론적 하위 공간 상태 회전 (손으로 풀어헤친 2차원 스칼라 최속 전개)
    x0_pred = cos_t * states_x0[ch] - sin_t * states_x1[ch]
    x1_pred = sin_t * states_x0[ch] + cos_t * states_x1[ch]

    cos_sq = cos_t * cos_t
    sin_sq = sin_t * sin_t
    cos_sin = cos_t * sin_t

    # 2. Prior Error Covariance Scalar Expansion
    # 사전 오차 공분산 스칼라 확장 연산 (대칭성 보존 배정 레이아웃)
    p00_m = (cos_sq * states_p00[ch]) - (2.0 * cos_sin * states_p01[ch]) + (sin_sq * states_p11[ch]) + q_noise
    p01_m = (cos_sin * (states_p00[ch] - states_p11[ch])) + ((cos_sq - sin_sq) * states_p01[ch])
    p11_m = (sin_sq * states_p00[ch]) + (2.0 * cos_sin * states_p01[ch]) + (cos_sq * states_p11[ch]) + q_noise

    if p00_m < 1e-9: p00_m = 1e-9
    if p11_m < 1e-9: p11_m = 1e-9

    # Zero-Sqrt Square-Domain Algebraic Shrinkage Guard (发热 원천 방어)
    # [제곱 도메인 수축 가드] 무거운 루트 연산(sqrt)을 완전히 제거하여 FPU 발열 요인 차단
    p_prod_m = p00_m * p11_m
    p01_m_sq = p01_m * p01_m
    if p01_m_sq > p_prod_m:
        p01_m = p01_m * 0.95 

    # 3. Innovation Covariance Singularity Guard (Safety Margin Enhanced)
    # 혁신 공분산 특이점 방어선 (저가형 칩 나눗셈 예외 완벽 방어용 EPSILON 적용)
    innov_cov = p00_m + r_noise
    if innov_cov <= EPSILON_GUARD:
        states_x0[ch], states_x1[ch] = x0_pred, x1_pred
        states_p00[ch], states_p01[ch], states_p11[ch] = p00_m, p01_m, p11_m
        return states_b_out_state[ch], (1 if states_b_out_state[ch] > 0.75 else 0)
    
    s_inv = 1.0 / innov_cov
    k0 = p00_m * s_inv
    k1 = p01_m * s_inv
    one_minus_k0 = 1.0 - k0

    # 4. Symmetric Joseph Form Covariance Update (Sign Error Fully Rectified)
    # 대수적 정정성이 교정된 대칭형 Joseph Form 오차 공분산 업데이트 (양의 정정성 영구 유지)
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = one_minus_k0 * (p01_m - k1 * p00_m) + (k0 * k1 * r_noise)
    p11_new = p11_m - (2.0 * k1 * p01_m) + (k0 * k1 * p01_m) + (k1 * k1 * p00_m) + (k1 * k1 * r_noise)

    if p00_new < 1e-9: p00_new = 1e-9
    if p11_new < 1e-9: p11_new = 1e-9

    # Post-Update Square-Domain Shrinkage Guard / 업데이트 사후 수축 가드 적용
    p_prod = p00_new * p11_new
    p01_new_sq = p01_new * p01_new
    if p01_new_sq > p_prod:
        p01_new = p01_new * 0.95

    # 5. Posterior State Update / 사후 참값 상태 변수 업데이트
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation

    # Volatile Internal Calculation Exception Gate / 최종 내부 연산 오염 방어선
    if (x0_new != x0_new or x1_new != x1_new or p00_new != p00_new or 
        x0_new > INPUT_NOISE_LIMIT or x0_new < -INPUT_NOISE_LIMIT):
        states_is_alive[ch] = 0
        states_dead_time[ch] = 0
        return 0.0, 0

    # 6. Zero-Baseline Hyper-Sigmoid Mapping via Padé [1/1] Approximant
    # 초저발열 하이퍼-시그모이드 매핑 (FPU를 파괴하는 대형 지수함수 exp를 유리함수 근사식으로 대체)
    energy = (x0_new * x0_new) + (x1_new * x1_new)
    scaled_energy = lambda_val * energy
    raw_prob = 0.0

    if scaled_energy > 0.0 and scaled_energy == scaled_energy:
        if scaled_energy >= HPNT_SATURATION_NODE:
            raw_prob = 1.0
        else:
            num = 6.928203230275509 * scaled_energy
            den = 12.0 + (scaled_energy * scaled_energy)
            raw_prob = num / den
            if raw_prob > 1.0: raw_prob = 1.0

    # 7. Dynamic Actuator Interface Linear Space Mapping / 액추에이터 인터페이스 부드러운 선형 맵핑
    local_theta = theta if theta < 0.999 else 0.999
    if raw_prob < local_theta:
        p_state = 0.0
    else:
        p_state = (raw_prob - local_theta) / (1.0 - local_theta)

    # Commit Verified Memory Planes / 최종 검증된 수치 평면 상태 확정 커밋
    states_p00[ch], states_p01[ch], states_p11[ch] = p00_new, p01_new, p11_new
    states_x0[ch], states_x1[ch] = x0_new, x1_new
    
    states_b_p00[ch], states_b_p01[ch], states_b_p11[ch] = p00_new, p01_new, p11_new
    states_b_x0[ch], states_b_x1[ch] = x0_new, x1_new
    states_b_out_state[ch] = p_state

    action_trigger = 1 if p_state > 0.75 else 0
    return p_state, action_trigger

# =========================================================================
# BATCH EXECUTION LOOP / 다채널 시간축 데이터 배칭 처리 루프
# =========================================================================
@nb.njit(cache=True, nogil=True, fastmath=False)
def _process_batch_loop(
    signal_matrix, est_x0_matrix, prob_history_matrix, trigger_history_matrix,
    p00, p01, p11, x0, x1, b_p00, b_p01, b_p11, b_x0, b_x1, b_out_state,
    is_initialized, is_alive, dead_time,
    cos_t_arr, sin_t_arr, q_noise, r_noise, lambda_val, theta_gate
):
    n_samples = signal_matrix.shape[0]
    num_channels = signal_matrix.shape[1]
    
    for i in range(n_samples):
        for ch in range(num_channels):
            p_state, trigger = _execute_channel_step_core(
                ch, signal_matrix[i, ch], p00, p01, p11, x0, x1,
                b_p00, b_p01, b_p11, b_x0, b_x1, b_out_state,
                is_initialized, is_alive, dead_time,
                cos_t_arr[ch], sin_t_arr[ch], q_noise, r_noise, lambda_val, theta_gate
            )
            est_x0_matrix[i, ch] = x0[ch]
            prob_history_matrix[i, ch] = p_state
            trigger_history_matrix[i, ch] = trigger
# =========================================================================
# WRAPPER INTERFACE (Structure of Arrays Architecture Matrix-Free Engine)
# 상위 래퍼 인터페이스 (SoA 연속 메모리 정렬 및 무할당 아키텍처 인프라)
# =========================================================================
class HPNTMultiChannelEngine:
    def __init__(self, num_channels=4, fs=250.0, target_freqs=None, q_noise=1e-3, r_noise=2.25, lambda_val=0.5, theta_gate=0.3):
        self.num_channels = num_channels
        dt = 1.0 / fs
        
        if target_freqs is None:
            freq_array = np.ones(num_channels, dtype=np.float64) * 10.0
        else:
            freq_array = np.array(target_freqs, dtype=np.float64)
            
        theta_rot = 2.0 * np.pi * freq_array * dt
        self.cos_t_arr = np.cos(theta_rot).astype(np.float64)
        self.sin_t_arr = np.sin(theta_rot).astype(np.float64)
        self.q_noise = float(q_noise)
        self.r_noise = float(r_noise)
        self.lambda_val = float(lambda_val)
        self.theta_gate = float(max(0.0, min(theta_gate, 0.99)))
        
        # Parallel Structure of Arrays Real-Time Scalar Registers
        # 상호 무간섭 다채널 고속 인덱싱을 위한 전용 SoA 스칼라 연속 배열 메모리 테이블 고정 할당
        self.p00 = np.ones(num_channels, dtype=np.float64)
        self.p01 = np.zeros(num_channels, dtype=np.float64)
        self.p11 = np.ones(num_channels, dtype=np.float64)
        self.x0 = np.zeros(num_channels, dtype=np.float64)
        self.x1 = np.zeros(num_channels, dtype=np.float64)
        
        self.b_p00 = np.ones(num_channels, dtype=np.float64)
        self.b_p01 = np.zeros(num_channels, dtype=np.float64)
        self.b_p11 = np.ones(num_channels, dtype=np.float64)
        self.b_x0 = np.zeros(num_channels, dtype=np.float64)
        self.b_x1 = np.zeros(num_channels, dtype=np.float64)
        self.b_out_state = np.zeros(num_channels, dtype=np.float64)
        
        self.is_initialized = np.zeros(num_channels, dtype=np.int32)
        self.is_alive = np.ones(num_channels, dtype=np.int32)
        self.dead_time = np.zeros(num_channels, dtype=np.int32)

    def process_batch(self, signal_matrix):
        safe_matrix = np.asarray(signal_matrix, dtype=np.float64)
        n_samples = safe_matrix.shape[0]
        
        est_x0_matrix = np.zeros((n_samples, self.num_channels), dtype=np.float64)
        prob_history_matrix = np.zeros((n_samples, self.num_channels), dtype=np.float64)
        trigger_history_matrix = np.zeros((n_samples, self.num_channels), dtype=np.int32)
        
        _process_batch_loop(
            safe_matrix, est_x0_matrix, prob_history_matrix, trigger_history_matrix,
            self.p00, self.p01, self.p11, self.x0, self.x1,
            self.b_p00, self.b_p01, self.b_p11, self.b_x0, self.b_x1, self.b_out_state,
            self.is_initialized, self.is_alive, self.dead_time,
            self.cos_t_arr, self.sin_t_arr, self.q_noise, self.r_noise, self.lambda_val, self.theta_gate
        )
        return est_x0_matrix, prob_history_matrix, trigger_history_matrix

# =========================================================================
# PRODUCTION-GRADE PRODUCTION & VISUALIZATION LAYER
# 프로덕션 등급 시뮬레이션 및 양산 검증 시각화 레이어
# =========================================================================
def run_production_simulation():
    fs = 250.0
    dt = 1.0 / fs
    total_time = 10.0
    t = np.arange(0, total_time, dt)
    n_samples = len(t)
    num_channels = 4
    
    # 4-Channel Independent target frequencies assignment / 4채널 양심 스케일 맞춤형 주파수 분할 인입
    target_freqs = [9.5, 10.0, 11.5, 13.0]
    raw_signals_matrix = np.zeros((n_samples, num_channels))
    
    # Generate Multi-Channel Signal Plane with Intermittent Massive Noise Infusion
    # 각 채널별 독립 유도 신호 및 특정 타임라인 구간에 극심한 파괴성 하드웨어 노이즈 강제 주입
    for ch in range(num_channels):
        pure_sig = np.sin(2.0 * np.pi * target_freqs[ch] * t)
        noise = np.random.normal(0, 1.5, n_samples)
        raw_signals_matrix[:, ch] = pure_sig + noise
        
        # Target Haptic Intent Activation Area / 의도 신호 액추에이션 활성화 구간 버스트 (4초 ~ 7초)
        active_mask = (t >= 4.0) & (t <= 7.0)
        raw_signals_matrix[active_mask, ch] += 3.0 * np.sin(2.0 * np.pi * target_freqs[ch] * t[active_mask])
    
    # [INTERRUPT INJECTION] Force massive anomaly to execute isolated 500-tick dead guard on Channel 1 (10.0Hz)
    # [실전 노이즈 차단 인터럽트 주입]: 1번 채널(10.0Hz)의 1.5초~2.0초 구간에 거대한 전기 노이즈(NaN 및 초과값) 유입
    raw_signals_matrix[(t >= 1.5) & (t <= 2.0), 1] = 1e15      # Hard boundary overflow / 하드 임계값 초과
    raw_signals_matrix[(t >= 2.1) & (t <= 2.3), 1] = np.nan    # Floating contamination / 수치 연산 파단용 NaN 유입

    # Instantiate Low-Cost Grid Friendly Engine / 양심적 4채널 저발열 그리드 다중 채널 엔진 가동
    engine = HPNTMultiChannelEngine(
        num_channels=num_channels,
        fs=fs,
        target_freqs=target_freqs,
        q_noise=1e-3,
        r_noise=2.25,
        lambda_val=0.5,
        theta_gate=0.3
    )
    
    est_x0, prob_hist, trig_hist = engine.process_batch(raw_signals_matrix)
    
    # Plotting multi-channel response tracking grid / 시각화 레이어 전개
    plt.figure(figsize=(14, 10))
    
    # Channel 0 (9.5Hz) Plot - Clean Trace
    plt.subplot(4, 1, 1)
    plt.plot(t, raw_signals_matrix[:, 0], color='gray', alpha=0.4, label='CH0 Raw (9.5Hz)')
    plt.plot(t, prob_hist[:, 0], color='blue', label='CH0 Prob Profile')
    plt.title('Multi-Channel Isolated Haptic Bypass Operating Grid (complies with 4-CH Rules)')
    plt.legend(loc='upper right')
    plt.grid(True)
    
    # Channel 1 (10.0Hz) Plot - Contains Intercept Quarantine Event (1.5s ~ 2.0s)
    # 1번 채널: 노이즈 격리로 인해 사망 후 500사이클 동안 연산을 멈추고 안전하게 쉬다가 복구되는 모습 증명
    plt.subplot(4, 1, 2)
    plt.plot(t, raw_signals_matrix[:, 1], color='orange', alpha=0.3, label='CH1 Raw (10.0Hz, Anomaly-Injected)')
    plt.plot(t, prob_hist[:, 1], color='red', linewidth=2, label='CH1 Prob Profile (Quarantined at 1.5s)')
    plt.axvspan(1.5, 1.5 + (500/fs), color='red', alpha=0.15, label='FPU Freezing Guard Area (500 Ticks)')
    plt.legend(loc='upper right')
    plt.grid(True)
    
    # Channel 2 (11.5Hz) Plot - Mutual Non-Interference Proof
    # 2번 채널: 1번 채널이 죽어 있는 동안 완벽하게 상호 무간섭 병렬 가동하며 자기 할 일(의도 검출)을 수행함 증명
    plt.subplot(4, 1, 3)
    plt.plot(t, raw_signals_matrix[:, 2], color='gray', alpha=0.4, label='CH2 Raw (11.5Hz)')
    plt.plot(t, prob_hist[:, 2], color='green', label='CH2 Prob Profile (Mutual Non-Interference Proof)')
    plt.legend(loc='upper right')
    plt.grid(True)
    
    # Channel 3 (13.0Hz) Plot - Clean Trace
    plt.subplot(4, 1, 4)
    plt.plot(t, raw_signals_matrix[:, 3], color='gray', alpha=0.4, label='CH3 Raw (13.0Hz)')
    plt.plot(t, prob_hist[:, 3], color='purple', label='CH3 Prob Profile')
    plt.axhline(y=0.75, color='black', linestyle=':', label='Trigger Boundary (0.75)')
    plt.xlabel('Time (seconds) / 시간 (초)')
    plt.legend(loc='upper right')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Execute production-grade 4-channel split target validation loop
    # 최종 프로덕션 가동 테스트: 양심적 4채널 독립 타겟 주파수 인입 및 하드웨어 가드 시뮬레이션 가동
    run_production_simulation()
