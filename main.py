import numpy as np
import numba as nb
import math
import matplotlib.pyplot as plt

# =========================================================================
# CORE FILTER ENGINE (Fixed Mathematical Formula & Cleaned Dead Code)
# =========================================================================
@nb.njit(cache=True, nogil=True, fastmath=False)
def _execute_single_step_core(
    raw_signal, p00, p01, p11, x0, x1, 
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta
):
    # State Prediction
    x0_pred = cos_t * x0 - sin_t * x1
    x1_pred = sin_t * x0 + cos_t * x1

    cos_sq = cos_t * cos_t
    sin_sq = sin_t * sin_t
    cos_sin = cos_t * sin_t

    # Covariance Prediction
    p00_m = (cos_sq * p00) - (2.0 * cos_sin * p01) + (sin_sq * p11) + q_noise
    p01_m = (cos_sin * (p00 - p11)) + ((cos_sq - sin_sq) * p01)
    p11_m = (sin_sq * p00) + (2.0 * cos_sin * p01) + (cos_sq * p11) + q_noise
    
    p_prod_m = p00_m * p11_m
    max_p01_m = math.sqrt(p_prod_m if p_prod_m > 1e-56 else 1e-56)
    if abs(p01_m) > max_p01_m:
        p01_m = max_p01_m if p01_m >= 0.0 else -max_p01_m

    # Innovation Covariance
    innov_cov = p00_m + r_noise
    if innov_cov < 1e-9:
        innov_cov = 1e-9

    # Kalman Gain
    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov

    one_minus_k0 = 1.0 - k0

    # Josephson Form Covariance Update (Corrected & Standardized)
    p00_new = (one_minus_k0 * one_minus_k0 * p00_m) + (k0 * k0 * r_noise)
    p01_new = (one_minus_k0 * p01_m) - (k1 * one_minus_k0 * p00_m) + (k0 * k1 * r_noise)
    p11_new = p11_m - (2.0 * k1 * p01_m) + (k1 * k1 * p00_m) + (k1 * k1 * r_noise)

    # Hard Bounds for Stability
    if p00_new < 1e-28: p00_new = 1e-28
    if p11_new < 1e-28: p11_new = 1e-28

    p_prod = p00_new * p11_new
    max_p01 = math.sqrt(p_prod if p_prod > 1e-56 else 1e-56)
    if abs(p01_new) > max_p01:
        p01_new = max_p01 if p01_new >= 0.0 else -max_p01

    # State Update
    innovation = raw_signal - x0_pred
    x0_new = x0_pred + k0 * innovation
    x1_new = x1_pred + k1 * innovation

    # Exception Guard
    if (math.isnan(x0_new) or math.isnan(x1_new) or 
        math.isnan(p00_new) or math.isnan(p01_new) or math.isnan(p11_new) or
        not (abs(x0_new) < 1e10 and abs(x1_new) < 1e10 and 
             p00_new >= 1e-28 and p00_new < 1e10 and 
             abs(p01_new) < 1e10 and 
             p11_new >= 1e-28 and p11_new < 1e10)):
        x0_new, x1_new = 0.0, 0.0
        p00_new, p01_new, p11_new = 1.0, 0.0, 1.0

    # Energy Probability Mapping (Simplified Logic)
    X_intent_energy = x0_new * x0_new + x1_new * x1_new
    scaled_energy = lambda_val * X_intent_energy

    if scaled_energy > 16.0:
        raw_prob = 1.0
    elif scaled_energy < 1e-12:
        raw_prob = 0.0
    else:
        raw_prob = (2.0 / (1.0 + math.exp(-scaled_energy))) - 1.0

    local_theta = theta if theta < 1.0 else 0.999999
    p_state = 0.0 if raw_prob < local_theta else (raw_prob - local_theta) / (1.0 - local_theta)

    return p00_new, p01_new, p11_new, x0_new, x1_new, p_state


# =========================================================================
# BATCH EXECUTION LOOP 
# =========================================================================
@nb.njit(cache=True, nogil=True, fastmath=False)
def _process_batch_loop(
    signal_array, est_x0, prob_history, p00, p01, p11, x0, x1,
    cos_t, sin_t, q_noise, r_noise, lambda_val, theta_gate
):
    n_samples = len(signal_array)
    for i in range(n_samples):
        p00, p01, p11, x0, x1, p_state = _execute_single_step_core(
            signal_array[i], p00, p01, p11, x0, x1,
            cos_t, sin_t, q_noise, r_noise, lambda_val, theta_gate
        )
        est_x0[i] = x0
        prob_history[i] = p_state
        
    return p00, p01, p11, x0, x1


# =========================================================================
# WRAPPER INTERFACE (Optimized Overhead)
# =========================================================================
class ScalarJosephKalmanFilter:
    def __init__(self, fs, target_freq, q_noise=1e-3, r_noise=2.25, lambda_val=0.5, theta_gate=0.3):
        dt = 1.0 / fs
        theta_rot = 2.0 * np.pi * target_freq * dt
        
        self.cos_t = float(np.cos(theta_rot))
        self.sin_t = float(np.sin(theta_rot))
        
        self.q_noise = float(q_noise)
        self.r_noise = float(r_noise)
        self.lambda_val = float(lambda_val)
        self.theta_gate = float(theta_gate)
        
        self.p00, self.p01, self.p11 = 1.0, 0.0, 1.0
        self.x0, self.x1 = 0.0, 0.0

    def update(self, raw_signal):
        self.p00, self.p01, self.p11, self.x0, self.x1, p_state = _execute_single_step_core(
            float(raw_signal), self.p00, self.p01, self.p11, self.x0, self.x1,
            self.cos_t, self.sin_t, self.q_noise, self.r_noise, self.lambda_val, self.theta_gate
        )
        return self.x0, p_state

    def process_batch(self, signal_array):
        # Fast & Safe array casting without redundant flag checking
        safe_signal = np.asarray(signal_array, dtype=np.float64)

        n_samples = len(safe_signal)
        est_x0 = np.zeros(n_samples, dtype=np.float64)
        prob_history = np.zeros(n_samples, dtype=np.float64)

        p00, p01, p11, x0, x1 = _process_batch_loop(
            safe_signal, est_x0, prob_history,
            self.p00, self.p01, self.p11, self.x0, self.x1,
            self.cos_t, self.sin_t, self.q_noise, self.r_noise, self.lambda_val, self.theta_gate
        )
        self.p00, self.p01, self.p11 = p00, p01, p11
        self.x0, self.x1 = x0, x1
            
        return est_x0, prob_history

    def reset(self):
        self.p00, self.p01, self.p11 = 1.0, 0.0, 1.0
        self.x0, self.x1 = 0.0, 0.0


# =========================================================================
# SIMULATION LAYER
# =========================================================================
def run_simulation():
    fs = 250.0
    dt = 1.0 / fs  
    target_freq = 10.0
    total_time = 10.0
    t = np.arange(0, total_time, dt)
    n_samples = len(t)

    pure_signal = np.sin(2.0 * np.pi * target_freq * t)
    noise = np.random.normal(0, 1.5, n_samples)
    raw_eeg = pure_signal + noise

    active_mask = (t >= 4.0) & (t <= 7.0)
    raw_eeg[active_mask] += 3.0 * np.sin(2.0 * np.pi * target_freq * t[active_mask])

    kf = ScalarJosephKalmanFilter(
        fs=fs, 
        target_freq=target_freq, 
        q_noise=1e-3, 
        r_noise=2.25, 
        lambda_val=0.5, 
        theta_gate=0.3
    )
    
    est_x0, prob_history = kf.process_batch(raw_eeg)

    plt.figure(figsize=(12, 8))
    
    plt.subplot(3, 1, 1)
    plt.plot(t, raw_eeg, color='gray', alpha=0.6, label='Raw EEG (with Noise)')
    plt.plot(t, pure_signal, color='blue', linestyle='--', label='Target Intent Ground Truth')
    plt.title('2x2 Pure Scalar Joseph Form Kalman Filter')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(t, est_x0, color='red', label='Kalman Estimated Phase X0')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(t, prob_history, color='green', label='Continuous Actuator Control Profile')
    plt.axhline(y=0.75, color='r', linestyle=':', label='Action Trigger Threshold (0.75)')
    plt.xlabel('Time (seconds)')
    plt.ylim(-0.05, 1.05)
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
