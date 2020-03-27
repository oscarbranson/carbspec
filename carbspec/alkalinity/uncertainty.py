import numpy as np
from .species import calc_KF, calc_KS, calc_TF, calc_TS

# uncertainty functions
def dTA_dm(C, m0, H, temp, sal):
    KF = calc_KF(temp, sal)
    KS = calc_KS(temp, sal)
    TF = calc_TF(sal)
    TS = calc_TS(sal)
    
    F = TF / (1 + KF / H) + TS / (KS * H * (1 + TS / KS) + 1) + H / (1 + TS / KS) 
    
    return C / m0 - F / m0

def dTA_dm0(m0, H, m, C, temp, sal):
    KF = calc_KF(temp, sal)
    KS = calc_KS(temp, sal)
    TF = calc_TF(sal)
    TS = calc_TS(sal)
    
    F = TF / (1 + KF / H) + TS / (KS * H * (1 + TS / KS) + 1) + H / (1 + TS / KS)
    
    return - C * m / m0**2 - F / m0 + (m + m0) * F / m0**2

def dTA_dH(H, m, m0, sal, temp):
    KF = calc_KF(temp, sal)
    KS = calc_KS(temp, sal)
    TF = calc_TF(sal)
    TS = calc_TS(sal)
    
    F = (TF * KF / (H**2 * (1 + KF / H)**2)) - ((KS * TS * (1 + TS / KS)) / (KS * H * (1 + TS / KS) + 1)**2) + (1 / (1 + TS / KS))
    
    return (m + m0) * F / m0

def dTA_dpH(pH, m, m0, sal, temp):
    KF = calc_KF(temp, sal)
    KS = calc_KS(temp, sal)
    TF = calc_TF(sal)
    TS = calc_TS(sal)
    H = 10**-pH
    
    F = ((H * KS * TS * (1 + TS / KS) * np.log(10)) / (1 + H * KS * (1 + TS / KS))**2) - (10**pH * TF * KF * np.log(10) / (1 + 10**pH * KF)**2) - ((H * np.log(10)) / (1 + TS / KS))
    
    return - (m + m0) * F / m0

def dTA_dC(m, m0):
    return m / m0