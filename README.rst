expecto
=======

.. image:: http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat
    :target: http://www.astropy.org/

.. image:: https://github.com/bmorris3/expecto/workflows/CI%20Tests/badge.svg
    :target: https://github.com/bmorris3/expecto/actions


Basic usage
+++++++++++

Let's get a Sun-like spectrum:

.. code-block:: python

    from expecto import get_spectrum

    spectrum = get_spectrum(
        T_eff=5800, log_g=4.5, cache=False
    )

Want a plot of the spectrum?

.. code-block:: python

    # Plot the spectrum:
    import matplotlib.pyplot as plt
    from astropy.visualization import quantity_support

    with quantity_support():
        plt.plot(spectrum.wavelength, spectrum.flux)