import numpy as np
import uncertainties as un
import uncertainties.unumpy as unp

def calc_pKBPB(sal):
    """
    Calculate pKa of dye at sample salinity.

    Eq 17 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Form:
    pKa = pKa(t=35) + A (35 - sal)

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

def temp_corr_KBPB(temp):
    C1, C2 = [-2.56020702e-06,  1.00921921e-07]
    return C1 * temp + C2 * temp**2

def calc_KBPB(temp=25, sal=35):
    """
    Calculate pKa of dye at sample salinity.

    Eq 17 of Nand & Ellwood (2018, doi:10.1002/lom3.10253)

    Form:
    pKa = pKa(t=35) + A (35 - sal)

    A = 1.74e-3 +/- 0.8e-4

    Parameters
    ----------
    sal : array_like
        Salinity in PSU

    Returns
    -------
    array_like : pKa of dye at specified salinity
    """
    return 10**-calc_pKBPB(sal) + temp_corr_KBPB(temp)

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

Kdict = {'MCP': calc_KMCP,
         'BPB': calc_KBPB}

def K_handler(dye, temp, sal, **kwargs):
    if dye not in Kdict:
        ValueError(f'dye={dye} is not valid. Please enter one of [' + ', '.join([Kdict.keys()]) + '].')
    return Kdict[dye](temp=temp, sal=sal, **kwargs)
