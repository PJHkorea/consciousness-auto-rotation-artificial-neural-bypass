import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import iirnotch, freqz
import math
from numba import njit

# =============================================================
# 1. Environment & Simulation Variables (10s, 250Hz sampling)
# =============================================================
np.random.seed(42)
fs = 250
dt = 1 / fs
t = np.arange(0, 10, dt)
N = len(t)

# Modeling Raw Contaminated Input
X_brain = np.zeros(N)
active_mask = (t >= 4) & (t <= 7)
X_brain[active_mask] = 1.5 * np.sin(2 * np.pi * 10 * t[active_mask])  # 10Hz Target SMR Signal

I_stim_distorted = 8.0 * np.sin(2 * np.pi * 60 * t - 0.5)  # 60Hz Powerline Interference
N_bio = np.random.normal(0, 1.2, N) + 0.5 * np.sin(2 * np.pi * 1.5 * t)  # Low-freq drift & Noise

Y_raw = X_brain + I_stim_distorted + N_bio

# =============================================================
# 2. Filter Coefficients & Analytical Phase Calibration
# =============================================================
b_notch, a_notch = iirnotch(w0=60.0, Q=30.0, fs=fs)

# [Phase Compensation] Extract exact analytical phase delay introduced by the notch filter at the tracking target frequency (10Hz)
w_target = 10.0  
w_vec, h_vec = freqz(b_notch, a_notch, worand=[w_target], fs=fs)
phase_delay = float(np.angle(h_vec[0]))  

# Digital domain angular rotation calculation embedded with phase delay feed-forward correction
w_rad = 2.0 * np.pi * w_target
cos_t = np.cos(w_rad * dt + phase_delay)
sin_t = np.sin(w_rad * dt + phase_delay)

q_val = 0.08  # Process Noise Covariance
R_val = 1.20  # Measurement Noise Covariance

# =============================================================
# 3. ARCF Computational Control Loop (Strictly Causal Real-Time Integration)
# =============================================================
# fastmath is set to False to enforce absolute floating-point precision stability under IEEE 754
@njit(cache=True, nogil=True, fastmath=False)
def execute_realtime_kalman_causal_fixed(y_raw, b, a, cos_t, sin_t, q, R, energy_out, y_filt_out):
    N_samples = len(y_raw)
    if N_samples == 0:
        return
        
    cos_t_f = float(cos_t)
    sin_t_f = float(sin_t)
    q_f = float(q)
    R_f = float(R)
    
    # State variables allocation
    x0, x1 = 0.0, 0.0
    p00, p01, p11 = 2.0, 0.0, 2.0  
    
    # Pre-allocating structural trigonometric constants
    cos_sq = cos_t_f * cos_t_f
    sin_sq = sin_t_f * sin_t_f
    two_cos_sin = 2.0 * cos_t_f * sin_t_f
    cos_sq_minus_sin_sq = cos_sq - sin_sq
    cos_sin = cos_t_f * sin_t_f
    
    # [True Causality] Statically allocated delay registers for IIR Direct Form II structure
    v1, v2 = 0.0, 0.0
    
    running_energy = 0.0
    ema_alpha = 0.08  
    
    for i in range(N_samples):
        # 3.1. Phase 1: Inline IIR Notch Filtering (Referencing only causal historical states)
        x_in = y_raw[i]
        y_notch = b[0] * x_in + v1
        v1 = b[1] * x_in - a[1] * y_notch + v2
        v2 = b[2] * x_in - a[2] * y_notch
        
        # 3.2. Phase 2: Causal Real-time Moving-Average Information Gating
        inst_energy = y_notch * y_notch
        if i == 0:
            running_energy = inst_energy
        else:
            running_energy = (1.0 - ema_alpha) * running_energy + ema_alpha * inst_energy
        
        # Continuous sigmoid scaling triggered by real-time energy synchronization
        gate_base = 1.0 / (1.0 + math.exp(-2.5 * (running_energy - 0.8)))
        w_gate = 0.1 + gate_base * 0.9
        
        # Hard Operational Operational Guard against transient spikes
        if w_gate < 0.1:
            w_gate = 0.1
        elif w_gate > 1.0:
            w_gate = 1.0
            
        y_filt = y_notch * w_gate
        y_filt_out[i] = y_filt  
        
        # 3.3. Phase 3: Analytical State Vector Prediction (Standard Harmonic Rotation)
        x0_m =  cos_t_f * x0 + sin_t_f * x1
        x1_m = -sin_t_f * x0 + cos_t_f * x1
        
        # Analytical Covariance Prediction: P_m = A * P * A^T + Q
        p00_m = cos_sq * p00 + two_cos_sin * p01 + sin_sq * p11 + q_f
        p01_m = -cos_sin * p00 + cos_sq_minus_sin_sq * p01 + cos_sin * p11
        p11_m = sin_sq * p00 - two_cos_sin * p01 + cos_sq * p11 + q_f
        
        # 3.4. Phase 3: Measurement Update via Exact Scalar Joseph Form Expansion
        innov_cov = p00_m + R_f
        if innov_cov > 1e-9:
            inv_innov = 1.0 / innov_cov
            k0 = p00_m * inv_innov
            k1 = p01_m * inv_innov  
            
            v = y_filt - x0_m
            x0 = x0_m + k0 * v
            x1 = x1_m + k1 * v
            
            # Caching components for hardware pipelining acceleration
            one_minus_k0 = 1.0 - k0
            k0_R = k0 * R_f
            k1_R = k1 * R_f
            
            # Rigorous expansion of Joseph Form: (I - KH)P(I - KH)^T + KRK^T
            p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0_R)
            p01_new = (-k1 * one_minus_k0 * p00_m) + (one_minus_k0 * p01_m) + (k0 * k1_R)
            p11_new = (k1 * k1 * p00_m) - (2.0 * k1 * p01_m) + p11_m + (k1 * k1_R)
        else:
            x0, x1 = x0_m, x1_m
            p00_new, p01_new, p11_new = p00_m, p01_m, p11_m
        
        # 3.5. Bound Constraints & Cauchy-Schwarz Stability Guards
        p00 = p00_new if p00_new > 1e-14 else 1e-14
        p11 = p11_new if p11_new > 1e-14 else 1e-14
        
        p_prod = p00 * p11
        max_p01 = math.sqrt(p_prod if p_prod > 1e-28 else 1e-28)
        
        if p01_new > max_p01:
            p01 = max_p01
        elif p01_new < -max_p01:
            p01 = -max_p01
        else:
            p01 = p01_new
        
        # Root-Mean-Square Energy tracking mapped to output memory buffer
        energy_out[i] = x0 * x0 + x1 * x1

# =============================================================
# 4. Memory Block Allocation & Execution
# =============================================================
X_intent_energy = np.zeros(N)
Y_filtered_signal = np.zeros(N)

# Execute the complete causal control kernel
execute_realtime_kalman_causal_fixed(
    Y_raw, b_notch, a_notch, cos_t, sin_t, q_val, R_val, X_intent_energy, Y_filtered_signal
)

# Phase 4: Non-linear Mapping & Actuator Decision Function
theta = 0.5  
lambda_val = 7.0
P_state = 1 / (1 + np.exp(-lambda_val * (X_intent_energy - theta)))

print(f"Causal simulation completed successfully.")
print(f"Average Activation Probability (4s-7s): {np.mean(P_state[active_mask]):.4f}")

# -------------------------------------------------------------
# Visualization & Result Verification Plotting
# -------------------------------------------------------------
fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

# Graph 1
axs[0].plot(t, Y_raw, color='gray', alpha=0.4, label='Y_raw(t) (Noise Contaminated Input)')
axs[0].plot(t, X_brain, color='green', linewidth=1.8, label='Target X_brain(t) (10Hz SMR)')
axs[0].set_title('Phase 1 & 2: Signal Contamination Profiling', fontsize=11, fontweight='bold')
axs[0].legend(loc='upper right')
axs[0].grid(True, alpha=0.3)

# Graph 2
ax2_twin = axs[1].twinx()
axs[1].plot(t, Y_filtered_signal, color='blue', alpha=0.6, label='Y_conditioned & Gated(t)')
ax2_twin.plot(t, 0.1 + 0.8 * active_mask, color='orange', linestyle='--', linewidth=1.5, label='Informational Target Profiling')
axs[1].set_title('Phase 2: Real-Time Causal Moving-Average Gating Spectrum', fontsize=11, fontweight='bold')
axs[1].legend(loc='upper left')
ax2_twin.legend(loc='upper right')
axs[1].grid(True, alpha=0.3)

# Graph 3
axs[2].plot(t, X_intent_energy, color='purple', linewidth=1.8, label='||X_intent(t)||^2 (State Vector Power)')
axs[2].axhline(y=theta, color='red', linestyle=':', linewidth=1.5, label='Baseline Energy Threshold (theta)')
axs[2].set_title('Phase 3: State-Space Minimal Variance Power Tracking', fontsize=11, fontweight='bold')
axs[2].legend(loc='upper right')
axs[2].grid(True, alpha=0.3)

# Graph 4
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
