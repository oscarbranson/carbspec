import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import uncertainties as un
import uncertainties.unumpy as unp

from carbspec.dye.Ks import calc_pKBPB

def smooth(a, win=21):
    """
    Calculate a running mean and stderr of an array.

    Parameters
    ----------
    a : array_like
        The array to smooth.
    win : int
        The size of the smoothing window (number of points)
l
    Returns
    -------
    (array_like, array_like) : tuple of (mean, stderr) of the smoothed array.
    """
    if win % 2 == 0:
        win += 1
        
    pad = [np.nan] * (win // 2)

    shape = a.shape[:-1] + (a.shape[-1] - win + 1, win)
    strides = a.strides + (a.strides[-1], )
    strided = np.lib.stride_tricks.as_strided(a, shape, strides)
    sm = np.apply_along_axis(np.nanmean, 1, strided)
    
    resid = strided - sm[:, np.newaxis]
    stderr = np.apply_along_axis(np.nanstd, 1, resid) / np.sqrt(win)
        
    return np.concatenate([pad, sm, pad]), np.concatenate([pad, stderr, pad])

def peak_ID(dat, acid_loc, base_loc, bkg_loc, peak_win=30, smooth_win=21):
    """
    Identify the absorption, standard error and location of peaks in a spectrum.

    Parameters
    ----------
    dat : dict
        A dictionary containing 'wavelength' and 'Abs' items.
    acid_loc, base_loc, bkg_loc : float
        The approximate locations of the acid, base and background peaks.
    peak_win : int
        The window either side of the acid and base peaks that is examined
        when identifying peak maxima.
    smooth_win : int
        The width of the smoothing window applied to the spectra.

    Returns
    -------
    tuple : containing (absorption, stderr, location) of the acid, base, bkg locations. 
    """
    # smooth spectra
    dat['sm_spec'], dat['se_spec'] = smooth(dat['Abs'], smooth_win)
        
    # acid peak
    aind = (dat['wavelength'] >= acid_loc - peak_win) & (dat['wavelength'] <= acid_loc + peak_win)
    aind[aind] = dat['sm_spec'][aind] == np.nanmax(dat['sm_spec'][aind])
    if abs(dat['wavelength'][aind][0] - acid_loc) >= 0.95 * peak_win:
        aind = abs(dat['wavelength'] - acid_loc) == min(abs(dat['wavelength'] - acid_loc))
    acid_loc = dat['wavelength'][aind][0]
    acid_abs = dat['sm_spec'][aind][0]
    acid_se = dat['se_spec'][aind][0]
    
    # base peak
    bind = (dat['wavelength'] >= base_loc - peak_win) & (dat['wavelength'] <= base_loc + peak_win)
    bind[bind] = dat['sm_spec'][bind] == np.nanmax(dat['sm_spec'][bind])
    if abs(dat['wavelength'][bind][0] - base_loc) >= 0.95 * peak_win:
        aind = abs(dat['wavelength'] - base_loc) == min(abs(dat['wavelength'] - base_loc))
    base_loc = dat['wavelength'][bind][0]
    base_abs = dat['sm_spec'][bind][0]
    base_se = dat['se_spec'][bind][0]
    
    # background
    bkg_ind = abs(dat['wavelength'] - bkg_loc) == np.nanmin(abs(dat['wavelength'] - bkg_loc))
    bgk_loc = dat['wavelength'][bkg_ind][0]
    bkg_abs = dat['sm_spec'][bkg_ind][0]
    bkg_se = dat['se_spec'][bkg_ind][0]
    
    return ((acid_abs, acid_se, acid_loc), (base_abs, base_se, base_loc), (bkg_abs, bkg_se, bkg_loc))

def calc_R_from_peaks(peaks):
    acid, base, bkg = peaks
    
    uacid = un.ufloat(float(acid[0]), float(acid[1]))
    ubase = un.ufloat(float(base[0]), float(base[1]))
    ubkg = un.ufloat(float(bkg[0]), float(bkg[1]))
    
    return (ubase - ubkg) / (uacid - ubkg)

def calc_R25(R, temp):
    """
    Adjust measured BPB absorption ratio for temperature.

    Eq 16 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Form:
    R25 = R * (1 + A * (25 - temp))

    A = 6.774e-3 +/- 0.9e-5

    Parameters
    ----------
    R : array_like
        Measured Base/Acid absorption ratio.
    temp : array_like
        Temperature of measurement (C)

    Returns
    -------
    array_like : Temperature corrected absorption
    """

    # A = un.ufloat(6.774e-3, 0.9e-5)
    A = 6.774e-3

    return R * (1 + (A * (25 - temp)))

def pH_from_R(R, temp, sal):
    """
    Calculate pH from Base/Acid absorption ratio, at known temperature and salinity.

    Equation 11 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Form:

    pH = pK + log10((R - e1) / (e2 - R * e3))

    Parameters
    ----------
    R : array_like
        Measured Base/Acid absorption ratio.
    temp : array_like
        Temperature of measurement (C)
    sal : array_like
        Salinity in PSU
    
    Returns
    -------
    array_like : Solution pH (Total Scale)
    """

    e1 = 5.3259624e-3
    e2 = 2.2319033
    e3 = 3.19e-2

    pKa = calc_pKBPB(sal)
    R25 = calc_R25(R, temp)

    return pKa + unp.log10((R25 - e1) / (e2 - R25 * e3))


# Plotting

def plot_peaks(dat, acid, base, bkg, win=15):
    acid_abs, acid_se, acid_loc = acid
    base_abs, base_se, base_loc = base
    bkg_abs, bkg_se, bkg_loc = bkg
    
    fig = plt.figure(figsize=[10,7])

    fax = fig.add_subplot(2,1,1)
    fax.scatter(dat['wavelength'], dat['Abs'], s=0.5, label='raw')
    fax.plot(dat['wavelength'], dat['sm_spec'], c='C1', label='smoothed')

    aax = fig.add_subplot(2,3,4)
    bax = fig.add_subplot(2,3,5)
    bkx = fig.add_subplot(2,3,6)

    # acid peak
    aind = (dat['wavelength'] >= acid_loc - win) & (dat['wavelength'] <= acid_loc + win)
    aax.scatter(dat['wavelength'][aind], dat['Abs'][aind], s=0.5)
    aax.plot(dat['wavelength'][aind], dat['sm_spec'][aind], c='C1')
    aax.fill_between(dat['wavelength'][aind], 
                     dat['sm_spec'][aind] - dat['se_spec'][aind], 
                     dat['sm_spec'][aind] + dat['se_spec'][aind], 
                     color='C1', alpha=0.2)
    aax.set_xlim(acid_loc - win, acid_loc + win)

    # base peak
    bind = (dat['wavelength'] >= base_loc - win) & (dat['wavelength'] <= base_loc + win)
    bax.scatter(dat['wavelength'][bind], dat['Abs'][bind], s=0.5)
    bax.plot(dat['wavelength'][bind], dat['sm_spec'][bind], c='C1')
    bax.fill_between(dat['wavelength'][bind], 
                     dat['sm_spec'][bind] - dat['se_spec'][bind], 
                     dat['sm_spec'][bind] + dat['se_spec'][bind], 
                     color='C1', alpha=0.2)
    bax.set_xlim(base_loc - win, base_loc + win)
    
    bkind = (dat['wavelength'] >= bkg_loc - win) & (dat['wavelength'] <= bkg_loc + win)
    bkx.scatter(dat['wavelength'][bkind], dat['Abs'][bkind], s=0.5)
    bkx.plot(dat['wavelength'][bkind], dat['sm_spec'][bkind], c='C1')
    bkx.fill_between(dat['wavelength'][bkind], 
                     dat['sm_spec'][bkind] - dat['se_spec'][bkind], 
                     dat['sm_spec'][bkind] + dat['se_spec'][bkind], 
                     color='C1', alpha=0.2)
    bkx.set_xlim(bkg_loc - win, bkg_loc + win)
    
    
    # background
    bkgind = (dat['wavelength'] >= bkg_loc - win) & (dat['wavelength'] <= bkg_loc + win)
    
    for ax in [fax, aax]:
        ax.axvline(acid_loc, c='C2', label='acid peak')
        ax.axhline(acid_abs, c='C2', label='_')

    for ax in [fax, bax]:
        ax.axvline(base_loc, c='C3', label='base peak')
        ax.axhline(base_abs, c='C3', label='_')
        
    for ax in [fax, bkx]:
        ax.axvline(bkg_loc, c='C4', label='baseline')
        ax.axhline(bkg_abs, c='C4', label='_')

    fax.legend(scatterpoints=3)
    
    fig.tight_layout()
    
    return fig, (fax, aax, bax, bkx)


## MCP functions
# from http://www.doi.org/10.1038/s41598-017-02624-0

def logk2e2(TK, S):
    a = -319.8369 + 0.688159 * S - 0.00018374 * S**2
    b = 10508.724 - 32.9599 * S + 0.059082 * S**2
    c = 55.54253 - 0.101639 * S
    d = -0.08112151
    return (a + b / TK + c * np.log(TK) + d * TK)

def e1(TK):
    return -0.004363 + 3.598e-5 * TK

def e3_e2(TK, S):
    return - 0.016224 + 2.42851e-4 * TK + 5.05663e-5 * (S - 35)

def pH_MCP(R, T, S):
    TK = T + 273.15
    
    return logk2e2(TK, S) + unp.log10((R - e1(TK)) / (1 - R * e3_e2(TK, S)))
