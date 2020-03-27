import numpy as np
from scipy.optimize import least_squares

def Jacobian(x, wv, aspl, bspl, daspl, dbspl, sigma, **kwargs):
    """
    Calculate the jacobian for the minimisation function.

    Parameters
    ==========
    x : tuple
        A tuple containing the model parameters as (a, b, B0, c, m)
    wv : array-like
        The wavelength of the data
    aspl, bspl : UnivariateSpline
        Spline objects that produce the acid (aspl) or base (aspl)
        molal absorption given a wavelength.
    daspl, sbspl : UnivariateSpline
        Spline objects that return the first derivative of aspl and
        bspl at a given wavelength.
    
    Returns
    =======
    Jacobian of fitting function as a matrix of shape (n,m) : array-like
    """
    a, b, _, c, m = x

    J = np.ones((len(wv), 5))
    
    J[:,0] = aspl(wv * m + c)  # a
    J[:,1] = bspl(wv * m + c)  # b
    # bkg is just ones
    J[:,3] = a * daspl(wv * m + c) + b * dbspl(wv * m + c)  # c
    J[:,4] = wv * a * daspl(wv * m + c) + wv * b * dbspl(wv * m + c)  # m
    
    return J / sigma.reshape(-1,1)  # this pre-scales the jacobian so that it's appropriate for scaled residuals

def specmix(x, wv, aspl, bspl, **kwargs):
    """
    Return the mixture of aspl and bspl specified by the parameters in x.

    Parameters
    ==========
    x : tuple
        A tuple containing the model parameters as (a, b, B0, c, m)
    wv : array-like
        The wavelength of the data
    aspl, bspl : UnivariateSpline
        Spline objects that produce the acid (aspl) or base (aspl)
        molal absorption given a wavelength.
    """
    a, b, B0, c, m = x
    return a * aspl(m * wv + c) + b * bspl(m * wv + c) + B0

def obj_fn(x, wv, Abs, sigma, aspl, bspl, **kwargs):
    """
    Objective function for least squares optimisation
    """
    return (specmix(x, wv, aspl, bspl) - Abs) / sigma
    # divide by sigma makes this equivalent to multiplying by 1 / sigma**2 once the sumsq of residuals is calculated.

def jac_2_cov(fit):
    """
    Calculate the covariance matrix from the jacobian contained within a least_squares result.
    
    Parameters
    """
    s_sq = 2 * fit.cost / (fit.fun.size - fit.x.size)  # RSS / DOF; fit.cost is half the sum of squares (see curve_fit source)
    # covariance matrix is inverse of hessian (H = J.dot(J.T)) scaled to MSE.
    return np.linalg.inv(fit.jac.T.dot(fit.jac)) * s_sq

def guess_p0(wv, Abs, aspl, bspl):
    # guess starting values for optimisation
    B0start = Abs[-10:].mean()  # background
    
    base_loc = np.argmax(bspl(wv))  # wavelength of maximum base absorption
    bstart = max(Abs[base_loc] - B0start, 0) / bspl(wv[base_loc])  # acid coefficient
    
    acid_loc = np.argmax(aspl(wv))  # wavelength of maximum acid absorption
    astart = max(Abs[acid_loc] - B0start - bstart * bspl(wv[acid_loc]), 0) / aspl(wv[acid_loc])  # acid coefficient

    return astart, bstart, B0start, 0, 1

def fit_spectrum(wv, Abs, aspl, bspl, sigma=np.array(1), p0=None,
                 bounds=((0, 0, -np.inf, -20, 0.98), (np.inf, np.inf, np.inf, 20, 1.02))):
    """
    Fit a spectrum with a combination of end-member spectra.

    Parameters
    ==========
    wv : array-like
        The wavelength of the absorption spectrum
    Abs : array-like
        The absorption spectrum
    aspl, bspl : UnivariateSpline
        Spline objects that produce the acid (aspl) or base (aspl)
        molal absorption given a wavelength.
    sigma : array-like
        The standard deviation of the data.
    pstart : array-like
        Start values for parameters (a, b, B0, c, m) used in fitting.
    bounds : two-tuple
        Bounds for parameters (a, b, B0, c, m) used in fitting.

    Returns
    =======
    p, cov  : the optimal values for (a, b, B0, c, m) and their covariance matrix
    """
    if p0 is None:
        p0 = guess_p0(wv, Abs, aspl, bspl)
    fit = least_squares(obj_fn, p0, jac=Jacobian, 
                        kwargs=dict(wv=wv, Abs=Abs, sigma=sigma, aspl=aspl, bspl=bspl, daspl=aspl.derivative(), dbspl=bspl.derivative()), 
                        bounds=bounds, method='trf', x_scale='jac', loss='soft_l1', tr_solver='exact')
    return fit.x, jac_2_cov(fit)
