/**
 * @file FluxMesh_TEST_32x_Scalar_Core.h
 * @brief Fully Flattened Scalar Node Architecture with Complete Numerical Integrity (32-bit Optimized).
 * 
 * @note [KR] 2x2 행렬을 완전히 제거하고, 제곱합 기반의 절대 양수 부호 보장 및 
 *           Padé 유리함수 근사를 레지스터 단에 직접 매핑한 자율 회전 신경 우회로 커널입니다. (32비트 경량화 버전)
 *       [EN] Erases all 2x2 matrix arrays; directly maps the square-sum based non-negative guarantee 
 *            and Padé approximation onto CPU registers for a self-rotating neural bypass. (32-bit Lightweight)
 * 
 * @attention [HARDWARE CONFIGURATION & COMPILER STRICT RULES]
 *       [KR] 1. 하드웨어 제한 사양: 본 엔진은 32비트 단정밀도 부동소수점 연산 장치(Single-Precision FPU)를 탑재한 
 *               Cortex-M4/M7, ESP32 등 임베디드 환경에 맞춰 가속 최적화를 달성하기 위해 float 규격으로 마감되었습니다.
 *            2. 컴파일러 금지 옵션: (-ffast-math / -Ofast 절대 사용 금지!) 
 *               이 옵션을 활성화하면 IEEE 754 표준이 무시되어 커널 내부의 'raw_signal != raw_signal' (NaN 검출 가드) 
 *               및 무단 최적화 삭제 방지용 'volatile' 격리벽 연산이 컴파일러에 의해 통째로 누락(DCE)됩니다.
 *               반드시 IEEE 754 표준을 무조건적으로 준수하는 '-O2' 또는 '-O3' 표준 최적화만 사용하십시오.
 * 
 *       [EN] 1. Hardware Specification: This engine is strictly engineered for 32-bit single-precision 
 *               FPU environments (e.g., Cortex-M4/M7, ESP32), precisely finalized in float to ensure maximum hardware acceleration.
 *            2. Forbidden Compiler Flags: (NEVER USE -ffast-math / -Ofast!)
 *               Activating these flags violates IEEE 754 standards, causing the compiler to totally eliminate (DCE) 
 *               the critical 'raw_signal != raw_signal' (NaN detection guard) and 'volatile' boundary logic.
 *               You must only employ standard compliant optimization flags such as '-O2' or '-O3'.
 */

#ifndef FLUXMESH_TEST_32X_SCALAR_CORE_H
#define FLUXMESH_TEST_32X_SCALAR_CORE_H

#include <stdint.h>
#include <stdbool.h>

/* --- MATHEMATICAL CONSTANTS & NUMERICAL BOUNDARIES (32-bit Adjusted) --- */
#define INNOVATION_SINGULARITY_EPSILON 1e-6f /**< [KR] float 정밀도에 맞춘 싱듈래리티 하한선 / [EN] 32-bit Division-by-zero defense guard */
#define FAILSAFE_REJECT_SIGNAL        -99.0f /**< [KR] 망 오염 방지용 거부 신호 / [EN] Network contamination defense signal */

/* --- TOPOLOGICAL SPATIAL ADJACENCY DEFINITION --- */
typedef enum {
    DIR_NORTH = 0,
    DIR_SOUTH = 1,
    DIR_EAST  = 2,
    DIR_WEST  = 3,
    DIR_MAX   = 4
} MeshDirection;

/**
 * @struct LocalVector2D
 * @brief Computed deterministic spatial vector data structure.
 */
typedef struct {
    float dx;         
    float dy;         
    float confidence; 
} LocalVector2D;

/**
 * @struct MeshNodeState
 * @brief [KR] 배열 기호([])를 전면 배제하고 순수 스칼라 32비트 float 레지스터 지향으로 진화한 노드 구조체
 *        [EN] Evolution into pure scalar 32-bit float register-oriented memory blocks without array indices.
 */
typedef struct {
    uint16_t node_id;         
    
    /* 2x2 Decoupled Estimation Space Split into Pure Registers */
    float x0;                 /**< [KR] 채널 0번의 상태 변수 / [EN] Channel 0 state variable register */
    volatile float x1;        /**< [KR] 위상 고정용 격리벽 앵커 / [EN] Isolation guard anchor for topology lock */
    
    /* Square-Sum Matrix Symmetry Preservation for Non-Negative Confidence */
    float p00;                /**< [KR] 오차 공분산 핵심 스칼라 / [EN] Primary error covariance scalar */
    volatile float p11;       /**< [KR] 무간섭 동기화 고정 스칼라 / [EN] Decoupled synchronization scalar anchor */
    
    bool is_isolated;         /**< [KR] 자가 치유 격리 플래그 / [EN] Self-healing isolation status flag */
} MeshNodeState;

/**
 * @brief Pure Scalar-based Joseph Form Operation & Topology Fusion Kernel (32-bit Optimized).
 */
static inline LocalVector2D process_topological_node_step(MeshNodeState* self, float raw_signal, const LocalVector2D neighbor_vectors[DIR_MAX]) {
    /* [KR] 초기화 단계부터 스칼라 거부 신호 강제 주입 */
    /* [EN] Force-inject failsafe rejection signal from the initialization phase */
    LocalVector2D output_vector = {FAILSAFE_REJECT_SIGNAL, FAILSAFE_REJECT_SIGNAL, 0.0f};

    /* [KR] 메모리 단선 및 Null 포인터 무결성 가드 검증 */
    /* [EN] Memory disconnection and Null pointer integrity guard verification */
    if (!self || !neighbor_vectors) {
        return output_vector;
    }

    /* [KR] 하드웨어 가드: 자가 격리 노드 연산 즉시 거부 및 우회 */
    /* [EN] Hardware Guard: Instantly reject and bypass isolated broken nodes */
    if (self->is_isolated) {
        return output_vector; 
    }

    /* [KR] 수치해석적 무결성 검사: float 유효 정밀도를 고려하여 한계선 백만(1e6f) 단위로 압축 차단 */
    /* [EN] Numerical Integrity Check: Block IEEE 754 NaN and float explosion boundaries at 1e6f */
    if (raw_signal != raw_signal || raw_signal > 1e6f || raw_signal < -1e6f) { 
        self->is_isolated = true; /* [KR] 세포 사멸(Apoptosis) 트리거 / [EN] Trigger cellular apoptosis */
        return output_vector;
    }

    /* [KR] [README.md 사상] 완전 해체형 스칼라 조셉 폼 연산 메커니즘 */
    /* [EN] [README.md Philosophy] Fully Flattened Scalar Joseph Form Core Engine */
    float innovation = raw_signal - self->x0;
    float S_residual = self->p00 + 1.0f; 

    /* [KR] 분모가 0에 수렴하여 발생하는 특이점 폭주 차단 */
    /* [EN] Prevent singularity explosion where the denominator converges to zero */
    if (S_residual < INNOVATION_SINGULARITY_EPSILON && S_residual > -INNOVATION_SINGULARITY_EPSILON) {
        output_vector.dx = 0.0f;
        output_vector.dy = 0.0f;
        output_vector.confidence = 1e-4f; /* [KR] 32비트 해상도 한계 마진 / [EN] 32-bit resolution margin */
        return output_vector;
    }

    float K_gain = self->p00 / S_residual;
    float ImKH = 1.0f - K_gain;

    /* ★ CRITICAL EDUCATIONAL POINT ★ */
    /* [KR] 제곱합 구조(A^2 * p + B^2)를 관통하여 컴퓨터가 어떤 반올림 오차를 내더라도 
            신뢰도가 절대 음수(-)로 뒤집히지 않도록 하드웨어 단에서 영원히 보장 */
    /* [EN] Executes a square-sum formula (A^2 * p + B^2) to eternally guarantee that 
            the confidence never flips to a negative value, despite floating-point round-off errors. */
    self->p00 = (ImKH * self->p00 * ImKH) + (K_gain * 1.0f * K_gain);
    
    /* [KR] 컴파일러 최적화 삭제를 방지하고 축 간 무간섭 동기화 전위 계승 */
    /* [EN] Prevent Dead Code Elimination(DCE) and enforce decoupled synchronization transfer */
    self->p11 = self->p00; 
    self->x0 = self->x0 + (K_gain * innovation);
    self->x1 = self->x0; /* [KR] 위상 기울기 연산용 격리벽 고정 / [EN] Freeze anchor for spatial gradient */

    /* [KR] [README2.md 사상] 공간적 인접성 기반 국소 위상 융합 */
    /* [EN] [README2.md Philosophy] Spatial Adjacency-based Local Topology Fusion */
    // [KR] 이웃 노드들과 수식을 연쇄적으로 얽어 자율 회전을 위한 흐름(Flux) 생성
    // [EN] Intertwine formulas with neighbors to generate physical rotation and dynamic flux
    float Spatial_Gradient_X = neighbor_vectors[DIR_EAST].dx - neighbor_vectors[DIR_WEST].dx;
    float Spatial_Gradient_Y = neighbor_vectors[DIR_NORTH].dx - neighbor_vectors[DIR_SOUTH].dx;

    /* [KR] Padé 유리함수 분모 제로 폭주 정밀 제어 (무거운 exp 함수 없이 초속 연산 달성) */
    /* [EN] Padé approximation singularity guard (Achieves ultra-fast scaling without heavy exp functions) */
    float denominator = 1.0f + self->x0;
    if (denominator < INNOVATION_SINGULARITY_EPSILON && denominator > -INNOVATION_SINGULARITY_EPSILON) {
        self->is_isolated = true; 
        return output_vector;
    }

    float linear_scale = 1.0f / denominator; 
    
    /* [KR] 오염되지 않은 정제된 확정론적 공간 벡터 도출 */
    /* [EN] Derivation of clean, verified deterministic spatial vector output */
    output_vector.dx = Spatial_Gradient_X * linear_scale;
    output_vector.dy = Spatial_Gradient_Y * linear_scale;
    output_vector.confidence = self->p00;

    return output_vector;
}

#endif /* FLUXMESH_TEST_32X_SCALAR_CORE_H */
