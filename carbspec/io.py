import os
import numpy as np
from glob import glob

def load_spectrum(file, low=400, high=700, colname_row=0, colname_sep='\t'):
    with open(file, 'r') as f:
        lines = f.readlines(colname_row + 1)
    cols = lines[colname_row].strip().split(colname_sep)

    dat = np.genfromtxt(file, skip_header=1).T
    
    return {k: v for k, v in zip(cols, dat[:, (dat[0] >= low) & (dat[0] <= high)])}

def load_spectra(folder, extension='.dat', low=400, high=700, colname_row=0, colname_sep='\t'):
    fs = glob(f'{folder}*{extension}')

    spec = {}
    for f in fs:
        fn = os.path.splitext(os.path.split(f)[-1])[0]
        spec[fn] = load_spectrum(f, low=low, high=high, colname_row=colname_row, colname_sep=colname_sep)
    
    return spec