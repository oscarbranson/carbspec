import numpy as np

def calc_pH_Tris(sal, tempC):
    """
    Calculate the pH of tris buffered seawater at given temperature and salinity.

    Equation 6 from Liu et al (2011) dx.doi.org/10.1021/es200665d
    """
    tempK = 273.15 + tempC
    return ((11911.08 - 18.2499 * sal - 0.039336 * sal**2) / tempK - 
             366.27059 + 0.53993607 * sal + 0.00016329 * sal**2 + 
             (64.52243 - 0.084041 * sal) * np.log(tempK) - 0.11149858 * tempK)