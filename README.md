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
# Technical Specification & Source Code: ARCF System

This document provides the definitive mathematical formulation and the production-ready Python implementation for the Autobiographical Resonance-based Closed-loop Filter (ARCF).

## Part 1: Mathematical Formulation & Core Components

The ARCF features an optimized two-state model augmented with a non-linear informational binder. The core processing pipeline executes via a static-typed Numba JIT environment, providing deterministic real-time performance and total immunity against numerical covariance collapse.

### 1. Phase 1: Real-Time Signal Conditioning
Primary elimination of the 60 Hz power-line artifact from the raw cranial biopotential ($Y_{\text{raw}}$) is executed using a high-Q Infinite Impulse Response (IIR) digital notch filter to preserve hidden cognitive potentials ($Y_{\text{ccl}}$):

$$Y_{\text{ccl}}[k] = \mathcal{L}_{\text{notch}}\left(Y_{\text{raw}}[k]\right)$$

### 2. Phase 2: Physiological Mutual Information Gating
To prevent motion artifacts or baseline drift from corrupting the state tracker, the conditioned signal is multiplied by a time-varying informational weight ($W_{\text{gate}}$) derived from the causal synchronization profile of the Default Mode Network (DMN) and stabilized by a lower bound constraint:

$$W_{\text{gate}}[k] = \max\left(0.1, \; \text{GatingSchedule}(t_k) + \eta[k]\right), \quad \eta \sim \mathcal{N}(0, \sigma^2)$$

$$Y_{\text{filtered}}[k] = Y_{\text{ccl}}[k] \cdot W_{\text{gate}}[k]$$

### 3. Phase 3: State-Space Minimal Variance Tracking (Safe-Kalman Core)
The discrete state-space framework models the system to track the microscopic 10 Hz sensorimotor resonance rhythm ($X_{\text{brain}}$) hidden in the filtered potential. The state transition configuration is governed by $\theta = 2\pi f \Delta t$:

#### A. Time Update (Predictive Step)
$$\hat{x}_{k\vert{}k-1} = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix} \hat{x}_{k-1\vert{}k-1}$$

$$P_{k\vert{}k-1} = A P_{k-1\vert{}k-1} A^T + Q$$

#### B. Joseph Form Covariance Update (Analytical Scalar Expansion)
To enforce absolute positive-definiteness under floating-point round-off errors in low-latency DSP environments, the covariance measurement update is executed via an analytical scalar expansion of the Joseph Form Equation ($M = I - KH, \ H=\begin{bmatrix}1 & 0\end{bmatrix}$). This mathematically guarantees code-to-formula synchronization:

$$m_0 = 1.0 - k_0$$

$$p_{00}^{\text{new}} = m_0^2 \cdot p_{00}^{m} + k_0^2 \cdot R$$

$$p_{01}^{\text{new}} = m_0 \cdot p_{01}^{m} - m_0 \cdot k_1 \cdot p_{00}^{m} + k_0 \cdot k_1 \cdot R$$

$$p_{11}^{\text{new}} = p_{11}^{m} - 2.0 \cdot k_1 \cdot p_{01}^{m} + k_1^2 \cdot p_{00}^{m} + k_1^2 \cdot R$$

#### C. Sub-zero Divergence Guard & Boundary Mapping
When the innovation covariance falls below safety thresholds due to severe transient noise, boundary mapping prevents zero-division and matrix singularity:

$$\text{If } (p_{00}^{m} + R) \le 10^{-9} \implies \text{Halt Measurement Update Loop}$$

$$p_{00} = \max\left(p_{00}^{\text{new}}, 10^{-14}\right), \quad p_{11} = \max\left(p_{11}^{\text{new}}, 10^{-14}\right)$$

The Cauchy-Schwarz inequality is strictly enforced in real-time to clip the cross-covariance component, preventing numerical asymmetry and filter explosion:

$$\vert{}p_{01}\vert{} \le \sqrt{p_{00} \cdot p_{11}}$$

### 4. Phase 4: Actuator Trigger Mapping
The state vector's root-mean-square energy maps to the probability space ($P_{\text{intent}}$) through a continuous sigmoid function with dimensional homogeneity, delivering a stable digital command to the actuator controller:

$$P_{\text{intent}}[k] = \frac{1}{1 + e^{-\lambda \left((x_0^2 + x_1^2) - \theta_{\text{baseline}}\right)}}$$

$$\text{If } P_{\text{intent}}[k] > 0.75 \longrightarrow \text{Trigger Actuator Controller (Exoskeleton Active)}$$

graph TD
    %% 스타일 정의
    classDef input fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,stroke-dasharray: 5 5;
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef output fill:#efebe9,stroke:#5d4037,stroke-width:2px;
    classDef loop fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px;

    %% 입력 데이터 레이어
    subgraph INPUT_STAGE [Input Data Layer]
        Y_raw["Y_raw(t) <br> Raw Cranial Biopotentials"]:::input
        I_stim["I_stim(t) <br> High-Amp Stimulation Input"]:::input
        S_autobio["S_autobio(t) <br> Autobiographical Salience Prompt"]:::input
    end

    %% 실시간 신호처리 및 연산 레이어
    subgraph COMP_LOOP [ARCF Core Computational Loop]
        Phase1["Phase 1: Linear Impedance Cancellation <br> <i>High-Q IIR Notch Filter Line Elimination</i>"]:::process
        Phase2["Phase 2: Physiological Mutual Information Gating <br> <i>Fused Numba JIT (nogil=True, fastmath=True)</i>"]:::process
        Phase3["Phase 3: State-Space Minimal Variance Estimation <br> <i>Statically Allocated Scalar Joseph Form Loop</i>"]:::process
    end

    %% 출력 및 액추에이터 제어 레이어
    subgraph OUTPUT_STAGE [Output & Control Layer]
        P_intent["P_state(t) <br> Sigmoid Energy-Dimensional Mapping"]:::output
        Trigger{"Threshold Check <br> P_state(t) > 0.75"}:::output
        ExoRobot["Trigger Actuator Controller <br> Robotic Exoskeleton On"]:::output
    end

    %% 데이터 흐름 연결
    Y_raw --> Phase1
    I_stim --> Phase1
    
    Phase1 -->|Y_ccl Signal Buffer| Phase2
    S_autobio -->|Cognitive Resonance Gate Trigger| Phase2
    
    Phase2 -->|Y_filtered_signal Spectrum| Phase3
    
    Phase3 -->|X_intent_energy Power V²| P_intent
    P_intent --> Trigger
    
    %% 폐루프 수렴 (거울 되먹임 루프)
    Trigger -->|YES| ExoRobot
    ExoRobot -.->|<b>Mirror Feedback Loop</b> <br> Afferent Somatosensory Feedback| Y_raw:::loop

    %% 스타일 적용
    style COMP_LOOP fill:#fff,stroke:#333,stroke-width:1px
    style INPUT_STAGE fill:#fff,stroke:#333,stroke-width:1px
    style OUTPUT_STAGE fill:#fff,stroke:#333,stroke-width:1px
