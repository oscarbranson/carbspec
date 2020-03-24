import numpy as np

# F
def calc_TF(Sal):
    """
    Calculate total Fluorine

    Riley, J. P., Deep-Sea Research 12:219-220, 1965:
    this is .000068.*Sali./35. = .00000195.*Sali
    """
    a, b, c = (0.000067, 18.998, 1.80655)
    return (a / b) * (Sal / c)  # mol/kg-SW

def calc_KF(TempC, Sal):
    """
    Calculate equilibrium constants for HF on Total pH scale.

    Dickson, Sabine and Christian, 2007

    Parameters
    ----------
    TempC : array-like
        Temperature in Celcius.
    Sal : array-like
        Salinity in PSU

    Returns
    -------
    array_like : KF on Total scale
    """
    TempK = TempC + 273.15

    a, b, c, = (874.0, -9.68, 0.111)

    return np.exp(a / TempK + b + c * Sal**0.5)

# S
def calc_TS(Sal):
    """
    Calculate total Sulphur

    Morris, A. W., and Riley, J. P., Deep-Sea Research 13:699-705, 1966:
    this is .02824.*Sali./35. = .0008067.*Sali
    """
    a, b, c = (0.14, 96.062, 1.80655)
    return (a / b) * (Sal / c)  # mol/kg-SW

def calc_KS(TempC, Sal):
    """
    Calculate equilibrium constants for HSO4 on Free pH scale.

    Dickson, Sabine and Christian, 2007

    Parameters
    ----------
    TempC : array-like
        Temperature in Celcius.
    Sal : array-like
        Salinity in PSU

    Returns
    -------
    array_like : KF
    """
    T = TempC + 273.15
    Istr = 19.924 * Sal / (1000 - 1.005 * Sal)

    param = np.array([141.328, -4276.1, -23.093, 324.57,
                                -13856, -47.986, -771.54, 35474,
                                114.723, -2698, 1776])  # Dickson 1990

    return np.exp(param[0] +
                  param[1] / T +
                  param[2] * np.log(T) + np.sqrt(Istr) *
                  (param[3] +
                  param[4] / T +
                  param[5] * np.log(T)) + Istr *
                  (param[6] +
                  param[7] / T +
                  param[8] * np.log(T)) +
                  param[9] / T * Istr * np.sqrt(Istr) +
                  param[10] / T * Istr**2 + np.log(1 - 0.001005 * Sal))

# B
def calc_TB(Sal):
    """
    Calculate total Boron
    
    Directly from CO2SYS:
    Uppstrom, L., Deep-Sea Research 21:161-162, 1974:
    this is 0.000416 * Sal/35. = 0.0000119 * Sal
    TB(FF) = (0.000232 / 10.811) * (Sal / 1.80655) in mol/kg-SW
    """
    a, b = (0.0004157, 35.)
    return a * Sal / b
    
def calc_KB(TempC, Sal):
    """
    Calculate KB

    From Dickson et al (1990b)
    """
    TempK = TempC + 273.15
    sqrtSal = Sal**0.5
    param = [
        -8966.90, 
        2890.53,
        77.942,
        1.728,
        0.0996,
        148.0248,
        137.1942,
        1.62142,
        -24.4344,
        25.085,
        0.2474,
        0.053105
        ]
        
    return np.exp((param[0] - param[1] * sqrtSal - param[2] * Sal +
                   param[3] * Sal * sqrtSal - param[4] * Sal * Sal) / TempK + 
                  (param[5] + param[6] * sqrtSal + param[7] * Sal) +
                  (param[8] - param[9] * sqrtSal - param[10] * Sal) * np.log(TempK) +
                  param[11] * sqrtSal * TempK)