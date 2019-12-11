import numpy as np
import uncertainties as un
from uncertainties.unumpy import log10, nominal_values
from scipy.optimize import curve_fit

import matplotlib.pyplot as plt

from carbspec.dye import calc_KBPB, calc_KMCP

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
    function : a mix_spectra function accepting the arguments (a, b, bkg, C0, C1)
    """
    def mix_spectra(x, a=1, b=1, bkg=0, C0=0, C1=1):
        """
        Predict a spectrum as a mixture of end-member molal absorption factors.

        Equation: Abs = bkg + a * acid(xm) + b * base(xm)
        where xm = C0 + x * C1

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
        C0 : float
            0th order wavelength adjustment.
        C1 : float
            1st order wavelength adjustment.

        Returns
        -------
        array_like : predicted absorption spectrum.
        """
        xn = C0 + x * C1
        return bkg + a * aspl(xn) + b * bspl(xn)

    return mix_spectra

def unmix_spectra(wavelength, absorption, aspl, bspl, weights=False):
    """
    Determine the relative contribution of acid and base absorption to a measured spectrum.
    
    By fitting the mix_spectra function to measured data.

    Parameters
    ----------
    wavelength : array_like
        The wavelength of the spectrum
    absorption : array_like
        The absorption of the spectru
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
    tuple : Containing the (a, b, bkg, C0, C1) terms of the mix_spectra function.
    """
    x = wavelength
    y = absorption

    mixture = make_mix_spectra(aspl, bspl)
    
    if isinstance(weights, bool):
        if weights:
            w = 1 / (mixture(x)**2 + 1)
        else:
            w = None
    else:
        w = weights
    
    # identify starting values for optimisation
    base_loc = x[bspl(x) == max(bspl(x))]
    acid_loc = x[aspl(x) == max(aspl(x))]
    
    bstart = max([float(y[abs(x - base_loc) == min(abs(x - base_loc))] / bspl(base_loc)), 0])
    astart = max([float(y[abs(x - acid_loc) == min(abs(x - acid_loc))] / aspl(acid_loc)), 0])
    # bstart = float(y[abs(x - base_loc) == min(abs(x - base_loc))] / bspl(base_loc))
    # astart = float(y[abs(x - acid_loc) == min(abs(x - acid_loc))] / aspl(acid_loc))
    
    # should really re-write this to allow parameter damping and prefer zeros
    return curve_fit(mixture, x, y, p0=(astart, bstart, 0, 0, 1),
                    sigma=w,
                    bounds=((0, 0, -0.1, -0.05, 0.95), 
                            (np.inf, np.inf, 0.1, 0.05, 1.05)))

def pH_from_F(F, K):
    return -log10(K / F)

def pH_from_mixed_spectrum(wavelength, spectrum, aspl, bspl, dye='BPB', temp=25., sal=35.):
    
    p, cov = unmix_spectra(wavelength, spectrum, aspl, bspl)
    pe = un.correlated_values(p, cov)
    
    F = pe[1] / pe[0]
    
    if dye == 'BPB':
        dyeK = calc_KBPB(sal, temp)
    elif dye == 'MCP':
        dyeK = calc_KMCP(temp, sal, 'dickson')
    else:
        raise ValueError(f'dye={dye} is not valid. Please enter BPB or MCP.')
    
    return pH_from_F(F, dyeK)

def plot_mixture(wavelength, absorption, p, aspl, bspl):
    x = wavelength
    y = absorption
    
    
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

    rax.scatter(x, y - mix_spectra(x, *p), s=0.5, c='k')
    rax.axhline(0, ls='dashed', c=(0,0,0,0.6))

    ax.set_ylabel('Absorption')

    rax.set_xlabel('Wavelength (nm)')
    rax.set_ylabel('Obs - Model')

    fig.tight_layout(h_pad=0.1)

    return fig, (ax, rax)