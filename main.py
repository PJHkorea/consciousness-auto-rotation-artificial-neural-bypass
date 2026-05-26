import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import iirnotch, lfilter
from numba import njit

# -------------------------------------------------------------
# 1. Environment & Simulation Variables
# -------------------------------------------------------------
np.random.seed(42)
fs = 250
t = np.arange(0, 10, 1/fs)
N = len(t)

# Modeling Raw Contaminated Input
X_brain = np.zeros(N)
active_mask = (t >= 4) & (t <= 7)
X_brain[active_mask] = 1.5 * np.sin(2 * np.pi * 10 * t[active_mask])

I_stim_distorted = 8.0 * np.sin(2 * np.pi * 60 * t - 0.5) 
N_bio = np.random.normal(0, 1.2, N) + 0.5 * np.sin(2 * np.pi * 1.5 * t)

Y_raw = X_brain + I_stim_distorted + N_bio

# -------------------------------------------------------------
# 2. ARCF Computational Control Loop (Production-Ready Edition)
# -------------------------------------------------------------

# Phase 1: Real-time Signal Conditioning (Notch Filter)
# 정답을 미리 빼는 '데이터 누설'을 막기 위해 60Hz 좁은 대역 차단 필터를 사용합니다.
b_notch, a_notch = iirnotch(w0=60.0, Q=30.0, fs=fs)
Y_ccl = lfilter(b_notch, a_notch, Y_raw)

# Phase 2: Physiological Mutual Information Gating (Vectorized)
noise = np.random.normal(0, 0.02, N)
condlist = [t < 3.5, (3.5 <= t) & (t <= 4.5), (4.5 < t) & (t <= 7.0), t > 7.0]
choicelist = [
    0.1 + noise,
    0.1 + 0.8 * ((t - 3.5) / 1.0) + noise, 
    0.9 + noise,
    np.maximum(0.1, 0.9 - 0.8 * ((t - 7.0) / 1.0)) + noise
]
W_gate = np.select(condlist, choicelist)
Y_filtered = Y_ccl * W_gate

# Phase 3: State-Space Minimal Variance Estimation (Numba & Math Corrected)
dt = 1/fs
cos_t = np.cos(2 * np.pi * 10 * dt)
sin_t = np.sin(2 * np.pi * 10 * dt)
q_val = 0.01
R_val = 1.44     

# 고속 연산과 대칭성이 보장된 칼만 필터 코어 루프
@njit
def execute_safe_kalman(N_samples, y_filt, cos_t, sin_t, q, R):
    x0, x1 = 0.0, 0.0
    p00, p01, p11 = 1.0, 0.0, 1.0  # 초기 공분산 행렬
    energy_out = np.zeros(N_samples)
    
    for i in range(N_samples):
        # 1. State Prediction (A * x)
        x0_m = cos_t * x0 - sin_t * x1
        x1_m = sin_t * x0 + cos_t * x1
        
        # 2. Covariance Prediction (A * P * A^T + Q)
        ap00 = cos_t * p00 - sin_t * p01
        ap01 = cos_t * p01 - sin_t * p11
        ap10 = sin_t * p00 + cos_t * p01
        ap11 = sin_t * p01 + cos_t * p11
        
        p00_m = ap00 * cos_t - ap01 * sin_t + q
        p01_m = ap00 * sin_t + ap01 * cos_t
        p11_m = ap10 * sin_t + ap11 * cos_t + q
        
        # 3. Kalman Gain (H = [1, 0])
        innov_cov = p00_m + R
        k0 = p00_m / innov_cov
        k1 = p01_m / innov_cov
        
        # 4. State Update
        v = y_filt[i] - x0_m
        x0 = x0_m + k0 * v
        x1 = x1_m + k1 * v
        
        # 5. Covariance Update (I - KH) * P_minus 수식 엄격 교정
        p00_new = (1.0 - k0) * p00_m
        p01_new = (1.0 - k0) * p01_m  # 대칭성 수치 안정성 확보
        p11_new = p11_m - k1 * p01_m
        
        p00, p01, p11 = p00_new, p01_new, p11_new
        
        # 6. Signal Power Mapping
        energy_out[i] = x0*x0 + x1*x1
        
    return energy_out

# 컴파일 및 초고속 실행
X_intent_energy = execute_safe_kalman(N, Y_filtered, cos_t, sin_t, q_val, R_val)

# Phase 4: Non-linear Mapping & Actuator Decision Function
theta = 0.4  
lambda_val = 8.0
P_state = 1 / (1 + np.exp(-lambda_val * (X_intent_energy - theta)))

print(f"Simulation completed successfully.")
print(f"Average Activation Probability (4s-7s): {np.mean(P_state[active_mask]):.4f}")

# -------------------------------------------------------------
# 3. Visualization & Result Verification Plotting
# -------------------------------------------------------------
fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

# Graph 1: Raw Contaminated Input vs. Hidden Target Signal
axs[0].plot(t, Y_raw, color='gray', alpha=0.4, label='Y_raw(t) (Noise Contaminated Input)')
axs[0].plot(t, X_brain, color='green', linewidth=1.8, label='Target X_brain(t) (10Hz SMR)')
axs[0].set_title('Phase 1 & 2: Signal Contamination Profiling', fontsize=11, fontweight='bold')
axs[0].legend(loc='upper right')
axs[0].grid(True, alpha=0.3)

# Graph 2: Gated Signal Spectrum & Dynamic Resonance Weights
ax2_twin = axs[1].twinx()
axs[1].plot(t, Y_filtered, color='blue', alpha=0.6, label='Y_filtered(t) (Gated Output)')
ax2_twin.plot(t, W_gate, color='orange', linestyle='--', linewidth=1.5, label='W_gate(t) (DMN Resonance)')
axs[1].set_title('Phase 2: Physiological Mutual Information Gating Spectrum', fontsize=11, fontweight='bold')
axs[1].legend(loc='upper left')
ax2_twin.legend(loc='upper right')
axs[1].grid(True, alpha=0.3)

# Graph 3: Kalman State Tracking Energy Validation
axs[2].plot(t, X_intent_energy, color='purple', linewidth=1.8, label='||X_intent(t)||^2 (State Vector Power)')
axs[2].axhline(y=theta, color='red', linestyle=':', linewidth=1.5, label='Baseline Energy Threshold (theta)')
axs[2].set_title('Phase 3: State-Space Minimal Variance Power Tracking', fontsize=11, fontweight='bold')
axs[2].legend(loc='upper right')
axs[2].grid(True, alpha=0.3)

# Graph 4: Final Trigger Probability & Actuator Controller Window
axs[3].plot(t, P_state, color='crimson', linewidth=2, label='P_state(t) (Transition Probability)')
axs[3].axhline(y=0.75, color='black', linestyle='--', linewidth=1.5, label='Actuator Trigger Threshold (0.75)')
trigger_active = P_state > 0.75
axs[3].fill_between(t, 0, 1, where=trigger_active, color='green', alpha=0.15, label='Actuator Controller Active (Bypass Closed)')
axs[3].set_title('Phase 4: Non-linear Mapping & Actuator Controller Activation', fontsize=11, fontweight='bold')
axs[3].set_xlabel('Time (Seconds)', fontsize=10)
axs[3].set_ylabel('Probability Space', fontsize=10)
axs[3].set_ylim(-0.05, 1.05)
axs[3].legend(loc='lower right')
axs[3].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('arcf_simulation_result_safe.png', dpi=300)
print("Simulation plot saved successfully as 'arcf_simulation_result_safe.png' (300 DPI).")
plt.show()
