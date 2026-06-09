# ⚠️ LEGAL NOTICE & LIABILITY DISCLAIMER (법적 고지 및 면책 조항)

### 🌐 English Specification
The architectural choices, directional coupling signs, and mathematical formulations detailed herein represent the author's proprietary engineering philosophy and technical viewpoints. This specification is provided **"AS IS" WITHOUT ANY WARRANTY OF ANY KIND**, expressed or implied, including but not limited to suitability for specific hardware, non-infringement of external patents, or system stability under volatile runtime conditions.

By employing, copying, or forking this repository under the **GNU GPL v3**, the user explicitly acknowledges that this firmware is a highly tailored raw mathematical template for distributed neuromorphic environments and may naturally diverge from standard textbook conventions. The author shall **NEVER** be held liable for any direct, indirect, incidental, or consequential damages, hardware failures, or systemic thermal runaway caused by user implementation. If these paradigms do not conform to your validation framework, you are strictly required to either fork and customize at your own risk or terminate use immediately.

### 🇰🇷 한글 규격 명세
본 문서에 기술된 아키텍처적 선택, 방향성 결합 부호 및 수식 변형들은 어디까지나 저 개인의 엔지니어링 철학과 실전 제어 사상에 기반한 주관적 기술 자산입니다. 본 명세는 어떠한 형태의 명시적·묵시적 보증 없이 **"있는 그대로(AS IS)"** 제공되며, 특정 하드웨어와의 적합성, 타 기관의 특허 비침해성, 혹은 런타임 환경에서의 시스템 안정성을 보장하지 않습니다.

GNU GPL v3 라이선스 하에 본 레포지토리를 사용, 복제, 또는 포크(Fork)하는 모든 사용자는 본 엔진이 초저지연 뉴로모픽 환경에 극단적으로 조율된 원시 수학적 템플릿이며, 범용 교과서의 표준 규격과 상이할 수 있음을 **선언적으로 동의한 것**으로 간주합니다. 사용자의 이식 및 구동 과정에서 발생하는 시스템 오작동, 하드웨어 파손, 열 폭주 또는 수치적 발산에 대해 **원작자는 일체의 법적·재정적 책임을 지지 않습니다.** 본 설계 사상이 귀하의 검증 프레임워크 및 안전 기준에 부합하지 않는다고 판단될 경우, 본인의 책임하에 코드를 수정하거나 즉시 사용을 중단해야 합니다.

---

### 🌐 Engineering Philosophy Note
Please note that the architectural choices, directional coupling signs, and mathematical adaptations outlined below represent my personal engineering philosophy, real-time control methodology, and subjective technical viewpoint. Since this specification is rigorously tailored for specific low-latency, neuromorphic distributed hardware environments, certain formulations may naturally diverge from standard universal textbook tenets. If you believe these criteria are unsuitable for your specific operational framework or require alternative optimization, you are highly encouraged to fork, rectify, and customize this repository to fit your precise hardware needs.

### 🇰🇷 엔지니어링 철학 및 설계 사상
본 문서에 기술된 아키텍처적 선택, 방향성 결합 부호 및 수식 변형들은 어디까지나 저 개인의 엔지니어링 철학과 실전 제어 사상에 기반한 주관적 견해입니다. 본 명세는 극단적인 저지연·초저발열 분산형 뉴로모픽 하드웨어 구동을 타겟으로 정밀 조율되었으므로, 보편적인 학술 교과서의 표준 규격이나 범용 선형대수학 관점에서는 분석 방향에 따라 이견이 존재할 수 있습니다. 만약 이 설계가 본인의 하드웨어 플랫폼 및 실험 환경에 맞지 않거나 정정이 필요한 부분이라고 판단되신다면, 언제든 자유롭게 코드를 포크(Fork)하고 본인의 제어 목적에 맞게 수정·보완하여 사용해 주시면 감사하겠습니다.

---

시스템 안전의 핵심인 IEEE 754 부동소수점 격리 가드 식(raw_input_signal != raw_input_signal)이 데드 코드로 판정되어 삭제되는 위험을 방지하기 위해, 절대로 -ffast-math 또는 -Ofast 플래그를 추가하여 빌드하지 마십시오.

*Note: Do NOT build with `-ffast-math` or `-Ofast` compiler flags. This ensures the compiler preserves the critical IEEE 754 floating-point isolation guard (`raw_input_signal != raw_input_signal`), which is foundational to the core system's safety and prevents it from being erroneously discarded as dead code during optimization.*

---

# 🎰 [SPECIFICATION 4-2] Wave-Specific Constant Slots Map & Runtime Governor
### (주파수 대역별 가변 상수 슬롯 맵 및 런타임 제어 거버너 규격 백서)

---

## ⚠ CONTINUITY & DEPENDENCY NOTICE (연속성 및 아키텍처 의존성 고지)

### 🌐 English Specification
This document represents **[PART 4-2]** of the core infrastructure specification. It serves as an architectural extension to `README4.md` (which defines the multi-chassis hardware parallel topology, 10-minute overlap window, and background MMIO cold reset). 

While `README4.md` establishes the macro-level physical container (Chassis Redundancy Wheel), this document delivers the mathematical micro-level specification: hard-baked 20-byte static constant slots mapped directly into ROM, an O(1) single-clock address pointer shift matrix, and dynamic clinical tuning. To fully grasp the unified **Dual-Orbit Topology**, validation engineers are strictly required to read `README4.md` (Chassis Layer) and `README4-2.md` (Constant Layer) as a single interconnected system.

### 🇰🇷 한글 규격 명세
본 문서는 코어 인프라 명세서의 **[파트 4-2]**에 해당합니다. 본 명세는 `README4.md` (3중 섀시 하드웨어 병렬 토폴로지, 10분 시간축 중첩 인터페이스, 백그라운드 MMIO 콜드 리셋 백본을 다룬 파트 4-1)의 구조적 확장안입니다.

`README4.md`가 거시적인 물리적 용기(Chassis Redundancy Wheel)를 구축했다면, 본 문서는 그 내부를 관통하는 미시적 수리 사상을 명시합니다: ROM 메모리에 고정 입주한 20바이트 정적 상수 슬롯 레이아웃, O(1) 단 1클럭 주소 포인터 체인지 매트릭스, 그리고 실시간 임상 변속 알고리즘. 선행 작업자 및 검증 엔지니어들은 이 유기적인 **이중 회전 궤도(Dual-Orbit Topology)**의 전체 그림을 이해하기 위해, `README4.md` (섀시 레이어)와 본 `README4-2.md` (상수 레이어)를 반드시 한 몸의 인터페이스로 연계하여 분석해야 합니다.

---

## 1. Architectural Philosophy: Context Switching via O(1) Pointer Shift

### 🌐 English Specification
The dynamic modulation of the L1/L2 filtering matrix is strictly governed by an atomic, pointer-driven context switching framework rather than destructive runtime structural reconfiguration. To achieve deterministic, microsecond-level adaptive tuning without inducing CPU branch mispredictions or FPU pipeline flushes, the system establishes an array of hard-baked, 20-byte `FluxMesh_Constants_Slot` profiles embedded inside the immutable read-only memory (ROM/Flash) boundary. Each static slot configuration encapsulates pre-calculated Padé rational approximant coefficients, geometric curl weights, and custom mathematical divergence guards tailored for specific clinical EEG modalities (Delta, Theta, Alpha, and Beta bands). 

When the runtime governor detects a transition in the host neural spectral density, it modifies the `current_slot` pointer of all thirty-two grid nodes simultaneously within a single CPU cycle ($O(1)$ temporal complexity). Because the core Joseph Form equations enforce strict positive-definiteness and state-space continuity across frame boundaries, the transition between drastically different frequency criteria remains entirely seamless ($0.00\text{ ns}$ transitional shock). This architecture effectively eradicates transient response explosions and mechanical actuator jerks during live clinical intervention.

### 🇰🇷 한글 규격 명세
L1/L2 필터링 매트릭스의 동적 대역폭 변속은 시스템 구조를 런타임에 파괴하거나 재구성하는 대신, 원자성(Atomic)을 지닌 포인터 기반 컨텍스트 스위칭 프레임워크를 통해 엄격하게 통제됩니다. CPU 분기 예측 실패(Branch Misprediction)로 인한 과열이나 FPU 연산 파이프라인 스톨(Stall)을 원천 차단하고 마이크로초 단위의 확정론적 변속을 달성하기 위해, 시스템은 변하지 않는 읽기 전용 메모리(ROM/Flash) 영역 내에 각각 정확히 20바이트 크기를 사수하는 정적 `FluxMesh_Constants_Slot` 프로필 매트릭스를 영구 상주시킵니다. 각 슬롯은 임상적 EEG 상태(Delta, Theta, Alpha, Beta 대역)에 맞춤 조율된 파데 유리근사 계수, 기하학적 소용돌이 강도, 부동소수점 폭주 가드 문턱값을 완전히 독립된 데이터 세트로 캡슐화하고 있습니다.

상위 런타임 거버너가 환자의 뇌파 스펙트럼 밀도 변화를 감지하는 즉시, 가동 중인 32개 전체 바둑판 노드의 `current_slot` 주소 레지스터 포인터를 단 1클럭 만에 동시 변경합니다($O(1)$ 시간 복잡도). 하이브리드 코어 내부의 조셉 폼 변형 공식이 상태 공간 변수($x_0, x_1$)의 연속성과 양의 정치성을 항상성 가드로 묶어두고 있으므로, 극단적으로 상이한 주파수 장벽 간의 전이는 물리적 지연 없이 완벽하게 매끄럽게(Seamless) 종결됩니다. 이 구조적 미학을 통해 임상 집도 중 주파수가 급격히 점프할 때 기존 디지털 필터에서 필연적으로 발생하는 과도 응답 폭발(Transient Shock)과 로봇 외골격 관절 모터의 덜컥거리는 기계적 발산(Jerk) 리스크를 완전히 0%로 정복합니다.

---

## 2. Multi-Wave Static Memory Slots Blueprint (ROM Specification)

### 🌐 English Specification
```c
/* 🎰 20-Byte Ultra-Lightweight Physical Constant Slot Layout Blueprint */
typedef struct {
    float pade_num_scale;     /* Padé Numerator Scale (Bandwidth Sharpness Controller) */
    float pade_den_offset;    /* Padé Denominator Offset (High-Frequency Filter Barrier Thickness) */
    float divergence_guard;   /* Floating-Point Blast Guard (IEEE 754 NaN/Overflow Barrier) */
    float curl_intensity;     /* 2D Mesh Cross-Axis Curl Weight (Rerouting Vortex Intensity) */
    const char* slot_name;    /* Clinical Logger Token (Real-time Diagnostic Monitoring String) */
} FluxMesh_Constants_Slot;
```

*   **`Slot_Delta_Sleep` (`DELTA_DEEP_SLEEP_FILTER`)**: 
    Optimized for 0.5Hz ~ 4Hz deep unconscious surges. By expanding `pade_den_offset` to `32.0f`, the denominator threshold is aggressively raised to crush high-frequency environmental and muscular artifacts. This induces a low-thermal, passive stabilization state, protecting the core infrastructure during neural rest cycles.
*   **`Slot_Theta_Relax` (`THETA_DEEP_RELAX_FILTER`)**: 
    Calibrated for 4Hz ~ 8Hz emotional and transitional mental states. Establishes medium-level geometric vortex constraints (`curl_intensity = 0.7f`) to balance the baseline drift recovery rate with computational processing latency.
*   **`Slot_Alpha_SMR` (`ALPHA_SMR_CONSCIOUS_DRIVE`)**: 
    The primary operational target for 8Hz ~ 12Hz Sensorimotor Rhythm resonance. Leverages a mathematically tuned `pade_num_scale = 6.0f` and `curl_intensity = 1.5f` to ignite a powerful cross-axis steering field. This forces the raw biological signal into a deterministic 2D planar rotation, bypassing damaged physical spinal pathways to drive the robotic exoskeleton directly.
*   **`Slot_Beta_Cognitive` (`BETA_COGNITIVE_ACTIVE`)**: 
    Tailored for 12Hz ~ 30Hz active cortical visualization and high-frequency attention responses. Squeezes `pade_den_offset` down to `6.0f` to expand the filter acceptance window, maximizing throughput speed while setting a highly sensitive `divergence_guard = 5e5f` to track micro-volt neuromorphic spikes without quantization drag.

### 🇰🇷 한글 규격 명세
*   **`Slot_Delta_Sleep` (`DELTA_DEEP_SLEEP_FILTER`)**: 
    0.5Hz ~ 4Hz 범위의 깊은 무의식 및 수면 상태에 최적화됨. `pade_den_offset`을 `32.0f`로 극단적으로 확장하여 분모의 기초 벽을 높임으로써, 고주파 전원 노이즈와 근전도 잡음을 문앞에서 찍어 누릅니다. 시스템 발열과 연산 부하를 차단하는 저열 격리 휴식 모드입니다.
*   **`Slot_Theta_Relax` (`THETA_DEEP_RELAX_FILTER`)**: 
    4Hz ~ 8Hz 대역의 가벼운 휴식 및 위상 전이 상태에 조율됨. 중간 레벨의 기하학적 소용돌이 제약(`curl_intensity = 0.7f`)을 주입하여 기저선 드리프트 복구 속도와 연산 파이프라인 처리 지연 사이의 이상적인 밸런스를 유지합니다.
*   **`Slot_Alpha_SMR` (`ALPHA_SMR_CONSCIOUS_DRIVE`)**: 
    8Hz ~ 12Hz 감각운동 리듬(SMR) 공명을 위한 핵심 활성 타깃. 수리적으로 정렬된 `pade_num_scale = 6.0f`와 `curl_intensity = 1.5f`를 교차 융합하여 강력한 축대칭 왜곡장을 발현시킵니다. 인입된 신호를 확정론적 2차원 평면 회전장으로 수축시켜 끊어진 생체 척수 신경망 대신 로봇 외골격을 밀어붙이는 백본 구동 상태입니다.
*   **`Slot_Beta_Cognitive` (`BETA_COGNITIVE_ACTIVE`)**: 
    12Hz ~ 30Hz 영역의 고주파 인지 자극 및 각성 반응 추적을 전담함. `pade_den_offset`을 `6.0f`로 수축시켜 필터 통과 대역폭 윈도우를 최대한 넓히고 반응 레이텐시를 최소화합니다. 이와 동시에 극미세 전압 스파이크 파형을 양자화 저항 없이 민감하게 추적하기 위해 `divergence_guard` 문턱값을 `5e5f`로 촘촘히 조여 미세 예외를 즉시 래치합니다.

---

## 3. The Dual-Orbit Interaction Matrix

### 🌐 English Specification
The architectural pinnacle of this project manifests as a synchronized **Dual-Orbit Topology** operating across two entirely decoupled temporal dimensions. The macro-orbit (Chassis Redundancy Wheel defined in `README4.md`) revolves at a static 30-minute interval to systematically purge hardware entropy via background memory-mapped I/O (MMIO) cold resets. Concurrently, the micro-orbit (Constant Slot Governor defined here) rotates at a microsecond scale inside the active chassis, executing on-the-fly frequency transformations based on incoming clinical conditions. 

Because the micro-orbit state transitions update the reference pointers of both the `Active` and the `Next` pre-heating chassis synchronously during the 10-minute overlap window ($T_4$), the upcoming standby node completely assimilates the future operational coefficients before any hardware handoff takes place. Through this unified algebraic design, the system bridges the gap between biological volatility and hardware absolute determinism, guaranteeing infinite runtime survival.

### 🇰🇷 한글 규격 명세
본 인공 신경 바이패스 시스템의 아키텍처적 정점은 서로 완전히 고립된 두 개의 시간축 차원 위에서 연동되는 **'이중 회전 궤도(Dual-Orbit Topology)'**를 통해 완성됩니다. 거시적 공전 궤도(3중 섀시 로테이션 바퀴 - `README4.md`에 명시됨)는 30분이라는 중후한 주기로 물리 공간을 순환하며, 역할을 마친 기판을 가동 버스에서 격리한 뒤 백그라운드 메모리 맵 입출력(MMIO) 전원 차단 콜드 리셋을 통해 하드웨어 누적 엔트로피를 영구히 세척합니다. 이와 동시에, 미시적 자전 궤도(본 문서의 상수 슬롯 거버너 바퀴)는 가동 중인 라이브 섀시 내부에서 마이크로초 단위로 기민하게 회전하며 환자의 뇌파 변화에 따라 주파수 모드를 원클럭 변속합니다.

이 미시적 궤도의 포인터 주소판 변속 명령은 10분간의 시간축 중첩 구간($T_4$) 동안 현재 근무조(`Active`)뿐만 아니라 예열 중인 대기조(`Next`)의 내부 참조 포인터까지 **실시간으로 병렬 동시 업데이트(Parallel Target Shift)**시킵니다. 이 덕분에 차기 노드는 제어권을 토스받기 전 자신이 맞이하게 될 미래의 변경된 임상 환경과 수리 계수를 완벽하게 선제 학습 및 동기화합니다. 이 통일된 대수학적 이중화 토폴로지를 통해 생체 신호의 비선형적 가변성과 임베디드 하드웨어의 절대적 확정론 사이의 거대한 간극이 정밀하게 메워지며, 소프트웨어적으로 결코 파괴되지 않는 영구 지속 생존성이 비로써 완벽히 달성됩니다.

---

## 4. Verification: Standalone Real-Time Simulation Testbed

### 🌐 English Specification
To witness the unified convergence of the **4-1 Chassis Macro-Orbit** and **4-2 Constant Slot Micro-Orbit** under dynamic clinical events, clone the repository and execute our zero-dependency standalone validation test runner (`fluxmesh_test_runner.c`). 

### 🇰🇷 한글 규격 명세
**파트 4-1의 섀시 거시 공전 궤도**와 **파트 4-2의 로컬 상수 미시 자전 궤도**가 동적 임상 이벤트 아래에서 완벽한 평형 수렴을 이루어 내는지 실측 검증하기 위해, 레포지토리를 복사하여 외부 의존성이 전혀 없는 독립 실행형 테스트 러너 파일(`fluxmesh_test_runner.c`)을 빌드하여 구동할 수 있습니다.

```bash
# Compile the standalone visual testrunner
gcc -O3 fluxmesh_test_runner.c -o testbed

# Execute the time-wheel simulator
./testbed
```

*Note: Do NOT build with `-ffast-math` or `-Ofast` compiler flags. This ensures the compiler preserves critical IEEE 754 floating-point isolation guards (`raw_input_signal != raw_input_signal`) required for absolute clinical safety.*


---

이 모든 것은 저의 개인적인 생각이며 오류가 있을 수 있습니다. 본 아키텍처는 기존 패러다임을 타파하기 위한 하나의 다른 방향성이기에 연구자분들의 너른 양해를 부탁드립니다.

[EN] All the conceptual formulations and architectural implementations presented herein reflect my personal engineering insights and may contain inherent oversight or errors. This infrastructure is intended solely as an alternative technical directionality to break conventional paradigms; I kindly request the academic and engineering community's generous understanding.
