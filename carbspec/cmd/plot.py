import matplotlib.pyplot as plt
from carbspec.spectro.mixture import make_mix_components, make_mix_spectra

from uncertainties.unumpy import nominal_values

def plot_spectrum(spectrum, fit_p=None, include=['absorbance', 'residuals', 'dark corrected', 'scale factor', 'raw']):
    if isinstance(include, str):
        include = [include]
    
    heights = {
        'raw': 1,
        'scale factor': 0.5,
        'dark corrected': 1, 
        'absorbance': 1,
        'residuals': 0.5,
    }
    
    height_ratios = [heights[k] for k in include]
    
    fig, axs = plt.subplots(len(include), 1, figsize=(5, 0.5 + 1.5 * len(include)), constrained_layout=True, sharex=True, height_ratios=height_ratios)

    if len(include) == 1:
        axs = [axs]
    
    wv = spectrum.wv
    
    for i, var in enumerate(include):
        match var:
            case 'raw':
                axs[i].plot(wv, spectrum.dark, label='dark', color='grey')
                if spectrum.light_reference is not None:
                    axs[i].plot(wv, spectrum.light_reference_raw, label='reference', color='C0')
                if spectrum.light_sample is not None:
                    axs[i].plot(wv, spectrum.light_sample_raw, label='sample', color='C1')
                axs[i].set_ylabel('raw counts')
            case 'scale factor':
                axs[i].plot(wv, spectrum.scale_factor, label='scale factor', color='C3')
            case 'dark corrected':
                axs[i].plot(wv, spectrum.light_reference, label='reference', color='C0')
                axs[i].plot(wv, spectrum.light_sample, label='sample', color='C1')
                axs[i].set_ylabel('counts - dark')
            case 'absorbance':
                axs[i].scatter(wv, spectrum.absorbance, label='sample', color='k', s=1)
                
                if fit_p is not None:
                    spec_fn = make_mix_spectra(spectrum.splines)
                    spec_components = make_mix_components(spectrum.splines)
                    pred = spec_fn(wv, *nominal_values(fit_p))
                    _, acid, base = spec_components(wv, *nominal_values(fit_p))
                    axs[i].plot(wv, pred, color='r', lw=1, label='fit')
                    axs[i].fill_between(wv, 0, acid, alpha=0.2, label='acid')
                    axs[i].fill_between(wv, 0, base, alpha=0.2, label='base')
                
                axs[i].set_ylabel('absorbance')
            case 'residuals':
                if fit_p is not None:
                    spec_fn = make_mix_spectra(spectrum.splines)
                    pred = spec_fn(wv, *nominal_values(fit_p))
                    resid = spectrum.absorbance - pred
                    
                    axs[i].scatter(wv, resid, label='residuals', color='k', s=1)
                    axs[i].axhline(0, color=(0,0,0,0.6), lw=0.5)


    axs[-1].set_xlim(min(wv), max(wv))
    axs[-1].set_xlabel('wavelength (nm)')

    title = ''
    if spectrum.sample is not None:
        title += spectrum.sample
    
    # if spectrum.pH is not None:
    #     title += f" : {spectrum.pH:.4f}"
        
    axs[0].set_title(title, fontsize=8, loc='left')

    for ax in axs:
        ax.legend(fontsize=8, bbox_to_anchor=(1, 1), loc='upper left')
        
    return fig, axs