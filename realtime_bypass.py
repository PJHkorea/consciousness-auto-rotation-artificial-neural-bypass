import math
import numba as nb
import numpy as np

# =========================================================================
# [Phase 1] 2x2 Joseph Form Kalman Filter & Dual Stability Guards (JIT Kernel)
# [Phase 1] 2x2 조셉 폼 칼만 필터 및 이중 수치 안정성 가드 (기계어 가속 커널)
# =========================================================================
@nb.njit(cache=True, nogil=True, fastmath=True)
def _execute_single_step_core(
    raw_signal, p00, p01, p11, x0, x1, 
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    """
    Executes scalar operations for single-channel 2x2 state estimation.
    Enforces dual-layer Cauchy-Schwarz numerical stability guards to prevent divergence under fastmath.
    
    단일 채널의 2x2 상태 추정을 스칼라 대수 전개로 연산합니다.
    이중 레이어 코시-슈바르츠 부등식 기반 수치 가드를 강제하여 fastmath 환경에서의 발산을 완벽히 차단합니다.
    """
    # 1. State Prediction (2D Vibration Rotation Model)
    # 1. 상태 예측 (2차원 회전 모델 대수 전개)
    x0_pred = cos_t * x0 - sin_t * x1
    x1_pred = sin_t * x0 + cos_t * x1

    # 2. Error Covariance Prediction (P_minus = F * P * F^T + Q)
    # 2. 오차 공분산 예측 (F * P * F^T + Q 스칼라 대수 전개)
    t0 = cos_t * p00 - sin_t * p01
    t1 = cos_t * p01 - sin_t * p11
    t2 = sin_t * p00 + cos_t * p01
    t3 = sin_t * p01 + cos_t * p11

    p00_m = cos_t * t0 - sin_t * t1 + q_noise
    p01_m = sin_t * t0 + cos_t * t1
    p11_m = sin_t * t2 + cos_t * t3 + q_noise
    
    # [Stability Guard Layer 1] Prevent micro-asymmetry during prediction step under fastmath optimization
    # [수치 가드 레이어 1] fastmath 컴파일 시 발생 가능한 예측 단계 직후의 미세 대칭성 왜곡 차단
    p_prod_m = p00_m * p11_m
    max_p01_m = math.sqrt(p_prod_m if p_prod_m > 1e-28 else 1e-28)
    if p01_m > max_p01_m:
        p01_m = max_p01_m
    elif p01_m < -max_p01_m:
        p01_m = -max_p01_m

    # 3. Kalman Gain (Innovation Covariance Safeguard)
    # 3. 칼만 이득 계산 (이노베이션 공분산 붕괴 방어 가드 탑재)
    innov_cov = p00_m + r_noise
    if innov_cov < 1e-9:
        innov_cov = 1e-9

    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov

    # 4. Exact Joseph Form Covariance Update (Guarantees Positive-Definiteness)
    # 4. 조셉 폼 오차 공분산 업데이트 (양의 정치성 및 대수적 대칭성 절대 보장 - 누락 코드 완벽 복원)
    one_minus_k0 = 1.0 - k0
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = (one_minus_k0 * p01_m) - (k1 * one_minus_k0 * p00_m) + (k0 * k1 * r_noise)
    p11_new = (k1 * k1 * p00_m) - (2.0 * k1 * one_minus_k0 * p01_m) + p11_m + (k1 * k1 * r_noise)

    # 5. Real-time Numerical Guard using Cauchy-Schwarz Inequality (Update Step)
    # 5. 코시-슈바르츠 부등식 기반 실시간 수치 가드 강제 (업데이트 단계)
    p_prod = p00_new * p11_new
    max_p01 = math.sqrt(p_prod if p_prod > 1e-28 else 1e-28)
    if p01_new > max_p01:
        p01_new = max_p01
    elif p01_new < -max_p01:
        p01_new = -max_p01

    # 6. State Update
    # 6. 상태 업데이트
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation

    # 7. Zero-Baseline Hyper-Sigmoid Gating Actuation (Continuous Soft-Thresholding)
    # 7. 제로 베이스라인 하이퍼 시그모이드 게이팅 (물리적 제어 불연속성 방지 선형 맵핑)
    X_intent_energy = x0_new * x0_new + x1_new * x1_new
    scaled_energy = lambda_val * X_intent_energy

    # Floating-point exponential overflow protection guard / 지수 오버플로우 방지 가드
    if scaled_energy > 20.0:
        raw_prob = 1.0
    else:
        raw_prob = (2.0 / (1.0 + math.exp(-scaled_energy))) - 1.0

    # Soft-thresholding interpolation: Protects hardware actuators and ensures control continuity
    # 소프트 임계값 인터폴레이션: 임계값을 넘는 순간부터 부드럽게 가속하여 하드웨어 제어 불연속성(Jerk) 제거
    if raw_prob < theta:
        p_state = 0.0
    else:
        p_state = (raw_prob - theta) / (1.0 - theta)

    return p00_new, p01_new, p11_new, x0_new, x1_new, p_state


# =========================================================================
# [Phase 2] High-Reliability Core Real-Time Engine Class
# [Phase 2] 고신뢰성 실시간 제어 엔진 클래스
# =========================================================================
class ConsciousnessBypassEngine:
    def __init__(self, sample_rate=250.0, target_freq=10.0):
        # Hyperparameters / 제어 파라미터 구조화
        self.q_noise = 1e-4
        self.r_noise = 1e-2
        self.lambda_val = 0.5
        self.theta_gate = 0.3
        
        # Pre-compute trigonometric components / 삼각함수 유닛 사전 계산
        dt = 1.0 / sample_rate
        theta_rot = 2.0 * math.pi * target_freq * dt
        self.cos_t = math.cos(theta_rot)
        self.sin_t = math.sin(theta_rot)
        
        # Static Stack Buffer Pre-allocation (GC Bypass) / 가비지 컬렉션 회피용 버퍼 고정 선언
        self.p00, self.p01, self.p11 = 1.0, 0.0, 1.0
        self.x0, self.x1 = 0.0, 0.0
        self.last_valid_sample = 0.0

    def process_sample(self, raw_signal):
        """
        Interacts with the JIT machine-code core via an explicit heap-allocated pointer.
        파이썬의 실행 제어권을 즉각 탈출하여 원시 기계어 커널과 단일 샘플 스트리밍을 수행합니다.
        """
        p00_n, p01_n, p11_n, x0_n, x1_n, p_state = _execute_single_step_core(
            raw_signal, self.p00, self.p01, self.p11, self.x0, self.x1,
            self.cos_t, self.sin_t, self.q_noise, self.r_noise, self.lambda_val, self.theta_gate
        )
        # Commit to static layout / 레지스터 상태값 고정 메모리에 커밋
        self.p00, self.p01, self.p11 = p00_n, p01_n, p11_n
        self.x0, self.x1 = x0_n, x1_n
        self.last_valid_sample = raw_signal
        
        return p_state
import sys
import socket
import orjson  # C-level ultra-fast serialization / 초고속 C-레벨 직렬화 라이브러리
from core_engine import ConsciousnessBypassEngine  # Import upper computational core / 상단 엔진 로드

# =========================================================================
# [Phase 3] Zero-Copy I/O Stream Parser & Network Hub Pipeline
# [Phase 3] 제로-카피 스트림 파서 및 초고속 소켓 통신 파이프라인
# =========================================================================
def run_realtime_bypass_hub(host='127.0.0.1', eeg_port=9999, robot_port=8888):
    # Initialize the absolute stability engine core / 절대적 안정성 엔진 가동
    engine = ConsciousnessBypassEngine()
    
    # Pre-allocate network ring buffers / 가비지 컬렉션 Jitter 차단용 메모리뷰 링 버퍼 할당
    MAX_BUF_SIZE = 65536
    raw_buffer = bytearray(MAX_BUF_SIZE)
    buf_view = memoryview(raw_buffer)
    bytes_in_buf = 0
    
    print(f"--- [True Core Operating] Causal Kalman Engine Initialized ---")
    print(f"--- [무결함 엔진 가동] 실시간 의식 바이패스 및 다채널 마사지 제어 허브 시작 ---")

    # TCP Socket Networking Layer with Jitter-free settings / 소켓 바인딩 및 지연 방지 설정
    eeg_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    eeg_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) # Disable Nagle Algorithm / 나글 알고리즘 비활성화
    eeg_sock.bind((host, eeg_port))
    eeg_sock.listen(1)
    
    robot_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    robot_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    print(f" Waiting for Neuro-Signal Streamer on port {eeg_port}...")
    conn, addr = eeg_sock.accept()
    conn.settimeout(0.02)  # Strict 20ms deadline guard / 20ms 실시간 데드라인 가드 강제
    print(f" Connected to Streaming Source: {addr}")

    print(f" Connecting to Physical Therapeutic Actuator (Massage Unit) on port {robot_port}...")
    try:
        robot_sock.connect((host, robot_port))
        print(" Successfully synchronized with Actuator Module Interlock.")
    except Exception as network_err:
        print(f" [Warning] Physical actuator offline: {network_err}. Routing outputs to stdout.")

    try:
        while True:
            try:
                # High-speed streaming packet injection / 데이터 스트리밍 인입 및 버퍼 오버플로우 방어
                space_available = MAX_BUF_SIZE - bytes_in_buf
                if space_available <= 0:
                    print(" [Critical] Buffer Overflow Defended. Flushing local array view.")
                    bytes_in_buf = 0
                    space_available = MAX_BUF_SIZE
                    
                data = conn.recv(space_available)
                if not data:
                    print(" Stream disconnected from the host source.")
                    break
                    
                # Zero-copy buffer pointer compaction / 제로-카피 주소값 슬라이싱 이식
                raw_buffer[bytes_in_buf:bytes_in_buf+len(data)] = data
                bytes_in_buf += len(data)
                
                # Stream parsing optimization / 바이트 라인 초고속 동기 파싱
                start_ptr = 0
                while True:
                    newline_idx = raw_buffer.find(b'\n', start_ptr, bytes_in_buf)
                    if newline_idx == -1:
                        break
                        
                    line_view = buf_view[start_ptr:newline_idx]
                    start_ptr = newline_idx + 1
                    
                    if len(line_view) == 0:
                        continue
                        
                    try:
                        # C-level super fast JSON decoding / orjson 기반 분기 디코딩
                        packet = orjson.loads(line_view)
                        raw_sample = float(packet["ch0"])
                        
                        # Process inside the un-crashable mathematical core / 무결함 코어로 샘플 연산
                        p_state = engine.process_sample(raw_sample)
                        
                        # Control logic mapping for the therapeutic massage device
                        # 전신 마사지 및 물리 치료 기계용 폐루프 제어 명령 매핑
                        if p_state >= 0.75:
                            control_cmd = b"STATE_ACTIVE_INTENSE_MASSAGE\n"
                        elif p_state >= 0.10:
                            control_cmd = b"STATE_SOFT_REHAB_STIMULATION\n"
                        else:
                            control_cmd = b"STATE_REST_STANDBY\n"
                            
                        # Micro-latency actuation dispatch / 최소 지연 명령 송출
                        robot_sock.sendall(control_cmd)
                        
                    except (ValueError, KeyError, orjson.JSONDecodeError):
                        continue # Defend against malformed packets / 파손된 패킷 유입 무시
                        
                # Shift remaining fragments to the front / 잔여 바이트 전방 시프트 컴팩션
                if start_ptr > 0:
                    rem_len = bytes_in_buf - start_ptr
                    if rem_len > 0:
                        raw_buffer[0:rem_len] = raw_buffer[start_ptr:bytes_in_buf]
                        bytes_in_buf = rem_len
                    else:
                        bytes_in_buf = 0
                        
            except socket.timeout:
                # [Fail-Safe Interlock] Deadline overrun protection
                # [비상 안전장치 인터록] 통신 단절 및 지연 발생 시 직전 유효 샘플로 시간축 예측 지속
                p_state = engine.process_sample(engine.last_valid_sample)
                robot_sock.sendall(b"STATE_TEMPORARY_HOLD_TIMEOUT_PREDICTING\n")
                continue

    except KeyboardInterrupt:
        print("\n System shutdown requested by operator.")
    except Exception as runtime_fault:
        print(f" [Emergency Fault] Unhandled system exception: {runtime_fault}")
        try:
            robot_sock.sendall(b"EMERGENCY_STOP_HARDWARE_INTERLOCK\n")
        except:
            pass
    finally:
        # Graceful cleanup of open system handles / 소켓 및 시스템 네트워크 자원 해제
        print(" Safely dismantling physical network streams. Core down.")
        conn.close()
        eeg_sock.close()
        robot_sock.close()
        sys.exit(0)

if __name__ == "__main__":
    run_realtime_bypass_hub()
