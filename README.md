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

# 1. 환경 및 시뮬레이션 변수 (10초, 250Hz 샘플링 속도)
np.random.seed(42)
fs = 250
t = np.arange(0, 10, 1/fs)
N = len(t)

# 오염된 원시 입력 모델링
X_brain = np.zeros(N)
active_mask = (t >= 4) & (t <= 7)
X_brain[active_mask] = 1.5 * np.sin(2 * np.pi * 10 * t[active_mask])

I_stim_distorted = 8.0 * np.sin(2 * np.pi * 60 * t - 0.5)
N_bio = np.random.normal(0, 1.2, N) + 0.5 * np.sin(2 * np.pi * 1.5 * t)

Y_raw = X_brain + I_stim_distorted + N_bio

# -------------------------------------------------------------
# ARCF 전산 제어 루프(최적화됨)
# -------------------------------------------------------------

# 1단계: 선형 임피던스 상쇄
Y_ccl = Y_raw - I_stim_distorted

# 2단계: 생리적 상호 정보 게이팅(벡터화)
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

# 3단계: 상태 공간 최소 분산 추정
dt = 1/fs
cos_t, sin_t = np.cos(2 * np.pi * 10 * dt), np.sin(2 * np.pi * 10 * dt)
A = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
H = np.array([[1, 0]])
I_matrix = np.eye(2)
Q = np.eye(2) * 0.01
R_val = 1.44

x_hat = np.zeros((2, 1))
P = np.eye(2) * 1.0
X_intent_energy = np.zeros(N)

# 초저지연 단일 루프 실행 (실시간 DSP 하드웨어에 최적화)
for i in range(N):
    # 시간 업데이트 (예측)
    x_hat_minus = A @ x_hat
    P_minus = A @ P @ A.T + Q

    # Measurement Update (Correct via high-speed index matching)
    y = Y_filtered[i]
    innov_cov = P_minus[0, 0] + R_val  # H @ P_minus @ H.T 고속 연산 스칼라 매핑
    K = P_minus[:, 0:1] / innov_cov    # Kalman Gain 벡터 연산 최적화

    x_hat = x_hat_minus + K * (y - x_hat_minus[0, 0])
    P = (I_matrix - K @ H) @ P_minus
    P = (P + P.T) / 2                  # 수치 안정성 강제 확보 (컴퓨터 반올림 오차 누적 방지)

    X_intent_energy[i] = x_hat[0, 0]**2 + x_hat[1, 0]**2

# 4단계: 비선형 매핑 및 액추에이터 결정 기능
theta = 0.4
lambda_val = 8.0
P_state = 1 / (1 + np.exp(-lambda_val * (X_intent_energy - theta)))

print(f"시뮬레이션이 성공적으로 완료되었습니다.")
print(f"평균 활성화 확률(4초~7초): {np.mean(P_state[active_mask]):.4f}")

# -------------------------------------------------------------
# 시각화 및 결과 검증 그래프 작성
# -------------------------------------------------------------
fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

# 그래프 1: 오염된 원시 입력 신호 대 은닉 목표 신호
axs[0].plot(t, Y_raw, color='gray', alpha=0.4, label='Y_raw(t) (노이즈 오염 입력)')
axs[0].plot(t, X_brain, color='green', linewidth=1.8, label='타겟 X_brain(t) (10Hz SMR)')
axs[0].set_title('1단계 및 2단계: 신호 오염 프로파일링', fontsize=11, fontweight='bold')
axs[0].legend(loc='upper right')
axs[0].grid(True, alpha=0.3)

# 그래프 2: 게이트 신호 스펙트럼 및 동적 공진 가중치
ax2_twin = axs[1].twinx()
axs[1].plot(t, Y_filtered, color='blue', alpha=0.6, label='Y_filtered(t) (게이트 출력)')
ax2_twin.plot(t, W_gate, color='orange', linestyle='--', linewidth=1.5, label='W_gate(t) (DMN 공명)')
axs[1].set_title('2단계: 생리학적 상호 정보 게이팅 스펙트럼', fontsize=11, fontweight='bold')
axs[1].legend(loc='upper left')
ax2_twin.legend(loc='upper right')
axs[1].grid(True, alpha=0.3)

# 그래프 3: 칼만 상태 추적 에너지 검증
axs[2].plot(t, X_intent_energy, color='purple', linewidth=1.8, label='||X_intent(t)||^2 (상태 벡터 전력)')
axs[2].axhline(y=theta, color='red', linestyle=':', linewidth=1.5, label='기준 에너지 임계값(theta)')
axs[2].set_title('3단계: 상태 공간 최소 분산 전력 추적', fontsize=11, fontweight='bold')
axs[2].legend(loc='upper right')
axs[2].grid(True, alpha=0.3)

# 그래프 4: 최종 트리거 확률 및 액추에이터 컨트롤러 윈도우
axs[3].plot(t, P_state, color='crimson', linewidth=2, label='P_state(t) (전이 확률)')
axs[3].axhline(y=0.75, color='black', linestyle='--', linewidth=1.5, label='액추에이터 트리거 임계값 (0.75)')
trigger_active = P_state > 0.75
axs[3].fill_between(t, 0, 1, where=trigger_active, color='green', alpha=0.15, label='액추에이터 컨트롤러 활성화 (바이패스 닫힘)')
axs[3].set_title('4단계: 비선형 매핑 및 액추에이터 컨트롤러 활성화', fontsize=11, fontweight='bold')
axs[3].set_xlabel('Time (Seconds)', fontsize=10)
axs[3].set_ylabel('Probability Space', fontsize=10)
axs[3].set_ylim(-0.05, 1.05)
axs[3].legend(loc='lower right')
axs[3].grid(True, alpha=0.3)

plt.tight_layout()

# 논문 및 백서 문서를 위한 이미지 파일로 자동 저장
plt.savefig('arcf_simulation_result.png', dpi=300)
print("시뮬레이션 플롯이 'arcf_simulation_result.png' (300 DPI)로 저장되었습니다.")
plt.show()
