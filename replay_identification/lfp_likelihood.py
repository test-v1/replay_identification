import numpy as np
from statsmodels.nonparametric.kernel_density import KDEMultivariate
from spectral import Multitaper, Connectivity


def lfp_likelihood_ratio(lfps, is_candidate_replay, sampling_frequency):
    '''The likelihood of being in a replay state over time given the
    spectral power of the local field potentials (LFPs).

    Parameters
    ----------
    lfps : ndarray, shape (n_time, n_signals)
    is_candidate_replay : bool ndarray, shape (n_time,)
    sampling_frequency : float

    Returns
    -------
    lfp_likelihood : ndarray (n_time,)

    '''
    ripple_band_power = np.log(estimate_ripple_band_power(
        lfps, sampling_frequency))
    kde = estimate_kernel_density(ripple_band_power)
    out_replay_log_likelihood = kde.pdf(
        ripple_band_power[~is_candidate_replay])
    in_replay_log_likelihood = kde.pdf(
        ripple_band_power[is_candidate_replay])

    return in_replay_log_likelihood - out_replay_log_likelihood


def estimate_kernel_density(ripple_band_power):
    '''Evaluate a multivariate gaussian kernel for each time point

    Parameters
    ----------
    ripple_band_power : ndarray, shape (n_time, n_signals)

    Returns
    -------
    kernel_density_estimate : sklearn function

    '''
    n_time, n_signals = ripple_band_power.shape
    # replace with np.var?
    power_variances = (np.std(ripple_band_power, axis=0) *
                       (4 / (n_signals + 2) / n_time) **
                       (1 / (n_signals + 4))) ** 2
    return KDEMultivariate(
        ripple_band_power, bw=power_variances, var_type='c' * n_signals)


def estimate_ripple_band_power(lfps, sampling_frequency):
    '''Estimates the 200 Hz power of each LFP

    Parameters
    ----------
    lfps : ndarray, shape (n_time, n_signals)
    sampling_frequency : float

    Returns
    -------
    ripple_band_power : ndarray (n_time, n_signals)

    '''
    m = Multitaper(lfps, sampling_frequency=sampling_frequency,
                   time_halfbandwidth_product=1,
                   time_window_duration=0.020,
                   time_window_step=1 / sampling_frequency)
    c = Connectivity.from_multitaper(m)
    closest_200Hz_freq_ind = np.argmin(np.abs(c.frequencies - 200))
    return c.power()[..., closest_200Hz_freq_ind, :].squeeze()
