import socket
import sys
import gc
import math
import numba as nb

# =========================================================================
# CORE MATHEMATICAL FILTER PARAMETERS & GLOBAL CONSTANTS
# =========================================================================
EPSILON_INNOV = 1e-9       # Innovation Covariance Lower Bound
EPSILON_GUARD = 1e-28      # Cauchy-Schwarz Geometric Mean Safeguard
BUFFER_MAX_SIZE = 4096     # 정적 수신 버퍼 최대 크기 제한

THRESHOLD_AUTOBIO_ACTIVE = 0.55    # 자극 활성화 상태 임계값
THRESHOLD_AUTOBIO_INACTIVE = 0.75  # 일반 대기 상태 임계값

# -------------------------------------------------------------------------
# [Phase 1] 2x2 Joseph Form Kalman Filter & Stability Guard Core
# -------------------------------------------------------------------------
@nb.njit(cache=True, nogil=True, fastmath=False)
def _execute_single_step_core(
    raw_signal, p00, p01, p11, x0, x1,
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    # 1. State Prediction
    x0_pred = cos_t * x0 - sin_t * x1
    x1_pred = sin_t * x0 + cos_t * x1

    # 2. Error Covariance Prediction
    cos_sq = cos_t * cos_t
    sin_sq = sin_t * sin_t
    cos_sin = cos_t * sin_t

    p00_m = (cos_sq * p00) - (2.0 * cos_sin * p01) + (sin_sq * p11) + q_noise
    p01_m = (cos_sin * (p00 - p11)) + ((cos_sq - sin_sq) * p01)
    p11_m = (sin_sq * p00) + (2.0 * cos_sin * p01) + (cos_sq * p11) + q_noise

    # [Stability Guard Layer 1]
    p_prod_m = p00_m * p11_m
    max_p01_m = math.sqrt(p_prod_m if p_prod_m > EPSILON_GUARD else EPSILON_GUARD)
    if p01_m > max_p01_m: p01_m = max_p01_m
    elif p01_m < -max_p01_m: p01_m = -max_p01_m

    # 3. Kalman Gain
    innov_cov = p00_m + r_noise
    if innov_cov < EPSILON_INNOV: innov_cov = EPSILON_INNOV
    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov

    # 4. Exact Joseph Form Covariance Update
    one_minus_k0 = 1.0 - k0
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = (one_minus_k0 * p01_m) - (k1 * one_minus_k0 * p00_m) + (k0 * k1 * r_noise)
    p11_new = p11_m - (2.0 * k1 * p01_m) + (k1 * k1 * p00_m) + (k1 * k1 * r_noise)

    if p00_new < 1e-14: p00_new = 1e-14
    if p11_new < 1e-14: p11_new = 1e-14

    # [Stability Guard Layer 2]
    p_prod = p00_new * p11_new
    max_p01 = math.sqrt(p_prod if p_prod > EPSILON_GUARD else EPSILON_GUARD)
    if p01_new > max_p01: p01_new = max_p01
    elif p01_new < -max_p01: p01_new = -max_p01

    # 6. State Update
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation

    # Exception Guard
    if (math.isnan(x0_new) or math.isnan(x1_new) or 
        math.isnan(p00_new) or math.isnan(p01_new) or math.isnan(p11_new) or
        abs(x0_new) > 1e10 or abs(x1_new) > 1e10):
        x0_new, x1_new = 0.0, 0.0
        p00_new, p01_new, p11_new = 1.0, 0.0, 1.0

    # 7. Zero-Baseline Hyper-Sigmoid Gating Actuation
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

# -------------------------------------------------------------------------
# [Phase 2] Real-time TCP/IP Socket Infrastructure & Actuator Integration
# -------------------------------------------------------------------------
def run_integrated_neural_bypass(host="127.0.0.1", port=9999):
    gc.disable()
    engine = RealtimeBypassMassageEngine()  
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"[*] Consciousness Bypass Core bound successfully. Listening on {host}:{port}")
        
        conn, addr = server_socket.accept()
        print(f"[+] Bi-directional stream established with sensor device: {addr}")
        conn.settimeout(0.02)
        
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
                    bytes_in_buffer = 0  
                
                bytes_received = conn.recv_into(buf_view[bytes_in_buffer:])
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
                    if len(line_view) == 0: continue
                    
                    try:
                        comma_idx = -1
                        for i in range(len(line_view)):
                            if line_view[i] == 44:
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
                    
                    send_buffer[0] = 48 + (p_int // 10000)
                    send_buffer[2] = 48 + ((p_int // 1000) % 10)
                    send_buffer[3] = 48 + ((p_int // 100) % 10)
                    send_buffer[4] = 48 + ((p_int // 10) % 10)
                    send_buffer[5] = 48 + (p_int % 10)
                    
                    conn.sendall(send_view[:7]) 
                
                if start_ptr > 0:
                    recv_buffer[:bytes_in_buffer - start_ptr] = recv_buffer[start_ptr:bytes_in_buffer]
                    bytes_in_buffer -= start_ptr
                    
            except socket.timeout:
                p_state = engine.process_sample(last_valid_sample, current_th)
                bytes_in_buffer = 0
                try:
                    conn.sendall(b"0.0000,HOLD\n")
                except socket.error:
                    break
            except Exception:
                continue
                
    except Exception as system_critical_error:
        print(f"[💥] System Critical Breakdown Detected: {system_critical_error}", file=sys.stderr)
    finally:
        print("[*] Launching Failsafe Sequence...")
        try:
            conn.sendall(b"0.0000,EMERGENCY_STOP\n")
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
        except Exception:
            pass
        server_socket.close()
        gc.enable()
        print("[*] Consciousness Neural Bypass Pipeline Safely Terminated.")

if __name__ == "__main__":
    run_integrated_neural_bypass()
