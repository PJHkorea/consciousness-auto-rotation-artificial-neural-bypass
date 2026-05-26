@njit(cache=True) 
def execute_perfect_kalman_v5(y_ccl, t_arr, noise_arr, cos_t, sin_t, q, R):
    N_samples = len(y_ccl)
    x0, x1 = 0.0, 0.0
    p00, p01, p11 = 1.0, 0.0, 1.0  
    
    energy_out = np.empty(N_samples, dtype=np.float64) 
    
    cos_sq = cos_t * cos_t
    sin_sq = sin_t * sin_t
    two_cos_sin = 2.0 * cos_t * sin_t
    
    for i in range(N_samples):
        t_curr = t_arr[i]
        
        # 1. Real-time Gating (시간 기반 제어)
        if t_curr < 3.5:
            w_gate = 0.1
        elif t_curr <= 4.5:
            w_gate = 0.1 + 0.8 * (t_curr - 3.5)
        elif t_curr <= 7.0:
            w_gate = 0.9
        else:
            w_gate = 0.9 - 0.8 * (t_curr - 7.0)
            
        # 노이즈 반영 후 하한선(0.1) 최종 보장
        w_gate += noise_arr[i]
        if w_gate < 0.1:
            w_gate = 0.1
            
        y_filt = y_ccl[i] * w_gate
        
        # 2. Prediction Step
        x0_m = cos_t * x0 - sin_t * x1
        x1_m = sin_t * x0 + cos_t * x1
        
        p00_m = cos_sq * p00 - two_cos_sin * p01 + sin_sq * p11 + q
        p01_m = cos_t * sin_t * p00 + (cos_sq - sin_sq) * p01 - cos_t * sin_t * p11
        p11_m = sin_sq * p00 + two_cos_sin * p01 + cos_sq * p11 + q
        
        # 3. Kalman Gain Step
        innov_cov = p00_m + R
        if innov_cov > 1e-9:
            inv_innov = 1.0 / innov_cov
            k0 = p00_m * inv_innov
            k1 = p01_m * inv_innov  
            
            # 4. Update States
            v = y_filt - x0_m
            x0 = x0_m + k0 * v
            x1 = x1_m + k1 * v
            
            # 5. Covariance Update (수치 대칭성 강화를 위한 대수적 단순화)
            # (I - K*H) 형태 반영: H = [1, 0] 이므로 
            # p00_new = (1-k0)*p00_m*(1-k0) + k0*R*k0 같은 형태로 정리 가능
            m0 = 1.0 - k0
            p00_new = m0 * p00_m * m0 + k0 * k0 * R
            p01_new = m0 * p01_m - k1 * p00_m * m0 + k0 * k1 * R
            p11_new = p11_m - 2.0 * k1 * p01_m + k1 * k1 * p00_m + k1 * k1 * R
        else:
            x0, x1 = x0_m, x1_m
            p00_new, p01_new, p11_new = p00_m, p01_m, p11_m
        
        # 6. Bound Constraints (기존 무결성 로직 유지)
        p00 = p00_new if p00_new > 1e-14 else 1e-14
        p11 = p11_new if p11_new > 1e-14 else 1e-14
        
        max_p01 = math.sqrt(p00 * p11)
        if p01_new > max_p01:
            p01 = max_p01
        elif p01_new < -max_p01:
            p01 = -max_p01
        else:
            p01 = p01_new
        
        energy_out[i] = x0 * x0 + x1 * x1
        
    return energy_out
