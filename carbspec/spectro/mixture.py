import numpy as np
import uncertainties as un
from uncertainties.unumpy import log10, nominal_values
from scipy.optimize import curve_fit
from .fitting import fit_spectrum, guess_p0
import matplotlib.pyplot as plt

from carbspec import dye as dyes

def make_mix_spectra(dye):
    """
    Returns a mix_spectra function incorporating the acid and base splines.

    Parameters
    ----------
    dye : str or dict
        Either the name of the dye you're using, or a dict containing 
        'acid' and 'base' entries with corresponding 
        scipy.interpolate.UnivariateSpline objects describing the molal 
        absorption spectrum of the acid form of the indicator dye across 
        the entire spectral range.

    Returns
    -------
    function : a mix_spectra function accepting the arguments (a, b, bkg, c, mc)
    """
    
    aspl, bspl = dyes.spline_handler(dye)

    def mix_spectra(x, a=1, b=1, bkg=0, c=0, m=1):
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

def unmix_spectra(wavelength, absorption, dye, sigma=None):
    """
    Determine the relative contribution of acid and base absorption to a measured spectrum.
    
    By fitting the mix_spectra function to measured data.

    Parameters
    ----------
    wavelength : array_like
        The wavelength of the spectrum
    absorption : array_like
        The absorption of the spectrum
    dye : str or dict
        Either the name of the dye you're using, or a dict containing 
        'acid' and 'base' entries with corresponding 
        scipy.interpolate.UnivariateSpline objects describing the molal 
        absorption spectrum of the acid form of the indicator dye across 
        the entire spectral range.
    weights : bool or array-like
        If True, fit is weighted by the 1/(S**2 + 1), where S is a spectrum at
        pKdye.
        If array-like, an array the same length as data to use as 
        weights (sigma: larger = less weight).

    Returns
    -------
    tuple : Containing the (a, b, bkg, c, m) terms of the mix_spectra function.
    """
    x = wavelength
    y = absorption

    aspl, bspl = dyes.spline_handler(dye)
    
    if sigma is None:
        sigma = np.array(1)
    
    # re-write this to allow parameter damping and prefer zeros?
    return fit_spectrum(x, y, aspl, bspl, sigma)



def pH_from_F(F, K):
    return -log10(K / F)

def pH_from_spectrum(wavelength, spectrum, dye='BPB', sigma=None, temp=25., sal=35., **kwargs):

    pe = un.correlated_values(*unmix_spectra(wavelength, spectrum, dye, sigma))
    
    F = pe[1] / pe[0]
    
    dyeK = dyes.K_handler(dye, temp=temp, sal=sal, **kwargs)
    
    return pH_from_F(F=F, K=dyeK)

def plot_mixture(wavelength, absorption, dye, p=None, sigma=None):
    x = wavelength
    y = absorption

    if p is None:
        p, _ = unmix_spectra(x, y, dye, sigma=sigma)
    
    fig = plt.figure(figsize=[6, 5])

    gs = plt.GridSpec(4, 1, fig)

    ax = fig.add_subplot(gs[:-1])
    rax = fig.add_subplot(gs[-1])

    ax.scatter(x, y, s=0.5, c='k', label='Measured')

    p = nominal_values(p)
    
    # plot mixed specturm
    mix_spectra = make_mix_spectra(dye)
    ax.plot(x, mix_spectra(x, *p), label='Model')

    # plot components
    aspl, bspl = dyes.spline_handler(dye)
    ax.axhline(p[2], c='k', ls='dashed', label='Baseline', lw=1)
    xn = p[-2] + x * p[-1]
    ax.plot(x, p[2] + aspl(xn) * p[0], c='b', ls='dashed', label='Acid', lw=1)
    ax.plot(x, p[2] + bspl(xn) * p[1], c='r', ls='dashed', label='Base', lw=1)

    ax.set_xticklabels([])

    ax.legend(scatterpoints=3)

    # plot residuals
    r = y - mix_spectra(x, *p)
    RSS = (r**2).sum()
    R2 = 1 - (RSS / ((y - y.mean())**2).sum())
    rax.scatter(x, r, s=0.5, c='k', alpha=0.2)
    rax.axhline(0, ls='dashed', c=(0,0,0,0.6))
    rax.text(.01, .005, f"RSS: {RSS:.2e}  |  $R^2$: {R2:.6f}", transform=rax.transAxes, ha='left', va='bottom')

    rmax = np.percentile(abs(r), 99)
    rax.set_ylim([- 3 * rmax, 3 * rmax])

    ax.set_ylabel('Absorption')

    rax.set_xlabel('Wavelength (nm)')
    rax.set_ylabel('Obs - Model')

    fig.tight_layout(h_pad=0.1)

    return fig, (ax, rax)

def spec_from_H(wv, H, dyeConc, dye, dyeK=None, temp=25, sal=35):

    aspl, bspl = dyes.spline_handler(dye)
    if dyeK is None and isinstance(dye, str):
        dyeK = dyes.K_handler(dye, temp, sal)

    a = dyeConc / (1 + dyeK / H)
    b = dyeConc / (1 + H / dyeK)
    
    return aspl(wv) * a + bspl(wv) * b

def spec_from_pH(wv, pH, dyeConc, dye, dyeK=None):
    return spec_from_H(wv, 10**-pH, dyeConc, dye, dyeK, temp=25, sal=35)