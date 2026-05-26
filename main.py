import math
import numpy as np
from numba import njit

@njit(cache=True, nogil=True, fastmath=True) 
def execute_realtime_kalman_final(y_ccl, t_arr, noise_arr, cos_t, sin_t, q, R, energy_out):
    # 1. 입력 배열 크기 불일치로 인한 세그멘테이션 폴트 방지 가드
    N_samples = len(y_ccl)
    if N_samples == 0 or len(t_arr) < N_samples or len(noise_arr) < N_samples or len(energy_out) < N_samples:
        return
        
    # 2. 명시적 스칼라 변환으로 컴파일 타임 타입 불일치 방지
    cos_t_f = float(cos_t)
    sin_t_f = float(sin_t)
    q_f = float(q)
    R_f = float(R)
    
    # 3. 실시간 최적화: 첫 번째 샘플로 초기 상태(x0) 동적 정렬
    w_gate_init = 0.1 if t_arr[0] < 3.5 else 0.9  
    x0 = float(y_ccl[0] * w_gate_init)
    x1 = 0.0
    
    # 초기 공분산 설정
    p00, p01, p11 = 2.0, 0.0, 2.0  
    
    cos_sq = cos_t_f * cos_t_f
    sin_sq = sin_t_f * sin_t_f
    two_cos_sin = 2.0 * cos_t_f * sin_t_f
    
    for i in range(N_samples):
        t_curr = t_arr[i]
        
        # Real-time Gating (시간 기반 제어)
        if t_curr < 3.5:
            w_gate = 0.1
        elif t_curr <= 4.5:
            w_gate = 0.1 + 0.8 * (t_curr - 3.5)
        elif t_curr <= 7.0:
            w_gate = 0.9
        else:
            w_gate = 0.9 - 0.8 * (t_curr - 7.0)
            
        w_gate += noise_arr[i]
        
        # 하드 오퍼레이셔널 가드: 과도한 노이즈로 인한 신호 왜곡 차단
        if w_gate < 0.1:
            w_gate = 0.1
        elif w_gate > 1.0:
            w_gate = 1.0
            
        y_filt = y_ccl[i] * w_gate
        
        # Prediction Step (예측 단계)
        x0_m = cos_t_f * x0 - sin_t_f * x1
        x1_m = sin_t_f * x0 + cos_t_f * x1
        
        p00_m = cos_sq * p00 - two_cos_sin * p01 + sin_sq * p11 + q_f
        p01_m = cos_t_f * sin_t_f * p00 + (cos_sq - sin_sq) * p01 - cos_t_f * sin_t_f * p11
        p11_m = sin_sq * p00 + two_cos_sin * p01 + cos_sq * p11 + q_f
        
        # Kalman Gain Step (칼만 이득 계산)
        innov_cov = p00_m + R_f
        if innov_cov > 1e-9:
            inv_innov = 1.0 / innov_cov
            k0 = p00_m * inv_innov
            k1 = p01_m * inv_innov  
            
            # Update States (상태 업데이트)
            v = y_filt - x0_m
            x0 = x0_m + k0 * v
            x1 = x1_m + k1 * v
            
            # Covariance Update (조셉 형태 완벽 정밀 교정 및 SIMD 융합 최적화)
            m0 = 1.0 - k0
            k0_R = k0 * R_f
            k1_R = k1 * R_f
            
            p00_new = m0 * p00_m * m0 + k0 * k0_R
            p01_new = m0 * p01_m - k1 * p00_m * m0 + k0 * k1_R
            p11_new = p11_m - 2.0 * k1 * p01_m + k1 * k1 * p00_m + k1 * k1_R
        else:
            x0, x1 = x0_m, x1_m
            p00_new, p01_new, p11_new = p00_m, p01_m, p11_m
        
        # Bound Constraints (수치적 상/하한선 제약 및 수치 안정성 보강)
        p00 = p00_new if p00_new > 1e-14 else 1e-14
        p11 = p11_new if p11_new > 1e-14 else 1e-14
        
        # p00 * p11 연산이 미세하게 음수가 되거나 언더플로우가 나는 것을 방지하는 클램핑 가드
        p_prod = p00 * p11
        max_p01 = math.sqrt(p_prod if p_prod > 1e-28 else 1e-28)
        
        if p01_new > max_p01:
            p01 = max_p01
        elif p01_new < -max_p01:
            p01 = -max_p01
        else:
            p01 = p01_new
        
        energy_out[i] = x0 * x0 + x1 * x1
