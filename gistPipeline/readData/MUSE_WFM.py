from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

import os
import logging

from printStatus import printStatus

from gistPipeline.readData import der_snr as der_snr


# ======================================
# Routine to set DEBUG mode
# ======================================
def set_debug(cube, xext, yext):
    logging.info(
        "DEBUG mode is activated. Instead of the entire cube, only one line of spaxels is used."
    )
    cube["x"] = cube["x"][int(yext / 2) * xext : (int(yext / 2) + 1) * xext]
    cube["y"] = cube["y"][int(yext / 2) * xext : (int(yext / 2) + 1) * xext]
    cube["snr"] = cube["snr"][int(yext / 2) * xext : (int(yext / 2) + 1) * xext]
    cube["signal"] = cube["signal"][int(yext / 2) * xext : (int(yext / 2) + 1) * xext]
    cube["noise"] = cube["noise"][int(yext / 2) * xext : (int(yext / 2) + 1) * xext]

    cube["spec"] = cube["spec"][:, int(yext / 2) * xext : (int(yext / 2) + 1) * xext]
    cube["error"] = cube["error"][:, int(yext / 2) * xext : (int(yext / 2) + 1) * xext]

    return cube


# ======================================
# Routine to load MUSE-cubes
# ======================================
def readCube(config):
    loggingBlanks = (len(os.path.splitext(os.path.basename(__file__))[0]) + 33) * " "

    # Read MUSE-cube
    printStatus.running("Reading the MUSE-WFM cube")
    logging.info("Reading the MUSE-WFM cube: " + config["GENERAL"]["INPUT"])

    # Reading the cube
    hdu = fits.open(config["GENERAL"]["INPUT"])
    if len(hdu) == 1:
        ihdu = 0
        printStatus.running("data in first HDU")
    else:
        ihdu = 1

    hdr = hdu[ihdu].header
    data = hdu[ihdu].data
    s = np.shape(data)
    spec = np.reshape(data, [s[0], s[1] * s[2]])

    wcshdr = WCS(hdr).to_header()

    # Read the variance spectra if available. Otherwise estimate the variance with the der_snr algorithm
    if len(hdu) >= 3:
        logging.info("Reading the error (variance) spectra from the cube")
        stat = hdu[2].data
        espec = np.reshape(stat, [s[0], s[1] * s[2]])
    elif len(hdu) <= 2:
        logging.info(
            "No error (variance) extension found. Estimating the variance spectra with the der_snr algorithm"
        )
        espec = np.zeros(spec.shape)
        for i in range(0, spec.shape[1]):
            espec[:, i] = der_snr.der_snr(spec[:, i])

    # Getting the wavelength info
    wave = hdr["CRVAL3"] + (np.arange(s[0])) * hdr["CD3_3"]

    # Getting the spatial coordinates
    origin = [
        float(config["READ_DATA"]["ORIGIN"].split(",")[0].strip()),
        float(config["READ_DATA"]["ORIGIN"].split(",")[1].strip()),
    ]
    xaxis = (np.arange(s[2]) - origin[0]) * hdr["CD2_2"] * 3600.0
    yaxis = (np.arange(s[1]) - origin[1]) * hdr["CD2_2"] * 3600.0
    x, y = np.meshgrid(xaxis, yaxis)
    x = np.reshape(x, [s[1] * s[2]])
    y = np.reshape(y, [s[1] * s[2]])
    pixelsize = hdr["CD2_2"] * 3600.0
    logging.info(
        "Extracting spatial information:\n"
        + loggingBlanks
        + "* Spatial coordinates are centred to "
        + str(origin)
        + "\n"
        + loggingBlanks
        + "* Spatial pixelsize is "
        + str(pixelsize)
    )

    # De-redshift spectra
    wave = wave / (1 + config["GENERAL"]["REDSHIFT"])
    logging.info(
        "Shifting spectra to rest-frame, assuming a redshift of "
        + str(config["GENERAL"]["REDSHIFT"])
    )

    # Shorten spectra to required wavelength range
    lmin = config["READ_DATA"]["LMIN_TOT"]
    lmax = config["READ_DATA"]["LMAX_TOT"]
    idx = np.where(np.logical_and(wave >= lmin, wave <= lmax))[0]
    spec = spec[idx, :]
    espec = espec[idx, :]
    wave = wave[idx]
    logging.info(
        "Shortening spectra to the wavelength range from "
        + str(config["READ_DATA"]["LMIN_TOT"])
        + "A to "
        + str(config["READ_DATA"]["LMAX_TOT"])
        + "A."
    )

    # Computing the SNR per spaxel
    idx_snr = np.where(
        np.logical_and(
            wave >= config["READ_DATA"]["LMIN_SNR"],
            wave <= config["READ_DATA"]["LMAX_SNR"],
        )
    )[0]
    signal = np.nanmedian(spec[idx_snr, :], axis=0)
    noise = np.sqrt(np.nanmedian(espec[idx_snr, :], axis=0))
    snr = np.nanmedian(spec[idx_snr, :] / np.sqrt(espec[idx_snr, :]), axis=0)
    logging.info(
        "Computing the signal-to-noise ratio in the wavelength range from "
        + str(config["READ_DATA"]["LMIN_SNR"])
        + "A to "
        + str(config["READ_DATA"]["LMAX_SNR"])
        + "A."
    )

    # Storing everything into a structure
    cube = {
        "x": x,
        "y": y,
        "wave": wave,
        "spec": spec,
        "error": espec,
        "snr": snr,
        "signal": signal,
        "noise": noise,
        "pixelsize": pixelsize,
        "wcshdr": wcshdr,
    }

    # Constrain cube to one central row if switch DEBUG is set
    if config["READ_DATA"]["DEBUG"] == True:
        cube = set_debug(cube, s[2], s[1])

    printStatus.updateDone("Reading the MUSE-WFM cube")
    print("             Read " + str(len(cube["x"])) + " spectra!")
    logging.info(
        "Finished reading the MUSE cube! Read a total of "
        + str(len(cube["x"]))
        + " spectra!"
    )

    return cube
