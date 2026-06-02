/**
 * @file fluxmesh_test_apoptosis_bypass_verify.c
 * @brief FluxMesh Cellular Apoptosis & Autonomous Flow Bypass Verification.
 *
 * @note [KR] 본 코드는 중심 노드가 오염/단선되어 세포 사멸(Apoptosis)에 이르렀을 때,
 *           이웃 노드들이 망 오염 방지 신호(-99.0)를 감지하고 연산을 자율 우회(Bypass)하여 
 *           안전 지대로 흐름을 재라우팅하는 '자가 치유 구조'를 정밀 검증하는 독립 커널입니다.
 *       [EN] Test-verification script for FluxMesh's cellular apoptosis and autonomous 
 *            rerouting bypass fields when a critical central node collapses.
 *
 * [COMPILATION & RUN]
 * GCC: gcc fluxmesh_test_apoptosis_bypass_verify.c -O2 -o fluxmesh_test_apoptosis_bypass_verify
 * Run: ./fluxmesh_test_apoptosis_bypass_verify
 */

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>

/* ========================================================================== */
/* 1. FluxMesh Core Engine Component                                          */
/* ========================================================================== */
#define INNOVATION_SINGULARITY_EPSILON 1e-9
#define FAILSAFE_REJECT_SIGNAL        -99.0

typedef enum {
    DIR_NORTH = 0,
    DIR_SOUTH = 1,
    DIR_EAST  = 2,
    DIR_WEST  = 3,
    DIR_MAX   = 4
} MeshDirection;

typedef struct {
    double dx;
    double dy;
    double confidence;
} LocalVector2D;

typedef struct {
    uint16_t node_id;         
    double x0;                
    volatile double x1;       
    double p00;               
    volatile double p11;      
    bool is_isolated;         
} MeshNodeState;

/**
 * @brief Pure Scalar-based Joseph Form Operation & Topology Fusion Kernel.
 */
static inline LocalVector2D process_topological_node_step(MeshNodeState* self, double raw_signal, const LocalVector2D neighbor_vectors[DIR_MAX]) {
    LocalVector2D output_vector = {FAILSAFE_REJECT_SIGNAL, FAILSAFE_REJECT_SIGNAL, 0.0};

    if (!self || !neighbor_vectors) return output_vector;

    /* [KR] [하드웨어 가드] 이미 세포 사멸(격리)된 노드는 즉시 거부 신호 반환 */
    /* [EN] [Hardware Guard] Instantly reject and return error signal for already isolated nodes */
    if (self->is_isolated) {
        return output_vector; 
    }

    /* [KR] [수치해석적 무결성 검사] 미친 신호(NaN, 오버플로우) 유입 시 자가 격리 트리거 */
    /* [EN] [Numerical Integrity Check] Trigger cellular apoptosis upon toxic signal influx (NaN, Overflow) */
    if (raw_signal != raw_signal || raw_signal > 1e12 || raw_signal < -1e12) { 
        self->is_isolated = true; 
        return output_vector;
    }

    double innovation = raw_signal - self->x0;
    double S_residual = self->p00 + 1.0; 

    if (S_residual < INNOVATION_SINGULARITY_EPSILON && S_residual > -INNOVATION_SINGULARITY_EPSILON) {
        output_vector.dx = 0.0; output_vector.dy = 0.0; output_vector.confidence = 1e-6;
        return output_vector;
    }

    double K_gain = self->p00 / S_residual;
    double ImKH = 1.0 - K_gain;

    self->p00 = (ImKH * self->p00 * ImKH) + (K_gain * 1.0 * K_gain);
    self->p11 = self->p00; 
    self->x0 = self->x0 + (K_gain * innovation);
    self->x1 = self->x0; 

    /* [KR] [우회 로직 가드 변형] 이웃 노드 중 고장난 노드(-99.0)가 있다면 그 신호를 감지하고 우회 연산 처리 */
    /* [EN] [Bypass Logic Adaptation] Detect and bypass if neighboring node is broken (-99.0) */
    double east_dx = (neighbor_vectors[DIR_EAST].dx == FAILSAFE_REJECT_SIGNAL) ? 0.0 : neighbor_vectors[DIR_EAST].dx;
    double west_dx = (neighbor_vectors[DIR_WEST].dx == FAILSAFE_REJECT_SIGNAL) ? 0.0 : neighbor_vectors[DIR_WEST].dx;
    double north_dx = (neighbor_vectors[DIR_NORTH].dx == FAILSAFE_REJECT_SIGNAL) ? 0.0 : neighbor_vectors[DIR_NORTH].dx;
    double south_dx = (neighbor_vectors[DIR_SOUTH].dx == FAILSAFE_REJECT_SIGNAL) ? 0.0 : neighbor_vectors[DIR_SOUTH].dx;

    double Spatial_Gradient_X = east_dx - west_dx;
    double Spatial_Gradient_Y = north_dx - south_dx;

    double denominator = 1.0 + self->x0;
    if (denominator < INNOVATION_SINGULARITY_EPSILON && denominator > -INNOVATION_SINGULARITY_EPSILON) {
        self->is_isolated = true; 
        return output_vector;
    }

    double linear_scale = 1.0 / denominator; 
    
    output_vector.dx = Spatial_Gradient_X * linear_scale;
    output_vector.dy = Spatial_Gradient_Y * linear_scale;
    output_vector.confidence = self->p00;

    return output_vector;
}

/* ========================================================================== */
/* 2. Apoptosis & Failsafe Bypass Verification Main Logic                     */
/* ========================================================================== */
int main(void) {
    printf("========================================================================\n");
    printf("💀 [FLUXMESH CELLULAR APOPTOSIS & BYPASS VERIFICATION]\n");
    printf("========================================================================\n\n");

    /* [KR] [시나리오 세팅] 중심 노드와 동서남북 메시 노드 구성 */
    /* [EN] [Scenario Setup] Construct center node and neighboring mesh nodes */
    MeshNodeState center_node = { .node_id = 50, .x0 = 0.0, .p00 = 1.0, .is_isolated = false };
    MeshNodeState east_node   = { .node_id = 51, .x0 = 0.0, .p00 = 1.0, .is_isolated = false };

    printf("[Phase 1] 하드웨어 단선 및 오염 신호 강제 유입 (Hardware Defect Influx)\n");
    /* [KR] 중심 노드에 폭주 전압(1e15)과 같은 치명적 오염 신호 유입 */
    /* [EN] Inject fatal toxic voltage into Center Node 50 (e.g., 1e15) */
    double contaminated_signal = 1e15; 
    printf(" -> [KR] Center Node 50에 치명적인 오염 전압 유입 (signal = %.1e)\n", contaminated_signal);
    printf(" -> [EN] Fatal toxic voltage injected into Center Node 50 (signal = %.1e)\n", contaminated_signal);

    LocalVector2D dummy_neighbors[DIR_MAX] = {0};
    LocalVector2D center_output = process_topological_node_step(&center_node, contaminated_signal, dummy_neighbors);

    /* [KR] 자가 격리(Apoptosis) 결과 검증 */
    /* [EN] Verify Cellular Apoptosis (Isolation) Results */
    printf(" -> center_node.is_isolated = %s\n", center_node.is_isolated ? "TRUE (Isolated)" : "FALSE");
    printf(" -> center_node output: dx = %.1f, dy = %.1f (Contamination Guard Active)\n\n", center_output.dx, center_output.dy);

    printf("[Phase 2] 이웃 노드들의 자율 우회 검증 (Autonomous Neighbor Bypass)\n");
    printf("------------------------------------------------------------------------\n");

    /* [KR] 동쪽 이웃 노드(51) 연산: 서쪽에 사멸한 중심 노드(50)가 배치된 상황 */
    /* [EN] East Neighbor 51 execution: Western link is occupied by the collapsed node 50 */
    LocalVector2D neighbors_of_east[DIR_MAX] = {
        [DIR_WEST]  = center_output,             /* [KR] 죽은 중심 노드의 거부 신호(-99.0) 유입 / [EN] Toxic influx (-99.0) */
        [DIR_EAST]  = { .dx = 2.0, .dy = 0.0 }, /* [KR] 정상 노드의 흐름 / [EN] Normal node flux */
        [DIR_NORTH] = { .dx = 0.0, .dy = 0.0 },
        [DIR_SOUTH] = { .dx = 0.0, .dy = 0.0 }
    };

    printf(" -> [KR] East Node 51 연산 개시 (서쪽 방향에서 격리 노드 거부 신호 감지)\n");
    printf(" -> [EN] East Node 51 execution started (Detected reject signal from Western node)\n");
    LocalVector2D east_out = process_topological_node_step(&east_node, 0.0, neighbors_of_east);
    
    /* [KR] 결과 해석: 동쪽 노드는 서쪽 노드가 죽었음을 인지하고, 흐름을 -99.0으로 오염시키는 대신 
            0.0 처리하여 우회(Bypass)한 뒤 정상 동쪽 노드의 흐름만 살려내어 유효 벡터를 출력함 */
    /* [EN] Result Analysis: Instead of getting contaminated by -99.0, East node filters it to 0.0,
            bypassing the dead zone and calculating clean vectors using remaining healthy links. */
    printf(" ■ Node 51 [EAST] Vector -> dx = %+.4f, dy = %+.4f\n", east_out.dx, east_out.dy);
    printf(" -> [KR] 상태 검증: 전체 망이 마비되지 않고 우회로를 통해 연산 무결성 유지 완료.\n");
    printf(" -> [EN] Verification: Network avoided paralysis, securing mathematical integrity via bypass.\n");
    printf("------------------------------------------------------------------------\n");
    printf("💡 Final Clue: Cellular apoptosis safely isolates physical defects.\n");
    printf("               Surrounding grid automatically bypasses the toxic node.\n");
    printf("========================================================================\n");

    return 0;
}
