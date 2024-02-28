import numpy as np
import scipy.optimize as opt
from .species import calc_KF, calc_TF, calc_KS, calc_TS

def TA_from_pH(pH, m_sample, m_acid, sal, temp, C_acid):
    """
    Calculate alkalinity from titration end-point pH.

    Equation 6 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Parameters
    ----------
    pH : array_like
        End-point pH of acid addition to seawater on the Total scale.
    m_sample : array_like
        Mass of sample.
    m_acid : array_like
        Mass of acid added.
    sal : array_like
        Salinity of sample.
    temp : array_like
        Temperature of sample.
    C_acid : array_like
        Concentration of acid
    
    Returns
    -------
    array_like : Alkalinity in mol kg-1
    """
    H = 10**-pH

    TS = calc_TS(sal)
    TF = calc_TF(sal)

    KS = calc_KS(temp, sal)
    KF = calc_KF(temp, sal)
    
    Hfree = H / (1 + TS / KS)
    HSO4 = TS / (1 + KS / Hfree)
    HF = TF / (1 + KF / H)
    
    # TODO: Implement C_dye correction

    return (m_acid * C_acid - (m_sample + m_acid) * (Hfree + HSO4 + HF)) / m_sample

# calculate end pH for a given TA
def TA_diff(pH, TA, m_sample, m_acid, sal, temp, C_acid):
    return (TA_from_pH(pH, m_sample, m_acid, sal, temp, C_acid) - TA)**2

def pH_from_TA(TA, m_sample, m_acid, sal, temp, C_acid):
    pH = opt.newton(TA_diff, 3., args=(TA, m_sample, m_acid, sal, temp, C_acid))
    return pH

# calculate m_acid to reach specified end pH
def m_acid_diff(m_acid, pH, TA, m_sample, sal, temp, C_acid):
    return (TA_from_pH(pH=pH, m_sample=m_sample, m_acid=m_acid, sal=sal, temp=temp, C_acid=C_acid) - TA)**2

def calc_m_acid(pH, TA, m_sample, sal, temp, C_acid):
    m_acid = opt.newton(m_acid_diff, 1., args=(pH, TA, m_sample, sal, temp, C_acid))
    return m_acid