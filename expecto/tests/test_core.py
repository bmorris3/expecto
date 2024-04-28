import pytest
import numpy as np

import astropy.units as u
from astropy.modeling.models import BlackBody
from astropy.tests.helper import assert_quantity_allclose

from ..core import get_spectrum


@pytest.mark.remote_data
def test_get_spectrum():

    test_temp = 12000
    test_logg = 6.0
    spectrum = get_spectrum(
        T_eff=test_temp, log_g=test_logg, cache=False
    )

    assert spectrum.wavelength.shape[0] == 1569128

    test_mask = spectrum.wavelength > 1e4 * u.Angstrom

    bb = np.pi * u.sr * BlackBody(test_temp * u.K)(spectrum.wavelength)
    bb_transformed = bb[test_mask].to(
        spectrum.flux.unit, u.spectral_density(spectrum.wavelength[test_mask])
    )

    bb_scaled = np.linalg.lstsq(
        bb_transformed.value[:, None], spectrum.flux[test_mask].value[:, None],
        rcond=-1
    )[0][0, 0] * bb_transformed

    assert_quantity_allclose(
        np.log(bb_scaled.value),
        np.log(spectrum.flux[test_mask].value),
        rtol=0.02
    )


@pytest.mark.remote_data
@pytest.mark.parametrize(
    'params,',
    [
        dict(T_eff=3477, log_g=4.833, Z=+0.33, alpha=0),
        dict(T_eff=3477, log_g=4.833, Z=-0.33, alpha=0.4),
        dict(T_eff=3477, log_g=4.833, Z=-0.33, alpha=0.8),
    ]
)
def test_metallicity(params):
    spectrum = get_spectrum(
        **params
    )

    # validate that the metadata matches
    # expectations given the inputs:
    retrieved_T_eff = spectrum.meta['PHXTEFF']
    retrieved_Z = spectrum.meta['PHXM_H']
    retrieved_alpha = spectrum.meta['PHXALPHA']

    assert retrieved_T_eff == np.round(params['T_eff'], -2)
    assert retrieved_Z == np.round(params['Z'] * 2, 0) / 2
    assert retrieved_alpha == params['alpha']
