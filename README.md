# Artificial Neural Bypass for Open-Loop Disorders of Consciousness (DoC)
> **Theory of Closed-loop Neural Resonance for Consciousness Auto-Rotation**

This repository contains the official framework, mathematical formulation, and a high-performance, production-ready real-time implementation of the **Autobiographical Resonance-based Closed-loop Filter (ARCF)**. This system functions as an artificial neural bypass to restore functional information loops in patients with Unresponsive Wakefulness Syndrome (UWS) or Minimum Conscious State (MCS).

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
1. **Layer 1 (Subcortical/Thalamic System)**: The baseline generator supplying arousal energy (Arousal Subsystem).
2. **Layer 2 (Cortical Lattice)**: The cognitive processing unit rendering the internal screen of awareness (Cognitive Lattice).

Patients in a vegetative state (UWS) are defined as being in an **Open-Loop State**, where the informational transit between these two layers is severed. This project establishes an **Artificial Neural Bypass (External Feedback Loop)** utilizing non-invasive technology to force the brain's internal network back into a self-sustaining cycle—**Consciousness Auto-Rotation**.

---

## 📊 System Architecture & Computational Loop

The data pipeline consists of an optimized 3-stage linear processing loop that operates in real-time on surface biopotentials to extract intent and trigger physical afferent feedback.

```mermaid
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
```

---

## 📐 Technical Specification (Mathematical Formulation)

This section provides the definitive mathematical formulation for the Autobiographical Resonance-based Closed-loop Filter (ARCF).

### 1. Phase 1: Real-Time Signal Conditioning
Primary elimination of the 60 Hz power-line artifact from the raw cranial biopotential ($Y_{\text{raw}}$) is executed using an inline digital Infinite Impulse Response (IIR) notch filter operating in Direct Form II structure to preserve hidden cognitive potentials ($Y_{\text{ccl}}$):

$$Y_{\text{ccl}}[k] = \mathcal{L}_{\text{notch}}(Y_{\text{raw}}[k])$$

An exact analytical feed-forward compensation for the frequency-dependent phase delay ($\phi_{\text{delay}}$) at the tracking target frequency (10 Hz) is integrated directly into the digital domain angular rotation calculation:

$$\theta = 2\pi f \Delta t + \phi_{\text{delay}}$$

### 2. Phase 2: Physiological Mutual Information Gating
To enforce strict real-time causality and eliminate reliance on artificial time-arrays, the system continuously tracks the instantaneous signal energy using an Exponential Moving Average (EMA). The conditioned signal is multiplied by a time-varying informational weight ($W_{\text{gate}}$) driven by a continuous sigmoid power synchronization profile:

$$E_{\text{running}}[k] = (1 - \alpha) \cdot E_{\text{running}}[k-1] + \alpha \cdot \left(Y_{\text{notch}}[k]\right)^2$$

$$W_{\text{gate}}[k] = \max\left(0.1, \,\, 0.1 + \frac{0.9}{1 + e^{-2.5 \cdot (E_{\text{running}}[k] - 0.8)}}\right)$$

$$Y_{\text{filtered}}[k] = Y_{\text{notch}}[k] \cdot W_{\text{gate}}[k]$$
### 3. Phase 3: State-Space Minimal Variance Tracking (Safe-Kalman Core)
The discrete state-space framework models the system to track the microscopic 10 Hz sensorimotor resonance rhythm (\(X_{\text{brain}}\)) hidden in the filtered potential.

#### A. Time Update (Predictive Step)
\[\hat{\mathbf{x}}_{k\vert{}k-1} = \begin{bmatrix} \cos\theta & \sin\theta \\ -\sin\theta & \cos\theta \end{bmatrix} \hat{\mathbf{x}}_{k-1\vert{}k-1}\]

\[p_{00\_m} = \cos^2\theta \cdot p_{00} + 2\cos\theta\sin\theta \cdot p_{01} + \sin^2\theta \cdot p_{11} + Q\]

\[p_{01\_m} = -\cos\theta\sin\theta \cdot p_{00} + (\cos^2\theta - \sin^2\theta) \cdot p_{01} + \cos\theta\sin\theta \cdot p_{11}\]

\[p_{11\_m} = \sin^2\theta \cdot p_{00} - 2\cos\theta\sin\theta \cdot p_{01} + \cos^2\theta \cdot p_{11} + Q\]

#### B. Joseph Form Covariance Update (Analytical Scalar Expansion)
To enforce absolute positive-definiteness under floating-point round-off errors in low-latency DSP environments, the covariance measurement update is executed via an analytical scalar expansion of the **Joseph Form Equation** (\(M = I - KH, \ H=\begin{bmatrix}1 & 0\end{bmatrix}\)):

\[m_0 = 1.0 - k_0\]

\[p_{00\_new} = (m_0^2 \cdot p_{00\_m}) + (k_0^2 \cdot R)\]

\[p_{01\_new} = (-k_1 \cdot m_0 \cdot p_{00\_m}) + (m_0 \cdot p_{01\_m}) + (k_0 \cdot k_1 \cdot R)\]

\[p_{11\_new} = (k_1^2 \cdot p_{00\_m}) - (2.0 \cdot k_1 \cdot p_{01\_m}) + p_{11\_m} + (k_1^2 \cdot R)\]

#### C. Sub-zero Divergence Guard & Boundary Mapping
When the innovation covariance falls below safety thresholds due to severe transient noise, boundary mapping prevents zero-division and matrix singularity:

\[\text{If } (p_{00\_m} + R) \le 10^{-9} \Longrightarrow \text{Halt Measurement Update Loop}\]

\[p_{00} = \max(p_{00\_new}, 10^{-14}), \quad p_{11} = \max(p_{11\_new}, 10^{-14})\]

The Cauchy-Schwarz inequality is strictly enforced in real-time to clip the cross-covariance component against numerical underflow, preventing structural asymmetry and filter explosion:

\[p_{\text{prod}} = p_{00} \cdot p_{11}\]

\[\lvert p_{01\_aligned} \rvert \le \sqrt{\max(p_{\text{prod}}, 10^{-28})}\]

### 4. Phase 4: Actuator Trigger Mapping
The state vector's root-mean-square energy maps to the probability space (\(P_{\text{state}}\)) through a continuous sigmoid function with dimensional homogeneity, delivering a stable digital command to the actuator controller:

\[P_{\text{state}}[k] = \frac{1}{1 + e^{-\lambda \left( (x_0^2 + x_1^2) - \theta_{\text{baseline}} \right)}}\]

\[\text{If } P_{\text{state}}[k] > 0.75 \longrightarrow \text{Trigger Actuator Controller (Exoskeleton Active)}\]

---

## 💻 Verified Production Implementation (Python & Network Fused)

This script contains the zero-copy real-time streaming core, Numba LLVM compiled scalar Joseph Form tracking loop, and integrated network latency accumulation defenses. Please check the `realtime_bypass.py` file in this repository for the fully production-ready execution script.

```python
# Real-Time Causal Core Snippet (From realtime_bypass.py)
# Optimized via explicit scalar registers and Joseph Form Symmetrization
for i in range(N_samples):
    # Phase 1: Inline IIR Notch Filtering
    y_notch = b * x_in + v0
    v0 = b * x_in - a * y_notch + v1
    v1 = b * x_in - a * y_notch
    
    # Phase 2: Real-time Moving-Average Information Gating
    inst_energy = y_notch * y_notch
    running_energy = (1.0 - ema_alpha) * running_energy + ema_alpha * inst_energy
    w_gate = 0.1 + (0.9 / (1.0 + math.exp(-2.5 * (running_energy - 0.8))))
    
    # Phase 3: Analytical Predictive & Measurement Joseph Form Step
    x0_m = cos_t * x0 + sin_t * x1
    x1_m = -sin_t * x0 + cos_t * x1
    
    p00_m = cos_sq * p00 + two_cos_sin * p01 + sin_sq * p11 + q
    p01_m = -cos_sin * p00 + cos_sq_minus_sin_sq * p01 + cos_sin * p11
    p11_m = sin_sq * p00 - two_cos_sin * p01 + cos_sq * p11 + q
    
    # Parallel Tuple Assignment to eliminate Race Conditions
    p00, p01, p11 = p00_new, p01_guard, p11_guard
```

---

## 🤝 How to Contribute & Collaborate

This project is a global endeavor to democratize neurorehabilitation technologies. We explicitly welcome:

1. **Clinical Research Institutions**: Seeking to implement this protocol in pilot clinical trials.
2. **DSP / Embedded Engineers**: Optimizing and porting the core scalar arithmetic loops directly into STM32 or FPGA architectures.
3. **Robotics Researchers**: Adapting the digital TCP/IP control stream interface into proprietary exoskeleton actuator protocols.

To protect the ecosystem from predatory corporate enclosures, all pull requests, feature branches, and software extensions merged into this pipeline will legally inherit the **GNU GPL v3 copyleft mandate**.

---
*Developed under the foundational architecture of the Consciousness Auto-Rotation Theory.*
