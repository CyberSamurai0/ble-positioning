class Kalman1D:
    def __init__(self, q=0.01, r=1.0, initial_value=None):
        self.q = q          # Process noise
        self.r = r          # Measurement noise
        self.x = initial_value  # State estimate
        self.p = 1.0        # Estimate uncertainty

    def update(self, measurement):
        if self.x is None:
            self.x = measurement
            return self.x

        # Prediction step
        p_pred = self.p + self.q

        # Kalman gain
        k = p_pred / (p_pred + self.r)

        # Update step
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * p_pred

        return self.x