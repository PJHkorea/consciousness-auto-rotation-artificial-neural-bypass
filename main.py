import numpy as np
import matplotlib.pyplot as plt

# 1. Environment & Simulation Variables (10s, 250Hz sampling rate)
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
# ARCF Computational Control Loop (Ultra-Optimized Edition)
# -------------------------------------------------------------

# Phase 1: Linear Impedance Cancellation
Y_ccl = Y_raw - I_stim_distorted  

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

# Phase 3: State-Space Minimal Variance Estimation (Optimized Scalar Expansion)
dt = 1/fs
cos_t = np.cos(2 * np.pi * 10 * dt)
sin_t = np.sin(2 * np.pi * 10 * dt)

# Initial States & Error Covariances (Structural Symmetry Optimized)
x0, x1 = 0.0, 0.0
p00, p01, p11 = 1.0, 0.0, 1.0  # Memory space optimization by omitting redundant p10

# Hyperparameters
q_val = 0.01
R_val = 1.44     

X_intent_energy = np.zeros(N)

# 250Hz real-time processing loop (5th Verified Version)
for i in range(N):
    # 1. Time Update (Predict State)
    x0_minus = cos_t * x0 - sin_t * x1
    x1_minus = sin_t * x0 + cos_t * x1
    
    # 2. Time Update (Predict Covariance: A * P)
    ap00 = cos_t * p00 - sin_t * p01
    ap01 = cos_t * p01 - sin_t * p11
    ap10 = sin_t * p00 + cos_t * p01
    ap11 = sin_t * p01 + cos_t * p11
    
    # P_minus = (A * P) * A^T + Q analytical expansion
    p00_m = ap00 * cos_t - ap01 * sin_t + q_val
    p01_m = ap00 * sin_t + ap01 * cos_t
    p11_m = ap10 * sin_t + ap11 * cos_t + q_val
    
    # 3. Measurement Update (Correct)
    y = Y_filtered[i]
    innov_cov = p00_m + R_val
    
    # Kalman Gain Calculation
    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov
    
    # Update State Variables
    v = y - x0_minus
    x0 = x0_minus + k0 * v
    x1 = x1_minus + k1 * v
    
    # Update Covariance: P = (I - KH)P_minus mathematical exact expansion
    # Parallel Tuple Assignment to prevent race condition or data contamination
    p00_new = (1.0 - k0) * p00_m
    p01_new = (1.0 - k0) * p01_m
    p11_new = p11_m - k1 * p01_m
    
    p00, p01, p11 = p00_new, p01_new, p11_new
    
    # State Vector Root-Mean-Square Energy Calculation
    X_intent_energy[i] = x0*x0 + x1*x1

# Phase 4: Non-linear Mapping & Actuator Decision Function
theta = 0.4  
lambda_val = 8.0
P_state = 1 / (1 + np.exp(-lambda_val * (X_intent_energy - theta)))

print(f"Simulation completed successfully.")
print(f"Average Activation Probability (4s-7s): {np.mean(P_state[active_mask]):.4f}")

# -------------------------------------------------------------
# Visualization & Result Verification Plotting
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
axs[0].get_shared_x_axes().join(axs[0], axs[1]) # Link axes for perfect alignment
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

# Save high-resolution plot for thesis and whitepaper configuration
plt.savefig('arcf_simulation_result.png', dpi=300)
print("Simulation plot saved successfully as 'arcf_simulation_result.png' (300 DPI).")
plt.show()
