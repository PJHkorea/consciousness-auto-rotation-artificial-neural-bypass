import numpy as np
import numba as nb
import math
import socket
import sys
import gc

# -------------------------------------------------------------
# [환경 설정 및 상수 / Configuration & Constants]
# -------------------------------------------------------------
EPSILON_INNOV = 1e-6
EPSILON_GUARD = 1e-12

# -------------------------------------------------------------
# [고속 연산 코어 - Numba JIT 적용 / High-Speed JIT Core]
# -------------------------------------------------------------
@nb.njit(cache=True, nogil=True, fastmath=False)
def _execute_single_step_core(
    raw_signal, p00, p01, p11, x0, x1,
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    """
    HPNT 단일 채널 상태 공간 추정 및 수치해석 안정성 가드 연산 코어 (No-SQRT 및 CW 부호 정정본)
    Pure Scalar + No-SQRT Estimation Kernel with Clockwise Rotation Alignment.
    """
    # [1] 상태 공간 시스템 동역학 예측 (Time Update - State) / Clockwise 전진 변환
    x0_pred = cos_t * x0 - sin_t * x1
    x1_pred = sin_t * x0 + cos_t * x1

    cos_sq = cos_t * cos_t
    sin_sq = sin_t * sin_t
    cos_sin = cos_t * sin_t

    # [2] 오차 공분산 예측 (Time Update - Covariance) / CW 부호 완전 정정
    p00_m = (cos_sq * p00) - (2.0 * cos_sin * p01) + (sin_sq * p11) + q_noise
    p11_m = (sin_sq * p00) + (2.0 * cos_sin * p01) + (cos_sq * p11) + q_noise
    p01_m = ((cos_sq - sin_sq) * p01) - (cos_sin * (p00 - p11))

    # 부동소수점 오차로 인한 음수 분산 방지 (하한선 제약 정합)
    if p00_m < 1e-6: p00_m = 1e-6
    if p11_m < 1e-6: p11_m = 1e-6

    # [No-SQRT Cauchy-Schwarz Guard] 양변 제곱 비교를 통한 루트 연산 원천 배제
    p_prod_m = p00_m * p11_m
    p01_m_sq = p01_m * p01_m
    if p01_m_sq > p_prod_m or math.isnan(p01_m_sq):
        min_diag = p00_m if p00_m < p11_m else p11_m
        p01_m = min_diag if p01_m > 0.0 else -min_diag
    # [3] 측정 갱신을 위한 이노베이션 분산 및 칼만 이득 계산
    innov_cov = p00_m + r_noise
    if innov_cov < EPSILON_INNOV:
        innov_cov = EPSILON_INNOV
    
    s_inv = 1.0 / innov_cov
    k0 = p00_m * s_inv
    if k0 > 1.0: k0 = 1.0
    k1 = p01_m * s_inv
    one_minus_k0 = 1.0 - k0

    # [4] Symmetric Joseph Form 구조 기반 사후 오차 공분산 업데이트 (오타 회귀 버그 원천 차단)
    k1_sq = k1 * k1
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = one_minus_k0 * (p01_m - k1 * p00_m) + (k0 * k1 * r_noise)
    p11_new = p11_m - (2.0 * k1 * one_minus_k0 * p01_m) + (k1_sq * p00_m) + (k1_sq * r_noise)

    if p00_new < 1e-6: p00_new = 1e-6
    if p11_new < 1e-6: p11_new = 1e-6

    # 사후 업데이트 No-SQRT Cauchy-Schwarz Stability Guard
    p_prod = p00_new * p11_new
    p01_new_sq = p01_new * p01_new
    if p01_new_sq > p_prod or math.isnan(p01_new_sq):
        min_diag_new = p00_new if p00_new < p11_new else p11_new
        p01_new = min_diag_new if p01_new > 0.0 else -min_diag_new

    # [5] 실제 측정값 반영 (Measurement Update - State)
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation

    # [6] 수치적 발산 및 NaN 고장 감지 시 Failsafe 분기 구조 논리 교정
    if (math.isnan(x0_new) or math.isnan(x1_new) or
        math.isnan(p00_new) or math.isnan(p01_new) or math.isnan(p11_new) or
        abs(x0_new) > 1e4 or abs(x1_new) > 1e4):
        x0_new, x1_new = x0_pred, x1_pred
        p00_new, p01_new, p11_new = 1.0, 0.0, 1.0

    # [7] 의도 에너지 및 최종 매핑 확률 연산 (Padé [1/1] 유리함수 스케일 다운 및 오버슛 교정 완료)
    X_intent_energy = x0_new * x0_new + x1_new * x1_new
    scaled_energy = lambda_val * X_intent_energy
    raw_prob = 0.0

    if scaled_energy > 0.0 and not math.isnan(scaled_energy):
        if scaled_energy >= 3.4641016151377545:
            raw_prob = 1.0
        else:
            num = 6.0 * scaled_energy
            den = 12.0 + (scaled_energy * scaled_energy)
            raw_prob = num / den
            if raw_prob > 1.0: raw_prob = 1.0
            if raw_prob < 0.0: raw_prob = 0.0

    local_theta = theta if theta < 0.9999 else 0.9999
    if raw_prob < local_theta:
        p_state = 0.0
    else:
        p_state = (raw_prob - local_theta) / (1.0 - local_theta)

    return p00_new, p01_new, p11_new, x0_new, x1_new, p_state

# -------------------------------------------------------------
# [필터 구동 엔진 클래스 / Filter Core Engine Class]
# -------------------------------------------------------------
class RealtimeBypassMassageEngine:
    def __init__(self, sample_rate=250.0, target_freq=10.0):
        dt = 1.0 / sample_rate
        theta_rot = 2.0 * math.pi * target_freq * dt
        self.cos_t = float(math.cos(theta_rot))
        self.sin_t = float(math.sin(theta_rot))
        self.q_noise = 1e-4
        self.r_noise = 1e-2
        self.lambda_val = 0.1  # 에너지 압축 변환을 위한 스케일 정합
        self.p00, self.p01, self.p11 = 1.0, 0.0, 1.0
        self.x0, self.x1 = 0.0, 0.0

    def process_sample(self, raw_signal, current_th):
        self.p00, self.p01, self.p11, self.x0, self.x1, p_state = _execute_single_step_core(
            float(raw_signal), self.p00, self.p01, self.p11, self.x0, self.x1,
            self.cos_t, self.sin_t, self.q_noise, self.r_noise, self.lambda_val, float(current_th)
        )
        return p_state
# -------------------------------------------------------------
# [환경 설정 및 상수 / Configuration & Constants]
# -------------------------------------------------------------
BUFFER_MAX_SIZE = 4096
THRESHOLD_AUTOBIO_ACTIVE = 0.55
THRESHOLD_AUTOBIO_INACTIVE = 0.75

# -------------------------------------------------------------
# [통합 신경 우회 파이프라인 구동 루프 / Integrated Neural Bypass Loop]
# -------------------------------------------------------------
def run_integrated_neural_bypass(host="127.0.0.1", port=9999):
    gc.disable()  # 오버헤드 방지를 위해 가비지 컬렉션 비활성화
    engine = RealtimeBypassMassageEngine()
    
    # JIT 지연 시간 무력화를 위한 최초 웜업 실행
    _ = engine.process_sample(0.0, THRESHOLD_AUTOBIO_INACTIVE)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn = None
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"[*] Consciousness Bypass Core bound successfully. Listening on {host}:{port}")
        conn, addr = server_socket.accept()
        print(f"[+] Bi-directional stream established with sensor device: {addr}")
        
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        conn.settimeout(0.02)  # 20ms 타임아웃 윈도우 설정

        recv_buffer = bytearray(BUFFER_MAX_SIZE)
        buf_view = memoryview(recv_buffer)
        bytes_in_buffer = 0
        last_valid_sample = 0.0
        current_th = THRESHOLD_AUTOBIO_INACTIVE
        
        send_buffer = bytearray(b"0.0000\n")
        send_view = memoryview(send_buffer)

        # 연속 타임아웃 발생 횟수를 추적할 레지스터 변수 선언
        consecutive_timeouts = 0

        while True:
            try:
                if bytes_in_buffer >= BUFFER_MAX_SIZE:
                    print("[⚠] Buffer Full without Newlines. Flushing static buffer memories.")
                    bytes_in_buffer = 0
                    
                max_receivable = BUFFER_MAX_SIZE - bytes_in_buffer
                bytes_received = conn.recv_into(buf_view[bytes_in_buffer:bytes_in_buffer + max_receivable])
                if not bytes_received:
                    print("[-] Stream interface disconnected by host device.")
                    break
                bytes_in_buffer += bytes_received

                start_ptr = 0
                while True:
                    newline_idx = recv_buffer.find(b'\n', start_ptr, bytes_in_buffer)
                    if newline_idx == -1:
                        break
                    line_view = buf_view[start_ptr:newline_idx]
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

                    # 스트림 데이터 패킷이 성공적으로 안착하면 타임아웃 카운터 즉시 리셋
                    consecutive_timeouts = 0

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
                    rem_len = bytes_in_buffer - start_ptr
                    if rem_len > 0:
                        recv_buffer[:rem_len] = buf_view[start_ptr:bytes_in_buffer]
                    bytes_in_buffer = rem_len

            except socket.timeout:
                consecutive_timeouts += 1
                
                # ─── [🛡️ 임상 페일세이프 가드 / Clinical Failsafe Guard] ───
                # 연속 타임아웃이 5회(5 * 20ms = 100ms)를 넘어가면 완전 단선 또는 환자 패드 탈조로 판단.
                # 무한 관성 구동을 전면 차단하고 강제로 break하여 finally 블록의 EMERGENCY_STOP 패킷을 송출.
                if consecutive_timeouts >= 5:
                    print("[🚨] Critical: Connection lost for over 100ms. Aborting inertia massage.", file=sys.stderr)
                    break

                # 100ms 미만의 일시적 네트워크 지터 구간에서만 원래 사상대로 관성 추종 제어 가동
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
