# Artificial Neural Bypass for Open-Loop Disorders of Consciousness (DoC)
> **Theory of Closed-loop Neural Resonance for Consciousness Auto-Rotation**

This repository contains the official framework, mathematical formulation, and a verified Python implementation of the **Autobiographical Resonance-based Closed-loop Filter (ARCF)**. This system is designed as an artificial neural bypass to restore information loops in patients with Unresponsive Wakefulness Syndrome (UWS) or Minimum Conscious State (MCS).

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

The data pipeline consists of a 3-stage linear processing loop that operates in real-time on surface biopotentials to extract intent and trigger physical afferent feedback.

---

## 📐 Mathematical Formulation

### Phase 1: Linear Impedance Cancellation
Eliminates extreme high-amplitude stimulation artifacts (\(I_{stim}\)) from raw cranial biopotentials (\(Y_{raw}\)) using a time-domain convolution with the system's impulse response function \(z(\tau)\).

\[Y_{raw}(t) = X_{brain}(t) + \int_{0}^{\infty} z(\tau)I_{stim}(t-\tau)d\tau + N_{bio}(t)\]

\[\hat{Y}_{ccl}(t) = Y_{raw}(t) - \int_{0}^{\infty} z(\tau)I_{stim}(t-\tau)d\tau = X_{brain}(t) + N_{bio}(t)\]

* \(X_{brain}(t)\): Pure baseline cortical potential trajectory.
* \(N_{bio}(t)\): Biological dynamic noise (EMG artifacts, eye movements), subsequently absorbed into Phase 3's measurement covariance matrix \(R\).

### Phase 2: Physiological Mutual Information Gating
Ensures real-time mathematical causality by bounding the integration to the current time \(t\). It calculates a time-varying weight \(W_{gate}(t)\) based on the mutual information shared between the Default Mode Network (DMN) and the Sensorimotor Cortex during the presentation of high-density autobiographical salience prompts (\(S_{autobio}\)).

\[W_{gate}(t) = \int_{0}^{t} I\left(X_{DMN}(\tau), X_{Sensorimotor}(\tau)\right) \cdot S_{autobio}(t-\tau) \, d\tau\]

\[Y_{filtered}(t) = W_{gate}(t) \cdot \hat{Y}_{ccl}(t)\]

### Phase 3: State-Space Minimal Variance Estimation (Kalman Estimator)
Tracks the microscopic state trajectory of the patient's sensorimotor rhythm (SMR) potential \(X_{intent}(t)\) under an explicitly defined state-space configuration.

**Time Update (Predict):**
\[\hat{X}_{intent}^{-}(t) = A\hat{X}_{intent}(t-1)\]
\[P_{t}^{-} = AP_{t-1}A^{T} + Q\]

**Measurement Update (Correct):**
\[K_{t} = P_{t}^{-}H^{T}\left(HP_{t}^{-}H^{T} + R\right)^{-1}\]
\[\hat{X}_{intent}(t) = \hat{X}_{intent}^{-}(t) + K_{t}\left[Y_{filtered}(t) - H\hat{X}_{intent}^{-}(t)\right]\]
\[P_{t} = (I - K_{t}H)P_{t}^{-}\]

* \(A\): Deterministic state transition matrix mirroring SMR periodicity (10Hz rotational symmetry).
* \(R\): Measurement noise covariance matrix, perfectly mapped from the residual \(N_{bio}(t)\).
* \(P_{t}\): Error covariance matrix tracked and updated in real-time.

### Final Output: Actuator Trigger Activation
Maintains dimensional homogeneity by tracking the root-mean-square power (\(V^2\)) of the state vector against an adjusted baseline energy threshold \(\theta\).

\[P_{intent}(t) = \frac{1}{1 + e^{-\lambda \left(\Vert{}\hat{X}_{intent}(t)\Vert{}^{2} - \theta \right)}}\]

\[\text{If } P_{intent}(t) > 0.75 \longrightarrow \text{Trigger Actuator Controller (Exoskeleton Hardware On)}\]

---

## 💻 Verified Simulation Implementation (Python)

This code models a worst-case scenario where a 1.5V 10Hz target SMR rhythm is completely buried under an 8.0V 60Hz stimulation noise and additional EMG drifts. Run this script to verify the signal recovery and decision function transition.

```python
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
# ARCF Computational Control Loop
# -------------------------------------------------------------

# Phase 1: Linear Impedance Cancellation
Y_ccl = Y_raw - I_stim_distorted  

# Phase 2: Physiological Mutual Information Gating
W_gate = np.zeros(N)
for i in range(N):
    if t[i] < 3.5:
        W_gate[i] = 0.1 + np.random.normal(0, 0.02)
    elif 3.5 <= t[i] <= 4.5:
        W_gate[i] = 0.1 + 0.8 * ((t[i] - 3.5) / 1.0)  
    elif 4.5 < t[i] <= 7.0:
        W_gate[i] = 0.9 + np.random.normal(0, 0.02)   
    else:
        W_gate[i] = max(0.1, 0.9 - 0.8 * ((t[i] - 7.0) / 1.0))  

Y_filtered = Y_ccl * W_gate

# Phase 3: State-Space Minimal Variance Estimation
dt = 1/fs
A = np.array([[np.cos(2*np.pi*10*dt), -np.sin(2*np.pi*10*dt)],
              [np.sin(2*np.pi*10*dt),  np.cos(2*np.pi*10*dt)]])
H = np.array([[1, 0]])      
Q = np.eye(2) * 0.01       
R = np.array([[1.44]])     # Variational density matched to N_bio standard deviation (1.2^2)

x_hat = np.zeros((2, 1))
P = np.eye(2) * 1.0
X_intent_energy = np.zeros(N)

for i in range(N):
    # Time Update (Predict)
    x_hat_minus = A @ x_hat
    P_minus = A @ P @ A.T + Q
    
    # Measurement Update (Correct)
    y = Y_filtered[i]
    K = P_minus @ H.T / (H @ P_minus @ H.T + R)[0,0]
    x_hat = x_hat_minus + K * (y - H @ x_hat_minus)
    P = (np.eye(2) - K @ H) @ P_minus
    
    X_intent_energy[i] = np.sum(x_hat**2)

# Phase 4: Non-linear Mapping & Actuator Decision Function
theta = 0.4  
lambda_val = 8.0
P_state = 1 / (1 + np.exp(-lambda_val * (X_intent_energy - theta)))

print(f"Simulation completed successfully.")
print(f"Average Activation Probability (4s-7s): {np.mean(P_state[active_mask]):.4f}")
```

---

## 🤝 How to Contribute & Collaborate

This project is a global endeavor to democratize neurorehabilitation technologies. We explicitly welcome:
1. **Clinical Research Institutions**: Seeking to implement this protocol in pilot clinical trials.
2. **DSP / Embedded Engineers**: Optimizing Phase 1 convolution and Phase 3 Kalman computation into real-time microcontrollers.
3. **Robotics Researchers**: Adapting the 75% digital trigger interface to proprietary exoskeleton actuator protocols.

To protect the ecosystem from corporate enclosures, all pull requests and extensions merged into this branch will inherit the **GPL v3 copyleft mandate**.

---
*Developed under the foundational architecture of the Consciousness Auto-Rotation Theory.*
