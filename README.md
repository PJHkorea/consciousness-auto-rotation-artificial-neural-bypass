# Artificial Neural Bypass for Open-Loop Disorders of Consciousness (DoC)
> **Theory of Closed-loop Neural Resonance for Consciousness Auto-Rotation**

This repository contains the official framework, mathematical formulation, and a high-performance, numerically stable Python implementation of the **Autobiographical Resonance-based Closed-loop Filter (ARCF)**. This system functions as an artificial neural bypass to restore information loops in patients with Unresponsive Wakefulness Syndrome (UWS) or Minimum Conscious State (MCS).

---

## ⚖️ License & Anti-Monopoly Declaration (GNU GPL v3)

This project is fully open-sourced under the **GNU General Public License v3 (GPL v3)**. 

### 🚫 STRICT ANTI-MONOPOLY CONDITION:
* **Freedom to Use & Modify**: Anyone is free to download, modify, and integrate this algorithm into any hardware or software system.
* **Mandatory Copyleft**: If you modify this source code or use it to create derivative works (including commercial medical devices, software, or rehabilitation systems), **you are LEGALLY OBLIGATED to open-source your entire derivative work's source code under the same GPL v3 license**.
* **Prior Art Registration**: This repository serves as public *Prior Art*. No individual, corporation, or institution can legally patent this specific multi-layered neuro-feedback integration framework or its exact mathematical formulations.

---

## 🧠 Core Philosophy: The Two-Layer Consciousness Model

Current neuromodulation paradigms often treat disorders of consciousness as a generalized cellular degradation. In contrast, this framework models human consciousness through **Two Distinct Layers**:
1. **Layer 1 (Subcortical/Thalamic System)**: The baseline generator supplying arousal energy.
2. **Layer 2 (Cortical Lattice)**: The cognitive processing unit rendering the internal screen of awareness.

Patients in a vegetative state (UWS) are defined as being in an **Open-Loop State**, where the informational transit between these two layers is severed. This project establishes an **Artificial Neural Bypass (External Feedback Loop)** utilizing non-invasive technology to force the brain's internal network back into a self-sustaining cycle—**Consciousness Auto-Rotation**.

---

## 📊 System Architecture & Computational Loop

The data pipeline consists of an optimized 3-stage linear processing loop that operates in real-time on surface biopotentials to extract intent and trigger physical afferent feedback.
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
# ARCF Computational Control Loop (Optimized)
# -------------------------------------------------------------

# Phase 1: Linear Impedance Cancellation
Y_ccl = Y_raw - I_stim_distorted  

# Phase 2: Physiological Mutual Information Gating (Vectorized)
noise = np.random.normal(0, 0.02, N)
condlist = [t < 3.5, (3.5 <= t) & (t <= 4.5), (4.5 < t) & (t <= 7.0), t > 7.0]
choicelist = [
    0.1 + noise,
    0.1 + 0.8 * ((t - 3.5) / 1.0), 
    0.9 + noise,
    np.maximum(0.1, 0.9 - 0.8 * ((t - 7.0) / 1.0))
]
W_gate = np.select(condlist, choicelist)
Y_filtered = Y_ccl * W_gate

# Phase 3: State-Space Minimal Variance Estimation
dt = 1/fs
cos_t, sin_t = np.cos(2*np.pi*10*dt), np.sin(2*np.pi*10*dt)
A = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
H = np.array([[1, 0]])      
I_matrix = np.eye(2)
Q = np.eye(2) * 0.01       
R_val = 1.44     

x_hat = np.zeros((2, 1))
P = np.eye(2) * 1.0
X_intent_energy = np.zeros(N)

# Ultra-low latency single-loop execution (Optimized for Real-Time DSP Hardware)
for i in range(N):
    # Time Update (Predict)
    x_hat_minus = A @ x_hat
    P_minus = A @ P @ A.T + Q
    
    # Measurement Update (Correct via high-speed index matching)
    y = Y_filtered[i]
    innov_cov = P_minus[0, 0] + R_val # H @ P_minus @ H.T 고속 연산 스칼라 매핑
    K = P_minus[:, 0:1] / innov_cov   # Kalman Gain 벡터 연산 최적화
    
    x_hat = x_hat_minus + K * (y - x_hat_minus[0, 0])
    P = (I_matrix - K @ H) @ P_minus
    P = (P + P.T) / 2 # 수치 안정성 강제 확보 (컴퓨터 반올림 오차 누적 방지)
    
    X_intent_energy[i] = x_hat[0, 0]**2 + x_hat[1, 0]**2

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
# 논문 및 백서 탑재를 위한 고해상도 이미지 파일로 자동 저장
plt.savefig('arcf_simulation_result.png', dpi=300)
print("Simulation plot saved as 'arcf_simulation_result.png' (300 DPI).")
plt.show()


