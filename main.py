# Phase 3: State-Space Minimal Variance Estimation (Optimized Scalar Expansion)
dt = 1/fs
cos_t = np.cos(2 * np.pi * 10 * dt)
sin_t = np.sin(2 * np.pi * 10 * dt)

# Initial States & Error Covariances
x0, x1 = 0.0, 0.0
p00, p01, p10, p11 = 1.0, 0.0, 0.0, 1.0

# Hyperparameters
q_val = 0.01
R_val = 1.44     

X_intent_energy = np.zeros(N)

# 250Hz real-time processing loop (3rd Optimized Version)
for i in range(N):
    # Time Update (Predict)
    x0_minus = cos_t * x0 - sin_t * x1
    x1_minus = sin_t * x0 + cos_t * x1
    
    # 2x2 Matrix Multiplication (A * P) using structural symmetry
    ap00 = cos_t * p00 - sin_t * p01
    ap01 = cos_t * p01 - sin_t * p11
    ap10 = sin_t * p00 + cos_t * p01
    ap11 = sin_t * p01 + cos_t * p11
    
    # P_minus = (A * P) * A^T + Q analytical expansion
    p00_m = ap00 * cos_t - ap01 * sin_t + q_val
    p01_m = ap00 * sin_t + ap01 * cos_t
    p11_m = ap10 * sin_t + ap11 * cos_t + q_val  # Rectified mathematical formulation
    
    # Measurement Update (Correct)
    y = Y_filtered[i]
    innov_cov = p00_m + R_val
    
    # Kalman Gain Calculation
    k0 = p00_m / innov_cov
    k1 = p01_m / innov_cov
    
    v = y - x0_minus
    x0 = x0_minus + k0 * v
    x1 = x1_minus + k1 * v
    
    # Covariance Update: (Identity - K*H) * P_minus
    p00 = (1.0 - k0) * p00_m
    p01 = (1.0 - k0) * p01_m
    p10 = p01  # Hard enforcement of structural symmetry
    p11 = p11_m - k1 * p01_m
    
    # State Vector Energy Tracking
    X_intent_energy[i] = x0*x0 + x1*x1
