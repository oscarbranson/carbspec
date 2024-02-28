import numpy as np
import uncertainties as un
import uncertainties.unumpy as unp

def calc_pKBPB(sal):
    """
    Calculate pKa of dye at sample salinity.

    Eq 17 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Form:
    
    pKa = pKa(sal=35) + A (35 - sal)

    A = 1.74e-3 +/- 0.8e-4

    Parameters
    ----------
    sal : array_like
        Salinity in PSU

    Returns
    -------
    array_like : pKa of dye at specified salinity
    """
    pKa35 = 3.515654103
    # A = un.ufloat(1.74e-3, 0.8e-4)
    A = 1.74e-3

    return pKa35 + A * (35.0 - sal)

def calc_pKBPB_Cam1(sal):
    """
    Calculate pKa of dye at sample salinity.

    Eq 17 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Form:
    pKa = pKa(s=35) + A (35 - sal)

    A = 1.74e-3 +/- 0.8e-4

    Parameters
    ----------
    sal : array_like
        Salinity in PSU

    Returns
    -------
    array_like : pKa of dye at specified salinity
    """
    pKa35 = 3.631498503311959
    # A = un.ufloat(1.74e-3, 0.8e-4)
    A = 1.74e-3

    return pKa35 + A * (35.0 - sal)

def temp_corr_KBPB(temp):
    C1, C2 = [-2.56020702e-06,  1.00921921e-07]
    return C1 * temp + C2 * temp**2

def temp_corr_KBPB_new(temp=25.):
    # calculated from R25 = RT * (1 + 6.774e-3 * (25. - T)) of Nand & Ellwood (2018, doi:10.1002/lom3.10253)
    
    # since pH = pK + log10((R - e1) / (e2 - R * e3)),
    # K = H * (R - e1) / (e2 - R * e3)
    # We want the correction factor KT / K25, which is:
    # KT_K25 = ((RT - e1) / (e2 - RT * e3)) / ((R25 - e1) / (e2 - R25 * e3))
    # from this, we calculate KT_K25 at a nominal R, fit it as a function of T
    # using a second order polynomial.
    
    p = [4.67075747e-05, 7.02630945e-03, 1.00006993e+00]
    
    return np.polyval(p, temp-25.)

def calc_KBPB(temp=25, sal=35):
    """
    Calculate K of dye at sample salinity and temperature.

    Eq 17 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Form:
    pKa = pKa(sal=35) + A (35 - sal)
    K = 10**-pKa + C1 * temp + C2 * temp**2

    A = 1.74e-3 +/- 0.8e-4
    C1 = -2.56020702e-06
    C2 = 1.00921921e-07

    Parameters
    ----------
    temp : array-like
        temperature in C
    sal : array_like
        Salinity in PSU

    Returns
    -------
    array_like : pKa of dye at specified salinity and temperature
    """
    return 10**-calc_pKBPB(sal) + temp_corr_KBPB(temp)

def calc_KBPB_Cam1(temp=25, sal=35):
    """
    Calculate K of dye at sample salinity and temperature.

    Calculated by minimising the standard deviation of repeat TA measurements of BPB_Cam1 dye.

    Form:
    pKa = pKa(t=35) + A (35 - sal)

    A = 1.74e-3 +/- 0.8e-4

    Parameters
    ----------
    temp : array-like
        temperature in C
    sal : array_like
        Salinity in PSU

    Returns
    -------
    array_like : pKa of dye at specified salinity and temperature
    """
    return 10**-calc_pKBPB_Cam1(sal) + temp_corr_KBPB(temp)

# MCP
def calc_KMCP(temp=25, sal=35, mode='dickson'):
    """
    K2 of MCP dye.

    Either calculated using equation 8 of SOP 6b in Dickson, 
    Sabine & Christian (2007, ISBN:1-897176-07-4), or calculated
    using in-house measurements of Tris-buffered artificial seawater. 

    Parameters
    ----------
    temp : array_like
        Temperature in Celcius
    sal : array_like
        Salinity
    mode : str
        'dickson' or 'tris'

    Returns
    -------
    array_like : K2 of MCP dye
    """
    if mode == 'tris':
        p = un.correlated_values([ 8.81873900e-12, -5.00996717e-11,  5.95759909e-09],
                                 [[ 5.72672924e-24, -2.56643258e-22,  2.80811298e-21],
                                  [-2.56643258e-22,  1.15587639e-20, -1.27159130e-19],
                                  [ 2.80811298e-21, -1.27159130e-19,  1.40773494e-18]])
        return np.polyval(p, temp)
    elif mode == 'dickson':
        tempK = temp + 273.15
        pK = 1245.69 / tempK + 3.8275 + 0.00211 * (35 - sal)
        return 10**-pK
    else:
        raise ValueError('Please specify `mode` as `tris` or `dickson`')

Kdict = {
    'MCP': calc_KMCP,
    'MCP_Cam1': calc_KMCP,
    'BPB': calc_KBPB,
    'BPB_Cam1': calc_KBPB_Cam1
    }

def K_handler(dye, temp, sal, **kwargs):
    if dye not in Kdict:
        ValueError(f'dye={dye} is not valid. Please enter one of [' + ', '.join([Kdict.keys()]) + '].')
    return Kdict[dye](temp=temp, sal=sal, **kwargs)
