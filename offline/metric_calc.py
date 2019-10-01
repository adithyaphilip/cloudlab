from typing import List
import math
import numpy as np
import scipy as sc
import scipy.stats as stats


def get_jfi(bws: List[float]):
    cov = stats.variation(bws)
    return 1 / (1 + cov ** 2)


def mathis_throughput(mss_b: int, rtt_s: float, loss_rate: float):
    return mss_b / (rtt_s * (loss_rate ** 0.5))
