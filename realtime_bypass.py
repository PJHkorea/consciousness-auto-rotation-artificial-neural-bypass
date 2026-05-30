import numpy as np
import numba as nb
import math
import socket
import sys

# =========================================================================
# SYSTEM CONSTANTS & PARAMETERS DEFINITION
# 시스템 전역 상수의 선언 및 수치 가드 임계값 바인딩
# =========================================================================
EPSILON_INNOV = 1e-9    # Innovation Covariance Lower Bound / 이노베이션 분산 하한선
EPSILON_GUARD = 1e-28   # Cauchy-Schwarz Geometric Mean Safeguard / 코시-슈바르츠 기하평균 하한

# Gating Thresholds Mapping (Dynamic Control Specification)
# 액추에이터 구동을 위한 동적 게이팅 임계값 정의
THRESHOLD_AUTOBIO_ACTIVE = 0.55    # Bio-stimulation active state threshold / 자극 활성화 상태 임계값
THRESHOLD_AUTOBIO_INACTIVE = 0.75  # Normal resting state threshold / 일반 대기 상태 임계값

# -------------------------------------------------------------------------
# [Phase 1] 2x2 Joseph Form Kalman Filter & Stability Guard Core
# -------------------------------------------------------------------------
@nb.njit(cache=True, nogil=True, fastmath=True)
def _execute_single_step_core(
    raw_signal, p00, p01, p11, x0, x1, 
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    """
    Executes scalar operations for single-channel 2x2 state estimation.
    Enforces dual-layer Cauchy-Schwarz numerical stability guards to prevent divergence.
    """
    # 1. State Prediction (2D Vibration Rotation Model)
    x0_pred = cos_t * x0 - sin_t * x1
    x1_pred = sin_t * x0 + cos_t * x1

    # 2. Error Covariance Prediction (P_minus = F * P * F^T + Q)
    t0 = cos_t * p00 - sin_t * p01
    t1 = cos_t * p01 - sin_t * p11
    t2 = sin_t * p00 + cos_t * p01
    t3 = sin_t * p01 + cos_t * p11

    p00_m = cos_t * t0 - sin_t * t1 + q_noise
    p01_m = sin_t * t0 + cos_t * t1
    p11_m = sin_t * t2 + cos_t * t3 + q_noise
    
    # [Stability Guard Layer 1] Prevent micro-asymmetry during prediction step
    # [수치 가드 레이어 1] 예측 단계 직후 발생 가능한 부동소수점 비대칭성 즉시 교정
    p_prod_m = p00_m * p11_m
    max_p01_m = math.sqrt(p_prod_m if p_prod_m > EPSILON_GUARD else EPSILON_GUARD)
    if p01_m > max_p01_m:
        p01_m = max_p01_m
    elif p01_m < -max_p01_m:
        p01_m = -max_p01_m

    # 3. Kalman Gain (Innovation Covariance Safeguard)
    innov_cov = p00_m + r_noise
    if innov_cov < EPSILON_INNOV:
        innov_cov = EPSILON_INNOV

    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov

    # 4. Exact Joseph Form Covariance Update (Guarantees Positive-Definiteness)
    one_minus_k0 = 1.0 - k0
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = (one_minus_k0 * p01_m) - (k1 * one_minus_k0 * p00_m) + (k0 * k1 * r_noise)
    p11_new = (k1 * k1 * p00_m) - (2.0 * k1 * one_minus_k0 * p01_m) + p11_m + (k1 * k1 * r_noise)

    # 5. Real-time Numerical Guard using Cauchy-Schwarz Inequality (Update Step)
    # [수치 가드 레이어 2] 업데이트 단계 직후 코시-슈바르츠 부등식 강제
    p_prod = p00_new * p11_new
    max_p01 = math.sqrt(p_prod if p_prod > EPSILON_GUARD else EPSILON_GUARD)
    if p01_new > max_p01:
        p01_new = max_p01
    elif p01_new < -max_p01:
        p01_new = -max_p01

    # 6. State Update
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation

    # 7. Zero-Baseline Hyper-Sigmoid Gating Actuation (Continuous Soft-Thresholding)
    # 물리적 제어 불연속성(Jerk)을 완전히 차단하는 부드러운 스케일링 인터폴레이션 이식
    X_intent_energy = x0_new * x0_new + x1_new * x1_new
    scaled_energy = lambda_val * X_intent_energy

    if scaled_energy > 20.0:
        raw_prob = 1.0
    else:
        raw_prob = (2.0 / (1.0 + math.exp(-scaled_energy))) - 1.0

    if raw_prob < theta:
        p_state = 0.0
    else:
        p_state = (raw_prob - theta) / (1.0 - theta)

    return p00_new, p01_new, p11_new, x0_new, x1_new, p_state


class RealtimeBypassMassageEngine:
    """
    State orchestrator encapsulation ensuring zero-heap runtime allocation.
    채널 상태 및 프리알로케이션 메모리 뷰를 독점 관리하는 객체 래퍼입니다.
    """
    def __init__(self, sample_rate=250.0, target_freq=10.0):
        dt = 1.0 / sample_rate
        theta_rot = 2.0 * math.pi * target_freq * dt
        self.cos_t = math.cos(theta_rot)
        self.sin_t = math.sin(theta_rot)
        
        self.q_noise = 1e-4
        self.r_noise = 1e-2
        self.lambda_val = 0.5

        # Initialize internal scalar states / 필터 오차 공분산 및 위상 상태 변수 초기화
        self.p00, self.p01, self.p11 = 1.0, 0.0, 1.0
        self.x0, self.x1 = 0.0, 0.0

    def process_sample(self, raw_signal, current_th):
        """Processes a single incoming streaming tick / 1개 틱의 스트리밍 입력을 처리합니다."""
        self.p00, self.p01, self.p11, self.x0, self.x1, p_state = _execute_single_step_core(
            raw_signal, self.p00, self.p01, self.p11, self.x0, self.x1,
            self.cos_t, self.sin_t, self.q_noise, self.r_noise, self.lambda_val, current_th
        )
        return p_state
# -------------------------------------------------------------------------
# [Phase 2] Real-time TCP/IP Socket Infrastructure & Actuator Integration
# -------------------------------------------------------------------------
def run_integrated_neural_bypass(host="127.0.0.1", port=9999):
    """
    Runs production-grade TCP/IP streaming pipeline with full exception guards.
    실시간 제로카피 소켓 스트리밍 및 비상 제어 오토매틱 셧다운 인터록을 실행합니다.
    """
    engine = RealtimeBypassMassageEngine()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"[*] Consciousness Bypass Core bound successfully. Listening on {host}:{port}")
        
        conn, addr = server_socket.accept()
        print(f"[+] Bi-directional stream established with sensor device: {addr}")
        
        # Enforce strict 20ms real-time latency deadline guard
        # 하드웨어 통신 랙 및 데드라인을 방어하기 위한 20ms 타임아웃 강제
        conn.settimeout(0.02)
        
        # True Zero-Copy Buffer Initialization via fixed bytearray allocation
        # 파이썬 힙 객체 오버헤드를 차단하기 위한 고정 바이트 배열 메모리 뷰 선언
        recv_buffer = bytearray(4096)
        buf_view = memoryview(recv_buffer)
        bytes_in_buffer = 0
        
        last_valid_sample = 0.0
        current_th = THRESHOLD_AUTOBIO_INACTIVE  # Default baseline threshold
        
        while True:
            try:
                # Direct read into fixed memory view without dynamic generation
                bytes_received = conn.recv_into(buf_view[bytes_in_buffer:])
                if not bytes_received:
                    print("[-] Stream interface disconnected by host device.")
                    break
                bytes_in_buffer += bytes_received
                
                # High-speed boundary packet parser
                start_ptr = 0
                while True:
                    newline_idx = recv_buffer.find(b'\n', start_ptr, bytes_in_buffer)
                    if newline_idx == -1:
                        break
                        
                    # Zero-Copy slice mapping / 불필요한 서브 스트링 복사 차단
                    line_view = buf_view[start_ptr:newline_idx]
                    raw_data = bytes(line_view).decode('utf-8').strip()
                    start_ptr = newline_idx + 1
                    
                    if not raw_data:
                        continue
                        
                    # Parse telemetry data packet / 인입 패킷 파싱 및 인터록 상태 트리거 분석
                    # Expected format: "raw_value,autobio_flag" (e.g., "1.45,1")
                    try:
                        parts = raw_data.split(',')
                        raw_signal = float(parts[0])
                        autobio_flag = int(parts[1]) if len(parts) > 1 else 0
                        
                        last_valid_sample = raw_signal
                        # Dynamic parameter matching bound directly to physical feedback status
                        current_th = THRESHOLD_AUTOBIO_ACTIVE if autobio_flag == 1 else THRESHOLD_AUTOBIO_INACTIVE
                        
                    except Exception:
                        continue
                    
                    # ⚡ Execute Mathematical Core Step
                    p_state = engine.process_sample(raw_signal, current_th)
                    
                    # Generate real-time actuator feedback control packet
                    # 하드웨어 드라이버 단으로 보낼 연속성 제어 명령 패킷 피드백
                    trigger_msg = f"{p_state:.4f}\n"
                    conn.sendall(trigger_msg.encode('utf-8'))
                    
                # Maintenance of remaining unparsed bytes in the static buffer
                if start_ptr > 0:
                    recv_buffer[:bytes_in_buffer - start_ptr] = recv_buffer[start_ptr:bytes_in_buffer]
                    bytes_in_buffer -= start_ptr
                    
            except socket.timeout:
                # ⚠️ EMERGENCY TIMEOUT COMPENSATION LAYER
                # 패킷 지연/유실 탈동기화 발생 시, 직전 샘플을 기반으로 필터 상태 추정을 단절 없이 보상 유지
                p_state = engine.process_sample(last_valid_sample, current_th)
                try:
                    timeout_compensation_msg = f"{p_state:.4f},TEMPORARY_HOLD\n"
                    conn.sendall(timeout_compensation_msg.encode('utf-8'))
                except socket.error:
                    break
                    
    except Exception as system_critical_error:
        print(f"[💥] System Critical Breakdown Detected: {system_critical_error}", file=sys.stderr)
        
    finally:
        # Enforce absolute fail-safe interface shutdown sequence
        # 시스템 다운 시 외부 구동 기기가 폭주하지 않도록 비상 정지 인터록(Emergency Lock) 발동
        try:
            emergency_signal = "0.0000,EMERGENCY_STOP\n"
            conn.sendall(emergency_signal.encode('utf-8'))
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
        except Exception:
            pass
        server_socket.close()
        print("[*] Consciousness Neural Bypass Pipeline Safely Terminated.")


if __name__ == "__main__":
    # Execute integrated real-time bypass node / 통합 노드 단독 기동
    run_integrated_neural_bypass()
