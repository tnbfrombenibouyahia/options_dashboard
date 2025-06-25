from scipy.stats import norm
from math import log, sqrt

def compute_delta(S, K, T, r, sigma, option_type='call'):
    if sigma <= 0 or T <= 0 or S <= 0 or K <= 0:
        return 0.0

    try:
        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        if option_type == 'call':
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1
    except:
        return 0.0