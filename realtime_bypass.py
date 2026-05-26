"""
Project: ZeroAxiom-Bypass (Real-Time Production Hub)
File: realtime_bypass_core.py
Description:
    Micro-Register Optimized Real-Time Single-Sample Engine (ARCF Core).
    Maintains strict mathematical integrity via Exact Scalar Joseph Form.
License: MIT
"""

import numpy as np
import math
import orjson
from numba import njit

# ==============================================================================
# Global Configuration Constants / 전역 설정 상수 (통합 관리)
# ==============================================================================
EPSILON_INNOV = 1e-9      # Innovation covariance lower bound / 이노베이션 공분산 하한
EPSILON_GUARD = 1e-14      # State covariance minimum guard / 상태 공분산 최하한 가드
EPSILON_PROD = 1e-28       # Cauchy-Schwarz product limit / 코시-슈바르츠 곱 제한

GATE_SCALE = -2.5          # Energy gating sensitivity / 에너지 게이팅 민감도 계수
GATE_OFFSET = 0.8          # Energy gating threshold center / 에너지 게이팅 중심 오프셋
LAMBDA_STATE = 7.0         # Sigmoid state transition slope / 시그모이드 상태 전이 기울기

# Sensitivity Thresholds for SMR Tracking / SMR 추적용 동적 임계값 기준
THRESHOLD_AUTOBIO_ACTIVE = 0.55    # Threshold under stimulation / 자극 활성화 시 임계값
THRESHOLD_AUTOBIO_INACTIVE = 0.75  # Default threshold / 일반 상태 임계값

# ==============================================================================
# JIT-Compiled Real-Time Signal Processing Kernel / 가속 연산 커널
# ==============================================================================
@njit(cache=True, nogil=True, fastmath=False)
def _execute_single_step_core(x_in, b, a, cos_t, sin_t, q, R, x, P, v, running_energy, ema_alpha):
    # [Register Optimization]: Local scalar unpacking to eliminate array reference overheads
    # [레지스터 최적화]: 배열 참조 오버헤드 제거를 위한 국소 스칼라 변수 매핑
    b0, b1, b2 = b[0], b[1], b[2]
    a1, a2 = a[1], a[2]
    x0, x1 = x[0], x[1]
    p00, p01, p11 = P[0], P[1], P[2]
    v0, v1 = v[0], v[1]

    # 3.1. Inline IIR Notch Filtering / 인라인 IIR 노치 필터링
    y_notch = b0 * x_in + v0
    v0 = b1 * x_in - a1 * y_notch + v1
    v1 = b2 * x_in - a2 * y_notch

    # 3.2. Real-time Information Gating / 실시간 정보 게이팅 (에너지 추정)
    inst_energy = y_notch * y_notch
    curr_energy = (1.0 - ema_alpha) * running_energy + ema_alpha * inst_energy
    gate_base = 1.0 / (1.0 + math.exp(GATE_SCALE * (curr_energy - GATE_OFFSET)))
    w_gate = 0.1 + gate_base * 0.9
    
    if w_gate < 0.1:
        w_gate = 0.1
    elif w_gate > 1.0:
        w_gate = 1.0
    y_filt = y_notch * w_gate

    # 3.3. Analytical State Vector Prediction / 해석적 상태 벡터 예측단계
    x0_m = cos_t * x0 + sin_t * x1
    x1_m = -sin_t * x0 + cos_t * x1
    
    cos_sq = cos_t * cos_t
    sin_sq = sin_t * sin_t
    two_cos_sin = 2.0 * cos_t * sin_t
    cos_sq_minus_sin_sq = cos_sq - sin_sq
    cos_sin = cos_t * sin_t
    
    p00_m = cos_sq * p00 + two_cos_sin * p01 + sin_sq * p11 + q
    p01_m = -cos_sin * p00 + cos_sq_minus_sin_sq * p01 + cos_sin * p11
    p11_m = sin_sq * p00 - two_cos_sin * p01 + cos_sq * p11 + q

    # 3.4. Exact Scalar Joseph Form Expansion / 조셉 폼 공분산 업데이트 (수치 안정성 확보)
    innov_cov = p00_m + R
    if innov_cov > EPSILON_INNOV:
        inv_innov = 1.0 / innov_cov
        k0 = p00_m * inv_innov
        k1 = p01_m * inv_innov
        innov_v = y_filt - x0_m
        
        x0_new = x0_m + k0 * innov_v
        x1_new = x1_m + k1 * innov_v
        
        one_minus_k0 = 1.0 - k0
        k0_R = k0 * R
        k1_R = k1 * R
        
        p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0_R)
        p01_new = (one_minus_k0 * p01_m) - (k1 * p00_m) + (k0 * k1_R)
        p11_new = (k1 * k1 * p00_m) - (2.0 * k1 * p01_m) + p11_m + (k1 * k1_R)
    else:
        x0_new, x1_new = x0_m, x1_m
        p00_new, p01_new, p11_new = p00_m, p01_m, p11_m

    # 3.5. Cauchy-Schwarz Stability Guards / 코시-슈바르츠 한계값 안정성 가드
    p00_guard = p00_new if p00_new > EPSILON_GUARD else EPSILON_GUARD
    p11_guard = p11_new if p11_new > EPSILON_GUARD else EPSILON_GUARD
    p_prod = p00_guard * p11_guard
    
    max_p01 = math.sqrt(p_prod if p_prod > EPSILON_PROD else EPSILON_PROD)
    if p01_new > max_p01:
        p01_guard = max_p01
    elif p01_new < -max_p01:
        p01_guard = -max_p01
    else:
        p01_guard = p01_new

    # Write-back to reference structures for state persistence / 원래 배열 구조에 포인터 쓰기
    x[0], x[1] = x0_new, x1_new
    P[0], P[1], P[2] = p00_guard, p01_guard, p11_guard
    v[0], v[1] = v0, v1
    
    energy_out = x0_new * x0_new + x1_new * x1_new
    return y_filt, energy_out, curr_energy


class ARCFSystem:
    def __init__(self, b_notch, a_notch, cos_t, sin_t, q=0.08, R=1.20):
        self.b = b_notch
        self.a = a_notch
        self.cos_t = cos_t
        self.sin_t = sin_t
        self.q = q
        self.R = R
        self.x = np.zeros(2, dtype=np.float64)
        self.P_mat = np.array([2.0, 0.0, 2.0], dtype=np.float64)
        self.v = np.zeros(2, dtype=np.float64)
        self.running_energy = 0.0

    def process_sample(self, raw_sample, ema_alpha=0.08, current_th=0.5):
        y_filt, energy_out, next_energy = _execute_single_step_core(
            raw_sample, self.b, self.a, self.cos_t, self.sin_t, self.q, self.R,
            self.x, self.P_mat, self.v, self.running_energy, ema_alpha
        )
        self.running_energy = next_energy
        p_state = 1.0 / (1.0 + math.exp(-LAMBDA_STATE * (energy_out - current_th)))
        return p_state
"""
Project: ZeroAxiom-Bypass (Real-Time Production Hub)
File: realtime_bypass_network.py
Description:
    True Zero-Copy Real-Time Network Infrastructure with Latency Accumulation Defenses.
License: MIT
"""

import socket
import orjson
import time
import numpy as np

# Bind core mathematical constants from front-end module / 전반부 핵심 상수 바인딩
from realtime_bypass_core import (
    ARCFSystem, 
    THRESHOLD_AUTOBIO_ACTIVE, 
    THRESHOLD_AUTOBIO_INACTIVE
)

# ==============================================================================
# Infrastructure Configuration Constants / 시스템 스트리밍 환경 변수
# ==============================================================================
COMMAND_INTERVAL = 0.1       # Actuator dead-time guard / 액추에이터 제어 명령 최소 주기
MAX_ALLOWED_TIMEOUTS = 5     # Maximum sequential timeout limits / 허용 가능한 최대 타임아웃 연속 횟수
MAX_BUF_SIZE = 65536         # Ring buffer bite allocation limit / 데이터 스트림 수집용 버퍼 크기

def run_integrated_neural_bypass():
    b_notch = np.array([0.97517, -1.85485, 0.97517], dtype=np.float64)
    a_notch = np.array([1.00000, -1.85485, 0.95035], dtype=np.float64)
    cos_t, sin_t = 0.96884, 0.24765
    
    EEG_HOST, EEG_PORT = "127.0.0.1", 9999
    ROBOT_HOST, ROBOT_PORT = "192.168.1.50", 8888
    
    print("🤖 [ZeroAxiom-Bypass] Initializing zero-latency streaming infrastructure / 스트리밍 인프라 가동 중...")
    engine = ARCFSystem(b_notch, a_notch, cos_t, sin_t)
    
    last_command_time = 0.0
    last_valid_sample = 0.0
    timeout_counter = 0
    current_th = THRESHOLD_AUTOBIO_INACTIVE  # State variable for timeout estimation / 타임아웃 보상 추적 변수
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as eeg_sock, \
         socket.socket(socket.AF_INET, socket.SOCK_STREAM) as robot_sock:
        try:
            eeg_sock.connect((EEG_HOST, EEG_PORT))
            robot_sock.connect((ROBOT_HOST, ROBOT_PORT))
            
            eeg_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            eeg_sock.settimeout(0.02)  # 20ms Deadline Guard / 타임아웃 한계 시간 설정
            robot_sock.settimeout(0.05)
            print("✅ [Infrastructure Active] Closed-loop neural bypass pipeline online / 폐루프 신경 바이패스 온라인.")
            
            raw_buffer = bytearray(MAX_BUF_SIZE)
            buf_view = memoryview(raw_buffer)
            bytes_in_buf = 0
            
            while True:
                # --- Step A: Non-blocking Oriented Packet Ingestion / 패킷 수신 레이어 ---
                try:
                    packet_len = eeg_sock.recv_into(buf_view[bytes_in_buf:], MAX_BUF_SIZE - bytes_in_buf)
                    if packet_len == 0: 
                        break  # Graceful connection shutdown from server / 원격 호스트 정상 종료
                    bytes_in_buf += packet_len
                    timeout_counter = 0
                except socket.timeout:
                    timeout_counter += 1
                    if timeout_counter >= MAX_ALLOWED_TIMEOUTS:
                        print("⚠ [CRITICAL] Signal loss threshold exceeded! Emitting TEMPORARY_HOLD packet / 신호 손실, 보류 패킷 전송.")
                        try: 
                            robot_sock.sendall(orjson.dumps({"action": "TEMPORARY_HOLD"}) + b"\n")
                        except socket.error: 
                            pass
                        timeout_counter = 0
                    
                    if bytes_in_buf == 0:
                        # Timeout Window Intercept: Clock the prediction engine with last valid sample
                        # 타임아웃 인터셉트: 스트림 파싱을 생략하고 최종 샘플로 필터 상태 추정만 지속
                        _ = engine.process_sample(last_valid_sample, current_th=current_th)
                        continue
                
                # --- Step B: High-Speed Stream Parsing (Zero-Copy Frame Extraction) / 제로카피 프레임 파싱 ---
                start_ptr = 0
                while True:
                    newline_idx = raw_buffer.find(b"\n", start_ptr, bytes_in_buf)
                    if newline_idx == -1:
                        break
                    
                    # True Zero-Copy slicing via memoryview / 메모리뷰 참조 슬라이싱으로 힙 할당 방지
                    line_view = buf_view[start_ptr:newline_idx]
                    start_ptr = newline_idx + 1
                    
                    if len(line_view) == 0 or line_view.isspace(): 
                        continue
                        
                    data = orjson.loads(line_view)
                    raw_sample = data["eeg_microvolts"]
                    last_valid_sample = raw_sample
                    
                    # Dynamic sensitivity adjustment / 자가 신호 플래그에 따른 임계값 동적 변환
                    s_autobio_active = data.get("S_autobio_active", False)
                    current_th = THRESHOLD_AUTOBIO_ACTIVE if s_autobio_active else THRESHOLD_AUTOBIO_INACTIVE
                    
                    p_state = engine.process_sample(raw_sample, current_th=current_th)
                    current_time = time.monotonic()
                    
                    if p_state > current_th and (current_time - last_command_time > COMMAND_INTERVAL):
                        command = {"action": "TRIGGER_EXOSKELETON_ON", "p_state": p_state}
                        try:
                            robot_sock.sendall(orjson.dumps(command) + b"\n")
                            last_command_time = current_time
                            print(f"⚡ P_state: {p_state:.3f} (Th: {current_th}) ➔ Actuator command transmitted / 제어 명령 전송 완료.")
                        except socket.error:
                            print("⚠ [WARNING] Robotic controller transmission error / 로봇 연결 유실 경고.")
                
                # --- Step C: Buffer Compaction & Overflow Defense / 슬라이딩 윈도우 버퍼 제어 ---
                if start_ptr > 0:
                    rem_len = bytes_in_buf - start_ptr
                    if rem_len > 0:
                        raw_buffer[:rem_len] = raw_buffer[start_ptr:bytes_in_buf]
                    bytes_in_buf = rem_len
                else:
                    bytes_in_buf = 0  # Zero latency residue achieved / 잔여 패킷 없음 보장
                
                if bytes_in_buf >= MAX_BUF_SIZE:
                    print("⚠ [CRITICAL] Buffer overflow condition detected! Flushing buffer / 버퍼 오버플로우 감지 및 초기화.")
                    bytes_in_buf = 0
                    
        except Exception as e:
            print(f"❌ [CRASH] Hardware communication loop fractured / 하드웨어 루프 예외 발생: {e}")
            print("🚨 Triggering EMERGENCY_STOP interlock and destroying network ports / 비상 정지 및 포트 자원 강제 해제...")
            try: 
                robot_sock.sendall(orjson.dumps({"action": "EMERGENCY_STOP"}) + b"\n")
                robot_sock.shutdown(socket.SHUT_RDWR)
                eeg_sock.shutdown(socket.SHUT_RDWR)
            except socket.error: 
                pass


if __name__ == "__main__":
    run_integrated_neural_bypass()
