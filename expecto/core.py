import warnings

import numpy as np

import astropy.units as u
from astropy.units import UnitsWarning
from astropy.io import fits
from astropy.utils.exceptions import AstropyUserWarning

from specutils import Spectrum1D


__all__ = [
    'get_spectrum'
]

phoenix_base_url = (
    'ftp://phoenix.astro.physik.uni-goettingen.de/'
    'v2.0/HiResFITS/PHOENIX-ACES-AGSS-COND-2011/'
)

phoenix_wavelength_url = (
    'ftp://phoenix.astro.physik.uni-goettingen.de/'
    'v2.0/HiResFITS/WAVE_PHOENIX-ACES-AGSS-COND-2011.fits'
)

phoenix_model_temps = np.concatenate([
    np.arange(2300, 7100, 100), np.arange(7000, 12200, 200)
])

phoenix_model_logg = np.arange(0, 6.5, 0.5)

phoenix_model_alpha = np.arange(-0.2, 1.4, 0.2)

phoenix_model_z = np.concatenate([
    np.arange(-4, -1, 1), np.arange(-2, 1.5, 0.5)
])


class OutsideGridWarning(AstropyUserWarning):
    """
    Warning for when there is no good match in the PHOENIX grid
    """
    pass


def validate_grid_point(T_eff, log_g, Z, alpha, closest_params):
    temp_out_of_range = (
        T_eff > phoenix_model_temps.max() or T_eff < phoenix_model_temps.min()
    )
    logg_out_of_range = (
        log_g > phoenix_model_logg.max() or log_g < phoenix_model_logg.min()
    )
    z_out_of_range = (
        Z > phoenix_model_z.max() or Z < phoenix_model_z.min()
    )
    alpha_out_of_range = (
        alpha > phoenix_model_alpha.max() or alpha < phoenix_model_alpha.min()
    )
    out_of_range = [
        temp_out_of_range, logg_out_of_range, z_out_of_range, alpha_out_of_range
    ]

    if np.any(out_of_range):
        warn_message = (
            f"{np.count_nonzero(out_of_range):d} supplied parameters out of the"
            f" boundaries of the PHOENIX model grid. Closest grid point has "
            f"parameters: {closest_params}"
        )
        warnings.warn(warn_message, OutsideGridWarning)


def get_url(T_eff, log_g, Z=0, alpha=0):
    """
    Construct an FTP address from a temperature, log g, metallicity, alpha.
    """
    closest_temp_index = np.argmin(np.abs(phoenix_model_temps - T_eff))
    closest_grid_temperature = phoenix_model_temps[closest_temp_index]

    closest_logg_index = np.argmin(np.abs(phoenix_model_logg - log_g))
    closest_grid_logg = phoenix_model_logg[closest_logg_index]

    closest_alpha_index = np.argmin(np.abs(phoenix_model_alpha - alpha))
    closest_grid_alpha = phoenix_model_alpha[closest_alpha_index]

    closest_Z_index = np.argmin(np.abs(phoenix_model_z - Z))
    closest_grid_Z = phoenix_model_z[closest_Z_index]

    closest_params = dict(
        T_eff=closest_grid_temperature,
        log_g=closest_grid_logg,
        Z=closest_grid_Z,
        alpha=closest_grid_alpha
    )

    # Give a warning if the input parameters are outside of the PHOENIX grid
    # parameter ranges:
    validate_grid_point(
        T_eff, log_g, Z, alpha, closest_params
    )

    if closest_grid_Z > 0.25:
        z_sign = '+'
    else:
        z_sign = '-'

    if closest_grid_alpha > 0.1:
        alpha_sign = '+'
    else:
        alpha_sign = '-'

    url = (
        phoenix_base_url +
        'Z' + z_sign +
        '{Z:1.1f}/lte{T_eff:05d}-{log_g:1.2f}' + alpha_sign +
        '{alpha:1.1f}.PHOENIX-ACES-AGSS-COND-2011-HiRes.fits'
    ).format(
        T_eff=closest_grid_temperature,
        log_g=closest_grid_logg,
        Z=abs(closest_grid_Z),
        alpha=closest_grid_alpha
    )
    return url


def get_spectrum(
        T_eff, log_g, Z=0, alpha=0, cache=False, vacuum=True
):
    """
    Download a PHOENIX model atmosphere spectrum for a star with given
    properties.

    Parameters
    ----------
    T_eff : float
        Effective temperature. The nearest grid-point will be selected.
    log_g : float
        Surface gravity. The nearest grid-point will be selected.
    Z : float
        Metallicity. The nearest grid-point will be selected.
    alpha : float
        Alpha element abundance. The nearest grid-point will be selected.
    cache : bool
        Cache the result to the local astropy cache. Default is `False`.
    vacuum : bool
        If `True`, return wavelengths in a vacuum, otherwise return for air.

    Returns
    -------
    spectrum : ~specutils.Spectrum1D
        Model spectrum
    """
    url = get_url(
        T_eff=T_eff, log_g=log_g, Z=Z, alpha=alpha
    )
    with fits.open(url, cache=cache) as fits_file:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UnitsWarning)
            header = fits_file[0].header
            flux_unit = u.Unit(header['BUNIT'])
        fluxes = fits_file[0].data * flux_unit

    wavelengths = get_phoenix_wavelengths(cache=cache, vacuum=vacuum)

    # only return wavelengths > 0:
    positive_wavelengths = wavelengths > 0

    # specutils requires that we sort the wavelengths:
    sort_wavelengths = np.argsort(wavelengths[positive_wavelengths])

    return Spectrum1D(
        flux=fluxes[positive_wavelengths][sort_wavelengths],
        spectral_axis=wavelengths[positive_wavelengths][sort_wavelengths],
        meta=header
    )


def get_phoenix_wavelengths(cache=True, vacuum=True):
    """
    Download a PHOENIX model atmosphere's wavelength grid
    Parameters
    ----------
    cache : bool
        Cache the result to the local astropy cache. Default is `True`.
    vacuum : bool (optional)
        Return vacuum wavelengths, otherwise air.

    Returns
    -------
    wavelengths : `~astropy.units.Quantity`
        Wavelength array grid in vacuum wavelengths
    """

    with fits.open(phoenix_wavelength_url, cache=cache) as fits_file:
        wavelengths_vacuum = fits_file[0].data

    # Wavelengths are provided at vacuum wavelengths. For ground-based
    # observations convert this to wavelengths in air, as described in
    # Husser 2013, Eqns. 8-10:
    sigma_2 = (10**4 / wavelengths_vacuum)**2
    f = (
        1.0 + 0.05792105/(238.0185 - sigma_2) +
        0.00167917 / (57.362 - sigma_2)
    )
    wavelengths_air = wavelengths_vacuum / f

    if vacuum:
        return wavelengths_vacuum * u.Angstrom

    return wavelengths_air * u.Angstrom
