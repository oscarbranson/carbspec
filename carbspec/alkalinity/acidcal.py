import numpy as np
import scipy.optimize as opt

from uncertainties import unumpy as unp
from .TA import TA_from_pH

def acid_zero(acid_str, crm_alk, pH, m0, m, sal, temp):
    """A helper function for calculating acid strength.

    Parameters
    ----------
    acid_str : float
        The strength of the acid in mol kg-1.
    crm_alk : float
        The Total Alkalinity of the CRM in umol kg-1.
    pH : float
        The measured pH of the sample.
    m0 : float
        The mass of the sample in g.
    m : float
        The mass of acid added in g.
    sal : float
        The salinity of the sample in PSU.
    temp : float
        The temperature at which the measurement was made in deg C.

    Returns
    -------
    float
        The squared difference between calculated alkalinity and CRM alkalinity.
    """
    TAs = TA_from_pH(pH, m0, m, sal, temp, acid_str) * 1e6
    return np.sum((unp.nominal_values(TAs - crm_alk)**2))

def calc_acid_strength(crm_alk, pH, m0, m, sal, temp):
    """Calculate acid strength from CRM alkalinity and titration pH.

    Parameters
    ----------
    crm_alk : float
        The Total Alkalinity of the CRM in umol kg-1.
    pH : float
        The measured pH of the sample.
    m0 : float
        The mass of the sample in g.
    m : float
        The mass of acid added in g.
    sal : float
        The salinity of the sample in PSU.
    temp : float
        The temperature at which the measurement was made in deg C.

    Returns
    -------
    float
        The strength of the acid in mol kg-1.
    """
    acid_fit = opt.minimize(acid_zero, 0.1, args=(crm_alk, pH, m0, m, sal, temp), method='Nelder-Mead')
    return acid_fit.x[0]

def acid_drift(p, x, crm_alk, pH, m0, m, sal, temp):
    acid_str = np.polyval(p, x)
    TAs = TA_from_pH(pH, m0, m, sal, temp, acid_str) * 1e6
    return np.sum((unp.nominal_values(TAs - crm_alk)**2))

def calc_acid_strength_drift(x, crm_alk, pH, m0, m, sal, temp, order=1):
    """A function for calculating the drift of acid strength over time.

    Parameters
    ----------
    x : array-like
        The x-axis value for the drift correction. Usually time in plain float format (e.g. decimal minutes).
    crm_alk : float
        The Total Alkalinity of the CRM in umol kg-1.
    pH : array-like
        The measured pH of the samples. Must be the same length as `x`.
    m0 : array-like
        The mass of the samples in g. Must be the same length as `x`.
    m : array-like
        The mass of acid added to the samples in g. Must be the same length as `x`.
    sal : array-like
        The salinity of the samples. Must be the same length as `x`.
    temp : array-like
        The temperature at which the measurements were made. Must be the same length as `x`.
    order : int, optional
        The degree of polynomial to use for the drift correction, by default 1

    Returns
    -------
    array-like
        Containing the coefficients of the polynomial fit to the drift correction in order 
        of decreasing degree (np.polyval order).
    """
    p0 = [0] * (order - 1) + [0.1]
    acid_fit = opt.minimize(acid_zero, p0, args=(x, crm_alk, pH, m0, m, sal, temp), method='Nelder-Mead')
    return acid_fit.x