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