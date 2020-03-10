import numpy as np
import uncertainties as un
from uncertainties.unumpy import log10, nominal_values
from scipy.optimize import curve_fit
from .fitting import fit_spectrum

import matplotlib.pyplot as plt

from carbspec.dye.Ks import calc_KBPB, calc_KMCP

def make_mix_spectra(aspl, bspl):
    """
    Returns a mix_spectra function incorporating the acid and base splines.

    Parameters
    ----------
    aspl, bspl : scipy.interpolate.UnivariateSpline
        Spline objects for the acid and base molal absorption factors across
        the entire spectral range.

    Returns
    -------
    function : a mix_spectra function accepting the arguments (a, b, bkg, c, mc)
    """
    def mix_spectra(x, a=1, b=1, bkg=0, c=0, m=0):
        """
        Predict a spectrum as a mixture of end-member molal absorption factors.

        Equation: Abs = bkg + a * acid(xm) + b * base(xm)
        where xm = c + x * m

        Parameters
        ----------
        x : array_like
            Wavelength
        a : float
            acid coefficient
        b : float
            base coefficient
        bkg : float
            A constant background offset.
        c : float
            0th order wavelength adjustment.
        mc : float
            1st order wavelength adjustment.

        Returns
        -------
        array_like : predicted absorption spectrum.
        """
        xn = c + x * m
        return bkg + a * aspl(xn) + b * bspl(xn)

    return mix_spectra

def unmix_spectra(wavelength, absorption, aspl, bspl, sigma=None):
    """
    Determine the relative contribution of acid and base absorption to a measured spectrum.
    
    By fitting the mix_spectra function to measured data.

    Parameters
    ----------
    wavelength : array_like
        The wavelength of the spectrum
    absorption : array_like
        The absorption of the spectrum
    aspl : scipy.interpolate.UnivariateSpline
        A spline describing the molal absorption spectrum of the acid
        form of the indicator dye across the entire spectral range.
    bspl : scipy.interpolate.UnivariateSpline
        A spline describing the molal absorption spectrum of the base
        form of the indicator dye across the entire spectral range.
    weights : bool or array-like
        If True, fit is weighted by the 1/(S**2 + 1), where S is a spectrum at
        pKdye.
        If array-like, an array the same length as data to use as 
        weights (sigma: larger = less weight).

    Returns
    -------
    tuple : Containing the (a, b, bkg, c, mc) terms of the mix_spectra function.
    """
    x = wavelength
    y = absorption

    # mixture = make_mix_spectra(aspl, bspl)
    
    if sigma is None:
        sigma = np.array(1)
    
    # starting values for optimisation
    B0start = y[-1]  # background
    base_loc = np.argmax(bspl(x))  # wavelength of maximum base absorption
    bstart = max(y[base_loc] - B0start, 0) / bspl(x[base_loc])  # acid coefficient
    
    acid_loc = np.argmax(aspl(x))  # wavelength of maximum acid absorption
    astart = max(y[acid_loc] - B0start - bstart * bspl(x[acid_loc]), 0) / aspl(x[acid_loc])  # acid coefficient

    # re-write this to allow parameter damping and prefer zeros?
    return fit_spectrum(x, y, aspl, bspl, sigma, [astart, bstart, B0start, 0, 1])

def pH_from_F(F, K):
    return -log10(K / F)

def pH_from_mixed_spectrum(wavelength, spectrum, aspl, bspl, dye='BPB', sigma=None, temp=25., sal=35.):
    
    p, cov = unmix_spectra(wavelength, spectrum, aspl, bspl, sigma)
    pe = un.correlated_values(p, cov)
    
    F = pe[1] / pe[0]
    
    if dye == 'BPB':
        dyeK = calc_KBPB(sal, temp)
    elif dye == 'MCP':
        dyeK = calc_KMCP(temp, sal, 'dickson')
    else:
        raise ValueError(f'dye={dye} is not valid. Please enter BPB or MCP.')
    
    return pH_from_F(F, dyeK)

def plot_mixture(wavelength, absorption, aspl, bspl, p=None, sigma=None):
    x = wavelength
    y = absorption

    if p is None:
        p, _ = unmix_spectra(x, y, aspl, bspl, sigma=sigma)
    
    fig = plt.figure(figsize=[6, 5])

    gs = plt.GridSpec(4, 1, fig)

    ax = fig.add_subplot(gs[:-1])
    rax = fig.add_subplot(gs[-1])

    ax.scatter(x, y, s=0.5, c='k', label='Measured')

    p = nominal_values(p)
    
    mix_spectra = make_mix_spectra(aspl, bspl)

    ax.plot(x, mix_spectra(x, *p), label='Model')

    ax.axhline(p[2], c='k', ls='dashed', label='Baseline', lw=1)
    xn = p[-2] + x * p[-1]
    ax.plot(x, p[2] + aspl(xn) * p[0], c='b', ls='dashed', label='Acid', lw=1)
    ax.plot(x, p[2] + bspl(xn) * p[1], c='r', ls='dashed', label='Base', lw=1)

    ax.set_xticklabels([])

    ax.legend(scatterpoints=3)

    r = y - mix_spectra(x, *p)
    RSS = (r**2).sum()
    R2 = 1 - (RSS / ((y - y.mean())**2).sum())
    rax.scatter(x, r, s=0.5, c='k')
    rax.axhline(0, ls='dashed', c=(0,0,0,0.6))
    rax.text(.01, .05, f"RSS: {RSS:.2e}  |  $R^2$: {R2:.6f}", transform=rax.transAxes, ha='left', va='bottom')

    ax.set_ylabel('Absorption')

    rax.set_xlabel('Wavelength (nm)')
    rax.set_ylabel('Obs - Model')

    fig.tight_layout(h_pad=0.1)

    return fig, (ax, rax)

def spec_from_H(wv, H, dyeConc, dyeK, aspl, bspl):
    a = dyeConc / (1 + dyeK / H)
    b = dyeConc / (1 + H / dyeK)
    
    return aspl(wv) * a + bspl(wv) * b

def spec_from_pH(wv, pH, dyeConc, dyeK, aspl, bspl):
    return spec_from_H(wv, 10**-pH, dyeConc, dyeK, aspl, bspl)