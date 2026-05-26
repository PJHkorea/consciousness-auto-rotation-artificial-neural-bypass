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
        Phase1["Phase 1: Linear Impedance Cancellation <br> <i>z(τ) Convolution Anti-Phase Filtering</i>"]:::process
        Phase2["Phase 2: Physiological Mutual Information Gating <br> <i>Vectorized np.select C-Engine Speed</i>"]:::process
        Phase3["Phase 3: State-Space Minimal Variance Estimation <br> <i>Ultra-Optimized Scalar Expansion Kalman Loop</i>"]:::process
    end

    %% 출력 및 액추에이터 제어 레이어
    subgraph OUTPUT_STAGE [Output & Control Layer]
        P_intent["P_intent(t) <br> Sigmoid Energy-Dimensional Mapping"]:::output
        Trigger{"Threshold Check <br> P_intent(t) > 0.75"}:::output
        ExoRobot["Trigger Actuator Controller <br> Robotic Exoskeleton On"]:::output
    end

    %% 데이터 흐름 연결
    Y_raw --> Phase1
    I_stim --> Phase1
    
    Phase1 -->|Y_filtered baseline| Phase2
    S_autobio -->|Cognitive Resonance Gate Trigger| Phase2
    
    Phase2 -->|Gated SMR Potential Spectrum| Phase3
    
    Phase3 -->|Root-Mean-Square Power V²| P_intent
    P_intent --> Trigger
    
    %% 폐루프 수렴 (거울 되먹임 루프)
    Trigger -->|YES| ExoRobot
    ExoRobot -.->|<b>Mirror Feedback Loop</b> <br> Afferent Somatosensory Feedback| Y_raw:::loop

    %% 스타일 적용
    style COMP_LOOP fill:#fff,stroke:#333,stroke-width:1px
    style INPUT_STAGE fill:#fff,stroke:#333,stroke-width:1px
    style OUTPUT_STAGE fill:#fff,stroke:#333,stroke-width:1px
```
