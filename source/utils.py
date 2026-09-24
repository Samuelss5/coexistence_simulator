import numpy as np

import os

def dbm2lin(x):

    return pow(10, x/10 - 3)

def db2lin(x):

    return pow(10,x/10)

def lin2db(x):
    """
    Converts a value from linear scale to decibels (dB).
    
    Parameters
    ----------
    x : float or ndarray
        Value(s) in linear scale.
    """

    return 10.0 * np.log10(x)

def cdf_args(x):

    """
    
    Generate the arguments to plot a CDF
    
    """

    return np.sort(x), np.arange(0, len(x)) / len(x)


def read_txt_file(file):

    """
    
    Read text files to get the values
    
    """

    if os.path.exists(file):

        data = np.loadtxt(file)

        return data
    
    else:

        print("Arquivo não encontrado")
