import numpy as np

# from Galban et al, 2007
def thermal_noise(Abs, k1):
    return k1 * (1 + 10**(-2 * Abs))**0.5

def photon_noise(Abs, k2):
    return k2 * (10**-Abs + 10**(-2 * Abs))**0.5

def cell_position_noise(Abs, k3):
    return k3 * 10**-Abs

def combine_errors(Abs, *it):
    noise = np.zeros(Abs.size)
    for i in it:
        noise += (i / Abs)**2
    
    return Abs * noise**0.5

def rel_photometric_error(Abs, sT):
    return (0.434 / Abs) * (sT / 10 ** -Abs)

def calc_rel_photometric_error(Abs, k1=0, k2=0, k3=0):
    shot = thermal_noise(Abs, k1)
    photon = photon_noise(Abs, k2)
    cell = cell_position_noise(Abs, k3)
    
    noise = combine_errors(Abs, shot, photon, cell)
    
    return rel_photometric_error(Abs, noise)

def calc_photometric_error(Abs, k1=0, k2=0, k3=0):
    return Abs * calc_rel_photometric_error(Abs, k1=k1, k2=k2, k3=k3)