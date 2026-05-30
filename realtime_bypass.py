import numpy as np
import numba as nb
import math

# -------------------------------------------------------------
# [환경 설정 및 상수]
# -------------------------------------------------------------
EPSILON_INNOV = 1e-9
EPSILON_GUARD = 1e-28

# -------------------------------------------------------------
# [고속 연산 코어 - Numba JIT 적용]
# -------------------------------------------------------------
@nb.njit(cache=True, nogil=True, fastmath=False)
def _execute_single_step_core(
    raw_signal, p00, p01, p11, x0, x1,
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    # [1] 상태 공간 시스템 동역학 예측 (Time Update - State)
    x0_pred = cos_t * x0 - sin_t * x1
    x1_pred = sin_t * x0 + cos_t * x1
    
    cos_sq = cos_t * cos_t
    sin_sq = sin_t * sin_t
    cos_sin = cos_t * sin_t
    
    # [2] 오차 공분산 예측 (Time Update - Covariance)
    # 논리 교정: 하한선 필터링 전, 순수 전파 수식으로 공분산 행렬 3개 원소를 동시 유도
    p00_m = (cos_sq * p00) - (2.0 * cos_sin * p01) + (sin_sq * p11) + q_noise
    p11_m = (sin_sq * p00) + (2.0 * cos_sin * p01) + (cos_sq * p11) + q_noise
    p01_m = (cos_sin * (p00 - p11)) + ((cos_sq - sin_sq) * p01)
    
    # 부동소수점 오차로 인한 음수 분산 방지 (하한선 제약)
    if p00_m < 1e-14: p00_m = 1e-14
    if p11_m < 1e-14: p11_m = 1e-14
    
    # 코시-슈바르츠 부등식 기반 상관계수 바운딩 방어 (|ρ| <= 1)
    p_prod_m = p00_m * p11_m
    max_p01_m = math.sqrt(p_prod_m if p_prod_m > EPSILON_GUARD else EPSILON_GUARD)
    if p01_m > max_p01_m:
        p01_m = max_p01_m
    elif p01_m < -max_p01_m:
        p01_m = -max_p01_m
        
    # [3] 측정 갱신을 위한 이노베이션 분산 및 칼만 이득 계산
    innov_cov = p00_m + r_noise
    if innov_cov < EPSILON_INNOV:
        innov_cov = EPSILON_INNOV
        
    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov
    
    # [4] Joseph Form 구조 기반 사후 오차 공분산 업데이트 (Measurement Update - Covariance)
    one_minus_k0 = 1.0 - k0
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = (one_minus_k0 * p01_m) - (k1 * one_minus_k0 * p00_m) + (k0 * k1 * r_noise)
    p11_new = p11_m - (2.0 * k1 * p01_m) + (k1 * k1 * p00_m) + (k1 * k1 * r_noise)
    
    if p00_new < 1e-14: p00_new = 1e-14
    if p11_new < 1e-14: p11_new = 1e-14
    
    p_prod = p00_new * p11_new
    max_p01 = math.sqrt(p_prod if p_prod > EPSILON_GUARD else EPSILON_GUARD)
    if p01_new > max_p01:
        p01_new = max_p01
    elif p01_new < -max_p01:
        p01_new = -max_p01
        
    # [5] 실제 측정값 반영 (Measurement Update - State)
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation
    
    # [6] 수치적 발산 및 NaN 고장 감지 시 Failsafe 분기 구조 논리 교정
    if (math.isnan(x0_new) or math.isnan(x1_new) or
        math.isnan(p00_new) or math.isnan(p01_new) or math.isnan(p11_new) or
        abs(x0_new) > 1e10 or abs(x1_new) > 1e10):
        # 영점(0.0) 추락 대신 직전 예측값(Prediction)을 유지하여 신호 파형의 연속성 보존
        x0_new, x1_new = x0_pred, x1_pred
        p00_new, p01_new, p11_new = 1.0, 0.0, 1.0
        
    # [7] 의도 에너지 및 최종 매핑 확률 연산
    X_intent_energy = x0_new * x0_new + x1_new * x1_new
    scaled_energy = lambda_val * X_intent_energy
    if scaled_energy > 20.0:
        raw_prob = 1.0
    else:
        raw_prob = (2.0 / (1.0 + math.exp(-scaled_energy))) - 1.0
        
    local_theta = theta if theta < 0.9999 else 0.9999
    if raw_prob < local_theta:
        p_state = 0.0
    else:
        p_state = (raw_prob - local_theta) / (1.0 - local_theta)
        
    return p00_new, p01_new, p11_new, x0_new, x1_new, p_state


# -------------------------------------------------------------
# [필터 구동 엔진 클래스]
# -------------------------------------------------------------
class RealtimeBypassMassageEngine:
    def __init__(self, sample_rate=250.0, target_freq=10.0):
        dt = 1.0 / sample_rate
        theta_rot = 2.0 * math.pi * target_freq * dt
        self.cos_t = float(math.cos(theta_rot))
        self.sin_t = float(math.sin(theta_rot))
        self.q_noise = 1e-4
        self.r_noise = 1e-2
        self.lambda_val = 0.5
        self.p00, self.p01, self.p11 = 1.0, 0.0, 1.0
        self.x0, self.x1 = 0.0, 0.0

    def process_sample(self, raw_signal, current_th):
        self.p00, self.p01, self.p11, self.x0, self.x1, p_state = _execute_single_step_core(
            float(raw_signal), self.p00, self.p01, self.p11, self.x0, self.x1,
            self.cos_t, self.sin_t, self.q_noise, self.r_noise, self.lambda_val, float(current_th)
        )
        return p_state
import socket
import sys
import gc
from filter_core import RealtimeBypassMassageEngine

# -------------------------------------------------------------
# [환경 설정 및 상수]
# -------------------------------------------------------------
BUFFER_MAX_SIZE = 4096
THRESHOLD_AUTOBIO_ACTIVE = 0.55
THRESHOLD_AUTOBIO_INACTIVE = 0.75

# -------------------------------------------------------------
# [통합 신경 우회 파이프라인 구동 루프]
# -------------------------------------------------------------
def run_integrated_neural_bypass(host="127.0.0.1", port=9999):
    gc.disable()  # 오버헤드 방지를 위해 가비지 컬렉션 비활성화
    engine = RealtimeBypassMassageEngine()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    conn = None
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"[*] Consciousness Bypass Core bound successfully. Listening on {host}:{port}")
        
        conn, addr = server_socket.accept()
        print(f"[+] Bi-directional stream established with sensor device: {addr}")
        conn.settimeout(0.02)  # 20ms 타임아웃 윈도우 설정
        
        recv_buffer = bytearray(BUFFER_MAX_SIZE)
        buf_view = memoryview(recv_buffer)
        bytes_in_buffer = 0
        last_valid_sample = 0.0
        current_th = THRESHOLD_AUTOBIO_INACTIVE
        
        send_buffer = bytearray(b"0.0000\n")
        send_view = memoryview(send_buffer)
        
        while True:
            try:
                if bytes_in_buffer >= BUFFER_MAX_SIZE:
                    print("[⚠] Buffer Full without Newlines. Flushing static buffer memories.")
                    bytes_in_buffer = 0
                    
                max_receivable = BUFFER_MAX_SIZE - bytes_in_buffer
                bytes_received = conn.recv_into(buf_view[bytes_in_buffer: bytes_in_buffer + max_receivable])
                if not bytes_received:
                    print("[-] Stream interface disconnected by host device.")
                    break
                    
                bytes_in_buffer += bytes_received
                start_ptr = 0
                
                while True:
                    newline_idx = recv_buffer.find(b'\n', start_ptr, bytes_in_buffer)
                    if newline_idx == -1:
                        break
                        
                    line_view = buf_view[start_ptr: newline_idx]
                    start_ptr = newline_idx + 1
                    if len(line_view) == 0:
                        continue
                        
                    try:
                        comma_idx = -1
                        for i in range(len(line_view)):
                            if line_view[i] == 44:  # ',' 캐릭터 감지
                                comma_idx = i
                                break
                                
                        if comma_idx == -1:
                            raw_signal = float(bytes(line_view))
                            autobio_flag = 0
                        else:
                            raw_signal = float(bytes(line_view[:comma_idx]))
                            autobio_flag = int(bytes(line_view[comma_idx+1:]))
                            
                        last_valid_sample = raw_signal
                        current_th = THRESHOLD_AUTOBIO_ACTIVE if autobio_flag == 1 else THRESHOLD_AUTOBIO_INACTIVE
                    except (ValueError, IndexError):
                        continue
                        
                    p_state = engine.process_sample(raw_signal, current_th)
                    p_int = int(p_state * 10000)
                    if p_int > 10000: p_int = 10000
                    elif p_int < 0: p_int = 0
                    
                    # 제로 카피 스트림 패킹 구조 최적화
                    send_buffer[0] = 48 + (p_int // 10000)
                    send_buffer[2] = 48 + ((p_int // 1000) % 10)
                    send_buffer[3] = 48 + ((p_int // 100) % 10)
                    send_buffer[4] = 48 + ((p_int // 10) % 10)
                    send_buffer[5] = 48 + (p_int % 10)
                    
                    conn.sendall(send_view[:7])
                    
                if start_ptr > 0:
                    # 논리 수정: 잔여 버퍼 이동 시 영역 오염 방지를 위해 memoryview 슬라이싱을 안전하게 대입
                    rem_len = bytes_in_buffer - start_ptr
                    if rem_len > 0:
                        recv_buffer[:rem_len] = buf_view[start_ptr:bytes_in_buffer]
                    bytes_in_buffer = rem_len
                    
            except socket.timeout:
                # 하드웨어 단말 지연으로 인한 20ms 타임아웃 대응 논리 복구
                p_state = engine.process_sample(last_valid_sample, current_th)
                bytes_in_buffer = 0
                try:
                    conn.sendall(b"0.0000,HOLD\n")
                except socket.error:
                    print("[-] Failed to transmit HOLD signal. Terminating connection.")
                    break
            except Exception:
                continue
                
    except Exception as system_critical_error:
        print(f"[💥] System Critical Breakdown Detected: {system_critical_error}", file=sys.stderr)
        
    finally:
        print("[*] Launching Failsafe Sequence...")
        if conn:
            try:
                conn.sendall(b"0.0000,EMERGENCY_STOP\n")
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except Exception:
                pass
        server_socket.close()
        gc.enable()  # 자원 정리 단계에서 다시 GC 활성화
        print("[*] Consciousness Neural Bypass Pipeline Safely Terminated.")

if __name__ == "__main__":
    run_integrated_neural_bypass()
