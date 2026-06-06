/**
 * @file fluxmesh_cortical_resonance_engine_test.h (Part 1/2)
 * @brief High-Dimensional Matrix Convergence & Attractor Trajectory Test Harness (Cortical Layer)
 *
 * @note [KR] 본 코드는 하드웨어 물리 통신망이 결착되지 않은 시뮬레이션 환경에서도 `fluxmesh_cortical_resonance_engine.h` 커널의
 * O(1) 대뇌 CRC8 지문 차단벽, 척수 사멸 시 유도되는 대뇌 제어 흐름(Control Flow) 격리 성능, 그리고 고차원 교차항 행렬 복원의 
 * 수치해석적 오차 마진을 완벽하게 검증하고 실증해 내는 '대뇌 단 최상위 테스트 하네스' 엔진의 1부 명세입니다.
 * 
 * [EN] This is the Part 1 specification of the Layer-2 Cortical Test Harness. 
 * It establishes a deterministic validation framework to verify cross-term matrix reconstruction, 
 * O(1) cortical checksum gating, and control flow isolation under simulated spinal apoptosis conditions.
 *
 * @license GNU GPLv3
 */

#ifndef FLUXMESH_CORTICAL_RESONANCE_ENGINE_TEST_H
#define FLUXMESH_CORTICAL_RESONANCE_ENGINE_TEST_H

#include "fluxmesh_cortical_resonance_engine.h"
#include <stdio.h>
#include <math.h>

/**
 * @struct CorticalTestTelemetry
 * @brief Metric tracker for host-layer matrix determinant scaling and AI attractor convergence.
 * [KR] 복원된 고차원 행렬의 수치적 판별식 오차 마진 및 AI 맥락 추론 어트랙터의 정상 장기 수렴도를 계측하는 대뇌 전용 텔레메트리 구조체.
 */
typedef struct {
    uint32_t total_packets;       /**< Total processed inbound streams / [KR] 총 누적 수신 처리된 척수 패킷 개수 */
    uint32_t rerouted_cycles;     /**< Count of host autonomic loop isolations / [KR] 척수 사멸로 인해 대뇌 자율 우회가 발동된 누적 횟수 */
    double   max_matrix_drift;    /**< Maximum mathematical determinant error / [KR] 복원된 고차원 행렬 교차항의 최대 수치 해석적 드리프트 편차 */
    double   avg_attractor_power; /**< Long-term AI context reasoning stability / [KR] 장기 가동 시 AI 맥락 가중치 어트랙터의 평균 활성 파워 */
} CorticalTestTelemetry;

/**
 * @brief Initializes the Cortical Test Telemetry container.
 * [KR] 대뇌 검증용 텔레메트리 구조체를 완전히 무결한 제로 상태로 초기화합니다.
 * @param telemetry Pointer to the target metric tracker / [KR] 초기화 대상 대뇌 텔레메트리 포인터
 */
static inline void fluxmesh_cortical_test_init(CorticalTestTelemetry* const telemetry) {
    telemetry->total_packets = 0;
    telemetry->rerouted_cycles = 0;
    telemetry->max_matrix_drift = 0.0;
    telemetry->avg_attractor_power = 0.0;
}

#endif /* FLUXMESH_CORTICAL_RESONANCE_ENGINE_TEST_H (Part 1 End) */
/**
 * @file fluxmesh_cortical_resonance_engine_test.h (Part 2/2)
 * @brief Host Attractor Stress Simulator Loop and Certification Report Generation.
 *
 * @note [KR] 본 코드는 척수 단말기(Layer 1)의 결함 상태와 정상 데이터를 교차 합성하여 대뇌 커널에 타격 유입시키고, 
 * 복원된 행렬 교차항 성분 디터미넌트의 정밀 거동을 추적하여 최종 합격 규격 리포트를 출력하는 2부 핵심 본체입니다.
 * 
 * [EN] This is the Part 2 component of the Layer-2 Cortical Test Harness. 
 * It runs a deterministic 1 kHz execution loop, synthesizing packet injections containing floating-point anomalies 
 * to confirm that the host AI context reasoning pipeline remains strictly stable under simulated native FPU workloads.
 */

#ifndef FLUXMESH_CORTICAL_RESONANCE_ENGINE_TEST_PART2_H
#define FLUXMESH_CORTICAL_RESONANCE_ENGINE_TEST_PART2_H

#include "fluxmesh_cortical_resonance_engine_test.h"

/**
 * @brief Runs a deterministic spino-cortical coupling verification and matrix reconstruction stress test.
 * [KR] 대뇌 호스트 수신 커널에 가혹한 패킷 결함 변칙 시나리오를 주입하여, 고차원 행렬 자율 복원 무결성을 실증합니다.
 * @param telemetry Pointer to the host monitoring metric tracker / [KR] 검증 지표 축적용 대뇌 텔레메트리 구조체 포인터
 * @param total_steps Total packet injection count to evaluate / [KR] 수행할 총 가상 패킷 스트림 주입 횟수
 */
static inline void fluxmesh_cortical_run_stress_test(CorticalTestTelemetry* const telemetry, uint32_t total_steps) {
    CorticalResonanceField test_field;
    fluxmesh_cortical_init(&test_field);
    
    fluxmesh_cortical_test_init(telemetry);
    double cumulative_attractor = 0.0;

    for (uint32_t i = 0; i < total_steps; i++) {
        InboundSpinalPacket packet;
        packet.sync = SPIN_SYNC_HEADER;
        packet.node_id = 0x01;
        packet.status = 0x00;
        packet.sequence = i;
        
        /* [KR] 척수의 조셉 폼 스칼라 신뢰도 마진 상태 가상 동기화 변수 유도 */
        packet.p00 = 1.0f / (1.0f + ((float)i * 0.0001f)); 

        /* [KR] 1kHz 샘플링 주기 하위에서 전진하는 물질세계의 가상 동역학 시간축 회전 좌표계 생성 */
        float theta = 2.0f * 3.14159265f * 10.0f / 1000.0f * (float)i;
        packet.dx = 2.5f * sinf(theta);
        packet.dy = 2.5f * cosf(theta);

        /* ========================================================================== */
        /* [CORTICAL GEOMETRIC DESTABILIZATION SIMULATION INJECTIONS]                */
        /* [대뇌 기하학적 파괴 지뢰밭 시나리오: 척수 사멸 및 극단적 사망 전위 강제 유입]   */
        /* ========================================================================== */
        if (i >= 300 && i <= 320) {
            /* [KR] 300~320 사이클: 말초 피폭으로 인한 척수 노드 사멸(0xFF) 및 사망 플래그(-99.0f) 수신 상황 강제 합성 */
            /* [EN] Cycle 300-320: Inject simulated spinal node apoptosis (0xFF) and explicit death boundaries (-99.0f). */
            packet.status = 0xFF;
            packet.dx = -99.0f;
            packet.dy = -99.0f;
        }

        /* [KR] 256바이트 분기 박멸 대뇌 테이블 엔진을 역구동하여 무결한 전송 패킷 지문(CRC8)을 선제 날인 */
        /* [EN] Compute and attach valid J1850 protocol check byte via the branchless cortical lookup engine. */
        uint8_t pre_crc = 0x00;
        const uint8_t* raw_bytes = (const uint8_t*)&packet;
        for (size_t j = 0; j < sizeof(InboundSpinalPacket) - 1; j++) {
            pre_crc = cortical_crc8_table[pre_crc ^ raw_bytes[j]];
        }
        packet.crc8 = pre_crc;

        /* [PHASE 1] Stream the prepared 24-byte packet frame into the Layer-2 Cortical Ingestion Core */
        /* [1단계] 준비된 패킷 가방을 64비트 대뇌 공명 커널 내부로 직분사 주입 가동 */
        bool is_processed = fluxmesh_cortical_ingest_packet(&test_field, &packet);
        if (!is_processed) continue;

        telemetry->total_packets++;

        /* [PHASE 2] Evaluate cortical flow dominance and autonomic self-healing loop status */
        /* [2단계] 척수 세포 사멸 경고 플래그 작동 시 대뇌의 제어 흐름(Control Flow) 격리 격벽 작동성 실증 */
        if (test_field.is_spinal_dead) {
            telemetry->rerouted_cycles++;
            /* [KR] 자율 우회 상태에서는 대뇌 고차원 공명 에너지가 수치적으로 칼같이 무조건 0.0000000000000000 상태로 마감되어야 함 */
            /* [EN] Ensure resonance energy is rigidly locked to exactly 0.0 when control flow redirection is triggered. */
            if (test_field.resonance_energy != 0.0 || test_field.P_mat != 0.0 || test_field.P_mat != 0.0) {
                telemetry->max_matrix_drift += 9999.0; // 격리벽 유실 에러 축적
            }
        } else {
            /* [PHASE 3] Track the high-dimensional matrix reconstruction numerical convergence drift */
            /* [3단계] 정상 가동 스케일 범위 내에서 복원된 교차항 행렬의 디터미넌트 해석적 누적 드리프트 편차 역추적 계측 */
            /* [KR] 이론값 수식: p00*p11 - p01*p10 -> p00^2 - (dx*dy*0.01)^2과의 실시간 수치 마진 비교 */
            double expected_det = ((double)packet.p00 * (double)packet.p00) - (field_p01_val * field_p01_val);
            double actual_det = (test_field.P_mat * test_field.P_mat) - (test_field.P_mat * test_field.P_mat);
            double current_drift = fabs(actual_det - expected_det);
            
            if (current_drift > telemetry->max_matrix_drift) {
                telemetry->max_matrix_drift = current_drift;
            }
            cumulative_attractor += test_field.context_weight;
        }
    }

    if (telemetry->total_packets > telemetry->rerouted_cycles) {
        telemetry->avg_attractor_power = cumulative_attractor / (double)(telemetry->total_packets - telemetry->rerouted_cycles);
    }
}

/**
 * @brief Diagnostic reporter to verify the Cortical Resonance pipeline integrity specifications.
 * [KR] 후학들이 대뇌 수신 파이프라인의 행렬 복원 신뢰도 통과 유무를 한눈에 볼 수 있도록 터미널 창에 뿌려주는 최종 규격 성적표 함수.
 */
static inline void fluxmesh_cortical_print_report(const CorticalTestTelemetry* const telemetry) {
    printf("\n==============================================================================\n");
    printf("[KR] FLUXMESH 대뇌 공명장 AI 추론 커널(Layer 2) 실전 시뮬레이션 결과 리포트\n");
    printf("[EN] FLUXMESH Cortical Resonance AI Engine (L2) Simulation Metrics Report\n");
    printf("==============================================================================\n");
    printf(" -> Total Ingested Packets [총 누적 수신 완료 패킷] : %u Steps\n", telemetry->total_packets);
    printf(" -> Autonomic AI Reroutes  [대뇌 자율 우회 제어 횟수]: %u (Target: ==21)\n", telemetry->rerouted_cycles);
    printf(" -> Max Matrix Atten Drift [복원 행렬 최대 수치 오차] : %.15f\n", telemetry->max_matrix_drift);
    printf(" -> Avg Attractor Power    [AI 맥락 추론 장기 활성도] : %.10f\n", telemetry->avg_attractor_power);
    printf("------------------------------------------------------------------------------\n");
    
    /* 10⁻¹² 미만의 무시할 수 있는 배정밀도 반올림 누적 편차 가드 판정 규칙 확정 */
    if (telemetry->max_matrix_drift < 1e-12 && telemetry->rerouted_cycles == 21) {
        printf("[RESULT] STATUS: PASSED. [KR] 대뇌 고차원 행렬 복원 및 AI 맥락 연동 검증 규격 통과 완료.\n");
        printf("[RESULT] STATUS: PASSED. [EN] Cortical high-dimensional matrix integration fully verified.\n");
    } else {
        printf("[RESULT] STATUS: FAILED. [KR] 고차원 행렬 판별식 발산 또는 제어 흐름 격리 실패 발생.\n");
        printf("[RESULT] STATUS: FAILED. [EN] High-dimensional matrix divergence or flow control leak detected.\n");
    }
    printf("==============================================================================\n\n");
}

#endif /* FLUXMESH_CORTICAL_RESONANCE_ENGINE_TEST_PART2_H */
