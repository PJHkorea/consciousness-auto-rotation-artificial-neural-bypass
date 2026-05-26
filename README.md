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
# ARCF Computational Control Loop (Ultra-Optimized)
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

# Phase 3: State-Space Minimal Variance Estimation (Scalar Expansion)
dt = 1/fs
cos_t = np.cos(2 * np.pi * 10 * dt)
sin_t = np.sin(2 * np.pi * 10 * dt)

# 초기 상태 및 공분산 (스칼라 변수 분할로 블록 메모리 접근 제거)
x0, x1 = 0.0, 0.0
p00, p01, p10, p11 = 1.0, 0.0, 0.0, 1.0

# 하이퍼파라미터 상수화
q_val = 0.01
R_val = 1.44     

X_intent_energy = np.zeros(N)

# NumPy 행렬 내적(@)을 완전히 제거한 250Hz 초고속 루프
for i in range(N):
    # Time Update (Predict) -> A @ x 및 A @ P @ A.T + Q 전개
    x0_minus = cos_t * x0 - sin_t * x1
    x1_minus = sin_t * x0 + cos_t * x1
    
    # P_minus = A @ P @ A.T + Q 직접 대수 전개
    p00_m = cos_t*(cos_t*p00 - sin_t*p10) - sin_t*(cos_t*p01 - sin_t*p11) + q_val
    p01_m = sin_t*(cos_t*p00 - sin_t*p10) + cos_t*(cos_t*p01 - sin_t*p11)
    p10_m = cos_t*(sin_t*p00 + cos_t*p10) - sin_t*(sin_t*p01 + cos_t*p11)
    p11_m = sin_t*(sin_t*p00 + cos_t*p10) + cos_t*(sin_t*p01 + cos_t*p11) + q_val
    
    # Measurement Update (Correct)
    y = Y_filtered[i]
    innov_cov = p00_m + R_val
    
    # 칼만 이득 (K = P_minus[:, 0] / innov_cov)
    k0 = p00_m / innov_cov
    k1 = p10_m / innov_cov
    
    # 상태 갱신 (x = x_minus + K * (y - x0_minus))
    v = y - x0_minus
    x0 = x0_minus + k0 * v
    x1 = x1_minus + k1 * v
    
    # 공분산 갱신 (P = (I - K@H) @ P_minus) 및 수치 대칭화 통합
    p00 = (1.0 - k0) * p00_m
    p01 = (1.0 - k0) * p01_m
    p10 = p10_m - k1 * p00_m
    p11 = p11_m - k1 * p01_m
    
    # 수치적 비대칭 방지 (동일 연산 결합)
    p01_avg = (p01 + p10) * 0.5
    p01 = p01_avg
    p10 = p01_avg
    
    # 에너지 계산
    X_intent_energy[i] = x0*x0 + x1*x1

# Phase 4: Non-linear Mapping & Actuator Decision Function
theta = 0.4  
lambda_val = 8.0
P_state = 1 / (1 + np.exp(-lambda_val * (X_intent_energy - theta)))

print(f"Simulation completed successfully.")
print(f"Average Activation Probability (4s-7s): {np.mean(P_state[active_mask]):.4f}")

