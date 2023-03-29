=======
expecto
=======

Pure Python package for retrieving
`PHOENIX model stellar spectra <https://phoenix.astro.physik.uni-goettingen.de/?>`_
via FTP. Spectra are returned as
`specutils.Spectrum1D <https://specutils.readthedocs.io/en/stable/api/specutils.Spectrum1D.html#specutils.Spectrum1D>`_
objects. The source code is available
`on GitHub <https://github.com/bmorris3/expecto>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   expecto/install.rst
   expecto/acknowledge.rst
   expecto/index.rst

Basic Usage
^^^^^^^^^^^

Let's get a Sun-like spectrum:

.. code-block:: python

    from expecto import get_spectrum

    spectrum = get_spectrum(
        T_eff=5800, log_g=4.5, cache=False
    )

and let's plot that spectrum:

.. code-block:: python

    import matplotlib.pyplot as plt
    from astropy.visualization import quantity_support

    with quantity_support():
        plt.plot(spectrum.wavelength, spectrum.flux)


.. plot::

    from expecto import get_spectrum

    spectrum = get_spectrum(
        T_eff=5800, log_g=4.5, cache=False
    )

    import matplotlib.pyplot as plt
    from astropy.visualization import quantity_support

    with quantity_support():
        plt.plot(spectrum.wavelength, spectrum.flux)

    plt.show()

