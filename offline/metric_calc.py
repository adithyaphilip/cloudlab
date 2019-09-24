from typing import List
import math
import numpy as np
import scipy as sc
import scipy.stats as stats


def get_jfi(bws: List[float]):
    cov = stats.variation(bws)
    return 1 / (1 + cov**2)