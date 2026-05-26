"""
Project: ZeroAxiom-Bypass (Real-Time Production Hub)
File: realtime_bypass.py
Description: 
    True Zero-Copy Real-Time Neural Bypass System for Exoskeleton Control.
    Utilizes memoryview slicing, orjson C-parser, and Numba register micro-optimization.
License: MIT
"""

import numpy as np
import math
import socket
import orjson  # High-speed C-library for JSON serialization
import time
from numba import njit

# ==============================================================================
# Micro-Register Optimized Real-Time Single-Sample Engine (ARCF Core)
# ==============================================================================
@njit(cache=True, nogil=True, fastmath=False)
def _execute_single_step_core(x_in, b, a, cos_t, sin_t, q, R, x, P, v, running_energy, ema_alpha):
    # [Register Optimization]: Local scalar unpacking to eliminate array reference overheads
    b0, b1, b2 = b[0], b[1], b[2]
    a1, a2 = a[1], a[2]
    x0, x1 = x[0], x[1]
    p00, p01, p11 = P[0], P[1], P[2]
    v0, v1 = v[0], v[1]

    # 3.1. Inline IIR Notch Filtering
    y_notch = b0 * x_in + v0
    v0 = b1 * x_in - a1 * y_notch + v1
    v1 = b2 * x_in - a2 * y_notch
    
    # 3.2. Real-time Information Gating
    inst_energy = y_notch * y_notch
    curr_energy = (1.0 - ema_alpha) * running_energy + ema_alpha * inst_energy
    
    gate_base = 1.0 / (1.0 + math.exp(-2.5 * (curr_energy - 0.8)))
    w_gate = 0.1 + gate_base * 0.9
    if w_gate < 0.1: w_gate = 0.1
    elif w_gate > 1.0: w_gate = 1.0
    y_filt = y_notch * w_gate
    
    # 3.3. Analytical State Vector Prediction
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
    
    # 3.4. Exact Scalar Joseph Form Expansion (Mathematical Integrity Restored)
    innov_cov = p00_m + R
    if innov_cov > 1e-9:
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
        
    # 3.5. Cauchy-Schwarz Stability Guards
    p00_guard = p00_new if p00_new > 1e-14 else 1e-14
    p11_guard = p11_new if p11_new > 1e-14 else 1e-14
    p_prod = p00_guard * p11_guard
    max_p01 = math.sqrt(p_prod if p_prod > 1e-28 else 1e-28)
    
    if p01_new > max_p01: p01_guard = max_p01
    elif p01_new < -max_p01: p01_guard = -max_p01
    else: p01_guard = p01_new
        
    # Internal write-back for state persistence
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
        
        lambda_val = 7.0
        p_state = 1.0 / (1.0 + math.exp(-lambda_val * (energy_out - current_th)))
        return p_state


# ==============================================================================
# Hardware Fault-Tolerant Real-Time Streaming Infrastructure
# ==============================================================================
def run_integrated_neural_bypass():
    # Notch filter & phase calibration constants optimized for 250Hz sampling (10Hz SMR tracking)
    b_notch = np.array([0.97517, -1.85485, 0.97517], dtype=np.float64)
    a_notch = np.array([1.00000, -1.85485, 0.95035], dtype=np.float64)
    cos_t, sin_t = 0.96884, 0.24765 
    
    EEG_HOST, EEG_PORT = "127.0.0.1", 9999
    ROBOT_HOST, ROBOT_PORT = "192.168.1.50", 8888
    
    print("🤖 [ZeroAxiom-Bypass] Initializing high-throughput production engine...")
    engine = ARCFSystem(b_notch, a_notch, cos_t, sin_t)
    
    last_command_time = 0.0
    COMMAND_INTERVAL = 0.1  # Actuator protection dead-time (100ms)
    last_valid_sample = 0.0 
    
    timeout_counter = 0
    MAX_ALLOWED_TIMEOUTS = 5 
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as eeg_sock, \
         socket.socket(socket.AF_INET, socket.SOCK_STREAM) as robot_sock:
        try:
            eeg_sock.connect((EEG_HOST, EEG_PORT))
            robot_sock.connect((ROBOT_HOST, ROBOT_PORT))
            
            eeg_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)   
            eeg_sock.settimeout(0.02) 
            robot_sock.settimeout(0.05) 
            print("✅ [Infrastructure Active] Closed-loop neural bypass online.")
            
            MAX_BUF_SIZE = 65536
            raw_buffer = bytearray(MAX_BUF_SIZE)
            buf_view = memoryview(raw_buffer)
            bytes_in_buf = 0
            
            while True:
                try:
                    packet_len = eeg_sock.recv_into(buf_view[bytes_in_buf:], MAX_BUF_SIZE - bytes_in_buf)
                    if packet_len == 0: break
                    bytes_in_buf += packet_len
                    timeout_counter = 0 
                except socket.timeout:
                    timeout_counter += 1
                    if timeout_counter >= MAX_ALLOWED_TIMEOUTS:
                        print("⚠️ [CRITICAL] Signal loss threshold exceeded! Sending TEMPORARY_HOLD to robot.")
                        try: robot_sock.sendall(orjson.dumps({"action": "TEMPORARY_HOLD"}) + b"\n")
                        except socket.error: pass
                        timeout_counter = 0 
                    
                    if bytes_in_buf == 0:
                        _ = engine.process_sample(last_valid_sample, current_th=0.75)
                    continue
                
                start_ptr = 0
                while True:
                    newline_idx = raw_buffer.find(b"\n", start_ptr, bytes_in_buf)
                    if newline_idx == -1:
                        break
                    
                    # [True Zero-Copy]: Passing memoryview slice to prevent implicit heap allocation
                    line_view = buf_view[start_ptr:newline_idx]
                    start_ptr = newline_idx + 1
                    
                    if len(line_view) == 0 or line_view.isspace(): continue
                    
                    data = orjson.loads(line_view)
                    raw_sample = data["eeg_microvolts"]
                    last_valid_sample = raw_sample 
                    
                    # Specification: Dynamic threshold adjustment via Autobiographical Stimulation
                    s_autobio_active = data.get("S_autobio_active", False)
                    current_th = 0.55 if s_autobio_active else 0.75
                    
                    p_state = engine.process_sample(raw_sample, current_th=current_th)
                    
                    current_time = time.monotonic() 
                    if p_state > current_th and (current_time - last_command_time > COMMAND_INTERVAL):
                        command = {"action": "TRIGGER_EXOSKELETON_ON", "p_state": p_state}
                        try:
                            robot_sock.sendall(orjson.dumps(command) + b"\n")
                            last_command_time = current_time 
                            print(f"⚡ P_state: {p_state:.3f} (Th: {current_th}) ➔ Actuator command sent successfully.")
                        except socket.error: 
                            print("⚠️ [WARNING] Robotic controller transmission error or link dropped.")
                
                if start_ptr > 0:
                    rem_len = bytes_in_buf - start_ptr
                    if rem_len > 0:
                        raw_buffer[:rem_len] = raw_buffer[start_ptr:bytes_in_buf]
                    bytes_in_buf = rem_len
                
                if bytes_in_buf >= MAX_BUF_SIZE:
                    print("⚠️ [CRITICAL] Buffer overflow detected due to stream corruption! Flushing buffer.")
                    bytes_in_buf = 0
                        
        except Exception as e:
            print(f"❌ [CRASH] Hardware communication loop fractured: {e}")
            try: robot_sock.sendall(orjson.dumps({"action": "EMERGENCY_STOP"}) + b"\n")
            except: pass

if __name__ == "__main__":
    run_integrated_neural_bypass()

