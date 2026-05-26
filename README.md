# Artificial Neural Bypass for Open-Loop Disorders of Consciousness (DoC)

**Theory of Closed-loop Neural Resonance for Consciousness Auto-Rotation**

이 레포지토리는 의식 불명 상태(UWS) 또는 최소 의식 상태(MCS) 환자의 기능적 정보 루프를 회복하기 위한 **Autobiographical Resonance-based Closed-loop Filter (ARCF)**의 공식 프레임워크와 구현 코드를 포함합니다 [1].

## ⚖ License & Anti-Monopoly Declaration (GNU GPL v3)

본 프로젝트는 GNU General Public License v3 (GPL v3)에 따라 오픈 소스로 공개됩니다.

### 🚫 STRICT ANTI-MONOPOLY CONDITION:

- **사용 및 수정 자유**: 누구나 이 알고리즘을 다운로드, 수정하여 하드웨어/소프트웨어 시스템에 통합할 수 있습니다.
- **의무 Copyleft**: 수정된 소스 코드나 이를 사용하여 생성된 파생 저작물(상업용 의료 기기, 소프트웨어 등)은 동일한 GPL v3 라이선스 하에 전체 소스 코드를 공개해야 합니다.
- **선행 기술 등록**: 이 레포지토리는 공개된 선행 기술로 기능하며, 해당 다층 신경 피드백 통합 프레임워크 또는 정확한 수학적 정식화에 대한 특허 취득을 제한합니다.

## 🧠 Core Philosophy: The Two-Layer Consciousness Model

본 프레임워크는 의식 장애를 2개의 구별된 층으로 모델링합니다:
1.  **Layer 1 (Subcortical/Thalamic System)**: 각성 에너지를 공급하는 베이스라인 생성기 (Arousal Subsystem).
2.  **Layer 2 (Cortical Lattice)**: 내적 인식 화면을 렌더링하는 인지 처리 단위 (Cognitive Lattice).

식물인간 상태(UWS)는 이 두 층 사이의 정보 흐름이 끊긴 **Open-Loop State**로 정의됩니다. 본 프로젝트는 비침습적 기술을 사용하여 뇌의 내부 네트워크를 자기 지속적 주기로 강제 전환하는 **Artificial Neural Bypass (External Feedback Loop)**를 구축하여 **Consciousness Auto-Rotation**을 유도합니다.

## 📊 System Architecture & Computational Loop

시스템은 표면 생체 전위에서 의도를 추출하고 물리적 구심성 피드백을 트리거하는 최적화된 3단계 실시간 선형 처리 루프(`Phase 1~3`)로 구성되며, 상세한 흐름도는 `Mermaid` 다이어그램을 참고하십시오 [1].
## 📐 Technical Specification (Mathematical Formulation)

This section provides the definitive mathematical formulation for the Autobiographical Resonance-based Closed-loop Filter (ARCF).

### 1. Phase 1: Real-Time Signal Conditioning

Primary elimination of the 60 Hz power-line artifact from the raw cranial biopotential (\(Y_{\text{raw}}\)) is executed using an inline digital Infinite Impulse Response (IIR) notch filter operating in Direct Form II structure to preserve hidden cognitive potentials (\(Y_{\text{ccl}}\)):

\[Y_{\text{ccl}}[k] = \mathcal{L}_{\text{notch}}(Y_{\text{raw}}[k])\]

An exact analytical feed-forward compensation for the frequency-dependent phase delay (\(\phi_{\text{delay}}\)) at the tracking target frequency (10 Hz) is integrated directly into the digital domain angular rotation calculation:

\[\theta = 2\pi f \Delta t + \phi_{\text{delay}}\]

### 2. Phase 2: Physiological Mutual Information Gating

To enforce strict real-time causality and eliminate reliance on artificial time-arrays, the system continuously tracks the instantaneous signal energy using an Exponential Moving Average (EMA). The conditioned signal is multiplied by a time-varying informational weight (\(W_{\text{gate}}\)) driven by a continuous sigmoid power synchronization profile:

\[E_{\text{running}}[k] = (1 - \alpha) \cdot E_{\text{running}}[k-1] + \alpha \cdot \left(Y_{\text{notch}}[k]\right)^2\]

\[W_{\text{gate}}[k] = \max\left(0.1, \; 0.1 + \frac{0.9}{1 + e^{-2.5 \cdot (E_{\text{running}}[k] - 0.8)}}\right)\]

\[Y_{\text{filtered}}[k] = Y_{\text{notch}}[k] \cdot W_{\text{gate}}[k]\]

### 3. Phase 3: State-Space Minimal Variance Tracking (Safe-Kalman Core)

The discrete state-space framework models the system to track the microscopic 10 Hz sensorimotor resonance rhythm (\(X_{\text{brain}}\)) hidden in the filtered potential.

#### A. Time Update (Predictive Step)

\[\hat{\mathbf{x}}_{k\vert{}k-1} = \begin{bmatrix} \cos\theta & \sin\theta \\ -\sin\theta & \cos\theta \end{bmatrix} \hat{\mathbf{x}}_{k-1\vert{}k-1}\]

\[p_{00\_m} = \cos^2\theta \cdot p_{00} + 2\cos\theta\sin\theta \cdot p_{01} + \sin^2\theta \cdot p_{11} + Q\]

\[p_{01\_m} = -\cos\theta\sin\theta \cdot p_{00} + (\cos^2\theta - \sin^2\theta) \cdot p_{01} + \cos\theta\sin\theta \cdot p_{11}\]

\[p_{11\_m} = \sin^2\theta \cdot p_{00} - 2\cos\theta\sin\theta \cdot p_{01} + \cos^2\theta \cdot p_{11} + Q\]

#### B. Joseph Form Covariance Update (Analytical Scalar Expansion)

To enforce absolute positive-definiteness under floating-point round-off errors in low-latency DSP environments, the covariance measurement update is executed via an analytical scalar expansion of the **Joseph Form Equation** (\(M = I - KH, \; H=\begin{bmatrix}1 & 0\end{bmatrix}\)):

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

\[\vert{}p_{01\_aligned}\vert{} \le \sqrt{\max(p_{\text{prod}}, 10^{-28})}\]

### 4. Phase 4: Actuator Trigger Mapping

The state vector's root-mean-square energy maps to the probability space (\(P_{\text{state}}\)) through a continuous sigmoid function with dimensional homogeneity, delivering a stable digital command to the actuator controller:

\[P_{\text{state}}[k] = \frac{1}{1 + e^{-\lambda \left( (x_0^2 + x_1^2) - \theta_{\text{baseline}} \right)}}\]

\[\text{If } P_{\text{state}}[k] > 0.75 \longrightarrow \text{Trigger Actuator Controller (Exoskeleton Active)}\]

## 💻 Verified Production Implementation (Python & Network Fused)

This script contains the zero-copy real-time streaming core, Numba LLVM compiled scalar Joseph Form tracking loop, and integrated network latency accumulation defenses. Please check the realtime_bypass.py file in this repository for the fully production-ready execution script.

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

## 🤝 How to Contribute & Collaborate

This project is a global endeavor to democratize neurorehabilitation technologies. We explicitly welcome clinical research institutions, DSP engineers, and robotics researchers. All extensions merged into this pipeline will legally inherit the **GNU GPL v3 copyleft mandate**.

*Developed under the foundational architecture of the Consciousness Auto-Rotation Theory.*
