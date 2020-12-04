<div align="right">
  <a href="https://zenodo.org/badge/latestdoi/227447816"><img src="https://zenodo.org/badge/227447816.svg" alt="DOI" height="18"></a>
  <a href="https://badge.fury.io/py/carbspec"><img src="https://badge.fury.io/py/carbspec.svg" alt="PyPI version" height="18"></a>
</div>

# ``carbspec`` : pH and Alkalinity Determination by Spectral Fitting

## Submitted Manuscript
> High-Precision characterisation of indicator dyes by Spectral Fitting: Application to Swawater pH and Alkalinity measurements. Branson, O. & Ellwood, M. *L&O Methods* 

Electronic supplements are available in the [**SI Folder**](SI/).

## Installation

pip install  carbspec

## Example Usage

```python
from carbspec.io import load_spectrum  # for reading files
from carbspec import spectro  # for doing the work

spec = load_spectrum('./SI/data/pH/CRM1_DICKSON_D10_CRM_100211_03_12_2019.dat')  # this data file is in the 'SI' folder of the reposiitory.
# NB Yo don't have to use 'load_spectrum' - the following function just requires two arrays containing wavelength and absorption.

spectro.pH_from_spectrum(s['wavelength'], s['Abs'])

> 3.570124144350996+/-0.006193756635537494
```

Further examples of pH and TA calculation on batches of files may be found in the [Figures](https://nbviewer.jupyter.org/github/oscarbranson/carbspec/blob/master/SI/Figures.ipynb) Supplement to the manusript.