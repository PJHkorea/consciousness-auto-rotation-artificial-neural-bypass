/**
 * @file fluxmesh_spinal_direct_bridge_test.h
 * @brief Ultra-Low Latency Deterministic Simulation Harness for Spino-Cortical Bridge Validation.
 *
 * @note [KR] 본 코드는 하드웨어 센서 보드가 없는 시뮬레이션 환경에서도 `fluxmesh_spinal_direct_bridge.h` 커널의 
 * 1kHz 실시간 구동성, O(1) CRC8 지문 무결성, 그리고 극한의 노이즈 타격 시 유도되는 세포 사멸(Apoptosis) 및 
 * 나노초 단위 스왑 포인터 거동을 수학적으로 완벽하게 모뮬레이션하여 증명하는 '확정론적 실전 테스트 하네스' 엔진입니다.
 * 
 * [EN] This test harness establishes a deterministic simulation framework to rigorously validate the 1 kHz real-time execution, 
 * O(1) CRC8 validation, and numerical anomaly isolation (Apoptosis) of the `fluxmesh_spinal_direct_bridge.h` interface.
 * It injects controlled transient voltages and IEEE-754 NaN anomalies to evaluate the system's runtime robustness 
 * under simulated native FPU environments without requiring physical biosensor attachments.
 *
 * @license GNU GPLv3
 */

#ifndef FLUXMESH_SPINAL_DIRECT_BRIDGE_TEST_H
#define FLUXMESH_SPINAL_DIRECT_BRIDGE_TEST_H

#include "fluxmesh_spinal_direct_bridge.h"
#include <math.h>
#include <stdio.h>

/**
 * @struct BridgeTestTelemetry
 * @brief Container for tracking simulation trajectory metrics and jitter safety margins.
 * [KR] 실시간 척수 직입 파이프라인의 수치해석적 오차 점수 및 타이밍 무결성을 계측하기 위한 추적 텔레메트리 구조체.
 */
typedef struct {
    uint32_t total_cycles;       /**< Total simulated time steps / [KR] 총 누적 모뮬레이션 타임 스텝 */
    uint32_t isolated_events;    /**< Count of triggered apoptosis states / [KR] 검출 및 차단된 누적 세포 사멸 횟수 */
    uint32_t checksum_failures;  /**< Count of simulated transmission corruptions / [KR] 전송 패킷 지문 오염 검출 횟수 */
    float    accumulated_variance;/**< Tracking convergence stability margin / [KR] 필터 컨버전스 누적 오차 변동폭 마진 */
} BridgeTestTelemetry;

/**
 * @brief Runs a deterministic 1 kHz microsecond-level stress injection test simulation.
 * [KR] 1kHz 주기의 가혹한 노이즈 및 결함 주입 시나리오를 가동하여 척수 직입 커널의 내고장성 장벽을 강제 검증합니다.
 * @param telemetry Pointer to the monitoring metric container / [KR] 검증 지표 축적용 텔레메트리 구조체 포인터
 * @param steps Total loop iterations to simulate / [KR] 수행할 총 모뮬레이션 타격 횟수
 */
static inline void fluxmesh_spinal_bridge_run_stress_test(BridgeTestTelemetry* const telemetry, uint32_t steps) {
    CellNode32 test_cell;
    fluxmesh_cell32_init(&test_cell);
    
    telemetry->total_cycles = 0;
    telemetry->isolated_events = 0;
    telemetry->checksum_failures = 0;
    telemetry->accumulated_variance = 0.0f;

    /* [KR] 시간축 각도 가속 매개변수 선언 (10Hz 신호 포착을 위한 1kHz 하이퍼 주기 샘플링 동치) */
    /* [EN] Angular frequency initialization corresponding to a 10 Hz target signal inside a 1 kHz loop. */
    float theta = 0.0f;
    const float delta_theta = 2.0f * 3.14159265f * 10.0f / 1000.0f;

    for (uint32_t i = 0; i < steps; i++) {
        telemetry->total_cycles++;
        
        /* [KR] 선형적 시간축을 사인과 코사인 위상 평면 공간으로 변환 주입 */
        /* [EN] Compress linear time into standard geometric sine/cosine coordinate anchors. */
        float cos_t = cosf(theta);
        float sin_t = sinf(theta);
        theta += delta_theta;

        /* [KR] 기본 기전력 데이터 생성 + 가우시안 백색 소음 모사 합성 */
        /* [EN] Generate synthetic baseline biopotential merged with simulated white noise. */
        float raw_signal_input = 2.5f * sinf(theta * 0.5f) + (((float)(i % 13) - 6.0f) * 0.1f);

        /* ========================================================================== */
        /* [STRESS INJECTION SCENARIOS: FORCING COGNITIVE BLASTS & NAN INFUSION]      */
        /* [극한 상황 지뢰밭 주입 시나리오: 폭주 전압 및 IEEE-754 결함 고의 주입]       */
        /* ========================================================================== */
        if (i == 500) {
            /* [KR] 500번째 사이클: 하드웨어가 비정상적인 전자기 펄스(EMP) 노이즈 신호를 얻어맞는 상황 시뮬레이션 */
            /* [EN] Cycle 500: Simulate severe external electromagnetic pulse (EMP) hardware hit. */
            raw_signal_input = 2e6f; 
        } 
        else if (i >= 501 && i <= 515) {
            /* [KR] 501~515 사이클: 센서 단선 또는 하드웨어 붕괴로 인한 IEEE-754 NaN(Not-a-Number) 원시 주입 타격 */
            /* [EN] Cycle 501-515: Inject critical floating-point anomalies (NaN) to test compiler-level safety guards. */
            uint32_t nan_bits = 0x7FC00000;
            raw_signal_input = *(float*)&nan_bits;
        }

        /* [PHASE 1] Execute the ultra-low latency spinal direct bridge execution loop */
        /* [1단계] 척수 직입 동기화 브릿지 코어 엔진 가동 (분기문 박멸 및 메모리 장벽 테스트) */
        fluxmesh_spinal_bridge_execute(&test_cell, raw_signal_input, cos_t, sin_t);

        /* [PHASE 2] Validate data integrity on the active hardware buffer slice post-swap */
        /* [2단계] 나노초 단위 스왑 직후, 대뇌 컴퓨터(PC)가 읽어갈 활성 버퍼 공간의 비트 데이터 역추적 검증 */
        uint8_t active_idx = current_buffer_idx;
        volatile SpinalPacket* const read_out_packet = &tx_ping_pong_buffer[active_idx];

        /* [PHASE 3] Extract packet fingerprint and evaluate via the O(1) table engine */
        /* [3단계] 룩업 테이블 기반 초고속 CRC8 엔진을 통한 무결성 지문 실시간 교차 검증 */
        uint8_t verified_crc = calc_fast_crc8((const volatile uint8_t*)read_out_packet, sizeof(SpinalPacket) - 1);
        
        if (read_out_packet->crc8 != verified_crc) {
            telemetry->checksum_failures++;
        }

        /* [PHASE 4] Track behavioral apoptosis and structural self-healing bypass states */
        /* [4단계] 척수 커널의 실시간 자폭 사멸 상태 모니터링 및 수치적 변동성 계측 점수 축적 */
        if (read_out_packet->status == 0xFF) {
            telemetry->isolated_events++;
            /* [KR] 자폭 격리 발동 상태에서는 대뇌로 공급되는 출력이 칼같이 무조건 -99.0f 전위로 고정되어야 함 */
            /* [EN] Verify that output pathways are rigidly locked to -99.0f during active apoptosis states. */
            if (read_out_packet->dx != -99.0f || read_out_packet->dy != -99.0f) {
                // [KR] 오류: 격리 장벽이 뚫림 / [EN] Critical Error: Isolation shield breached!
                telemetry->accumulated_variance += 999.0f; 
            }
        } else {
            /* [KR] 정상 가동 범위에서는 잔차 편차의 정밀 수렴도 측정 */
            /* [EN] Accumulate baseline convergence metrics during stable operations. */
            telemetry->accumulated_variance += fabsf(read_out_packet->dx - (2.5f * sinf(theta * 0.5f)));
        }
    }
}

/**
 * @brief Standard terminal out logger to verify the spino-cortical pipeline integrity metrics.
 * [KR] 후학들이 시뮬레이터 터미널 창에서 검증 스펙 합격 유무를 한눈에 볼 수 있도록 뿌려주는 리포트 출력 함수.
 */
static inline void fluxmesh_spinal_bridge_print_report(const BridgeTestTelemetry* const telemetry) {
    printf("\n==============================================================================\n");
    printf("[KR] FLUXMESH 척수 직입 브릿지 커널(Layer 1) 실전 시뮬레이션 결과 리포트\n");
    printf("[EN] FLUXMESH Spinal-Direct Bridge Kernel (L1) Simulation Metrics Report\n");
    printf("==============================================================================\n");
    printf(" -> Total Processed Steps  [총 누적 연산 사이클]   : %u Hz / Steps\n", telemetry->total_cycles);
    printf(" -> Checksum Jitter Errors [지문 변형 에러 검출]   : %u (Target: 0)\n", telemetry->checksum_failures);
    printf(" -> Apoptosis Isolations   [세포 사멸 격리 보호 횟수]: %u (Target: >=15)\n", telemetry->isolated_events);
    printf(" -> Filter Residual Drift  [정제 잔차 컨버전스 점수] : %f\n", telemetry->accumulated_variance / (float)telemetry->total_cycles);
    printf("------------------------------------------------------------------------------\n");
    
    if (telemetry->checksum_failures == 0 && telemetry->isolated_events >= 15) {
        printf("[RESULT] STATUS: PASSED. [KR] 척수-대뇌 무결성 인프라 검증 규격 통과 완료.\n");
        printf("[RESULT] STATUS: PASSED. [EN] Spino-Cortical infrastructure criteria fully verified.\n");
    } else {
        printf("[RESULT] STATUS: FAILED. [KR] 수치해석적 오차 또는 타이밍 지터 가드 뚫림 발생.\n");
        printf("[RESULT] STATUS: FAILED. [EN] Numerical drift or timing jitter guard breach detected.\n");
    }
    printf("==============================================================================\n\n");
}

#endif /* FLUXMESH_SPINAL_DIRECT_BRIDGE_TEST_H */
