import numpy as np

def load_spectrum(file, low=400, high=700, colname_row=0, colname_sep='\t'):
    with open(file, 'r') as f:
        lines = f.readlines(colname_row + 1)
    cols = lines[colname_row].strip().split(colname_sep)

    dat = np.genfromtxt(file, skip_header=1).T
    
    return {k: v for k, v in zip(cols, dat[:, (dat[0] >= low) & (dat[0] <= high)])}

