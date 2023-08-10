import numpy as np
import scipy.optimize as opt

from uncertainties import unumpy as unp
from .TA import TA_from_pH

def acid_zero(acid_str, crm_alk, pH, m0, m, sal, temp):
    TAs = TA_from_pH(pH, m0, m, sal, temp, acid_str) * 1e6
    return np.sum((unp.nominal_values(TAs - crm_alk)**2))

def calc_acid_strength(crm_alk, pH, m0, m, sal, temp):
    acid_fit = opt.minimize(acid_zero, 0.1, args=(crm_alk, pH, m0, m, sal, temp), method='Nelder-Mead')
    return acid_fit.x

def acid_drift(p, x, crm_alk, pH, m0, m, sal, temp):
    acid_str = np.polyval(p, x)
    TAs = TA_from_pH(pH, m0, m, sal, temp, acid_str) * 1e6
    return np.sum((unp.nominal_values(TAs - crm_alk)**2))

def calc_acid_strength_drift(x, crm_alk, pH, m0, m, sal, temp, order=1):
    p0 = [0] * (order - 1) + [0.1]
    acid_fit = opt.minimize(acid_zero, p0, args=(x, crm_alk, pH, m0, m, sal, temp), method='Nelder-Mead')
    return acid_fit.x