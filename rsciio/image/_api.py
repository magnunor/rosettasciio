# -*- coding: utf-8 -*-
# Copyright 2007-2023 The HyperSpy developers
#
# This file is part of RosettaSciIO.
#
# RosettaSciIO is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RosettaSciIO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RosettaSciIO. If not, see <https://www.gnu.org/licenses/#GPL>.

import os
import logging

import imageio.v3 as iio
import numpy as np

from rsciio._docstrings import (
    FILENAME_DOC,
    RETURNS_DOC,
    SIGNAL_DOC,
)
from rsciio.utils.tools import _UREG


_logger = logging.getLogger(__name__)


def file_writer(
    filename,
    signal,
    scalebar=False,
    scalebar_kwds=None,
    output_size=None,
    imshow_kwds=None,
    **kwds,
):
    """Writes data to any format supported by pillow. The file format is defined by
    the file extension that is any one supported by imageio. When any of the
    parameters ``output_size``, ``scalebar`` or ``imshow_kwds`` is given,
    :py:func:`~.matplotlib.pyplot.imshow` is used to generate a figure.

    Parameters
    ----------
    %s
    %s
    scalebar : bool, Default=False
        Export the image with a scalebar.
    scalebar_kwds : dict, optional
        Dictionary of keyword arguments for the scalebar. Useful to set
        formatting, location, etc. of the scalebar. See the documentation of
        the 'matplotlib-scalebar' library for more information.
    output_size : {tuple of length 2, int, None}, Default=None
        The output size of the image in pixels (width, height):

            * if *int*, defines the width of the image, the height is
              determined from the aspec ratio of the image
            * if *tuple of length 2*, defines the width and height of the
              image. Padding with white pixels is used to maintain the aspect
              ratio of the image.
            * if *None*, the size of the data is used.

        For output sizes larger than the data size, "nearest" interpolation is
        used by default and this behaviour can be changed through the
        *imshow_kwds* dictionary.

    imshow_kwds : dict, optional
        Keyword arguments dictionary for :py:func:`~.matplotlib.pyplot.imshow`.
    **kwds : keyword arguments, optional
        Allows to pass keyword arguments supported by the individual file
        writers as documented at
        https://imageio.readthedocs.io/en/stable/formats/index.html when
        exporting an image without scalebar. When exporting with a scalebar,
        the keyword arguments are passed to the `pil_kwargs` dictionary of
        :py:func:`~matplotlib.pyplot.savefig`

    """
    data = signal["data"]
    sig_axes = [ax for ax in signal["axes"] if not ax["navigate"]]
    nav_axes = [ax for ax in signal["axes"] if ax["navigate"]]

    if scalebar_kwds is None:
        scalebar_kwds = dict()
    scalebar_kwds.setdefault("box_alpha", 0.75)
    scalebar_kwds.setdefault("location", "lower left")

    # HyperSpy uses struct arrays to store RGBA data
    from rsciio.utils import rgb_tools

    if rgb_tools.is_rgbx(data):
        data = rgb_tools.rgbx2regular_array(data)

    if scalebar:
        try:
            from matplotlib_scalebar.scalebar import ScaleBar
        except ImportError:  # pragma: no cover
            scalebar = False
            _logger.warning(
                "Exporting image with scalebar requires the "
                "matplotlib-scalebar library."
            )

    if scalebar or output_size or imshow_kwds:
        try:
            from matplotlib.figure import Figure
        except ImportError:
            raise ValueError(
                "Using the `output_size`, `imshow_kwds` arguments or "
                "exporting with a scalebar requires the matplotlib library."
            )

        dpi = 100

        if imshow_kwds is None:
            imshow_kwds = dict()
        imshow_kwds.setdefault("cmap", "gray")

        axes = []
        if len(sig_axes) == 2:
            axes = sig_axes
        elif len(nav_axes) == 2:
            # Use navigation axes
            axes = nav_axes
        else:
            raise RuntimeError("This dimensionality is not supported.")

        aspect_ratio = imshow_kwds.get("aspect", None)
        if not isinstance(aspect_ratio, (int, float)):
            aspect_ratio = data.shape[0] / data.shape[1]

        if output_size is None:
            # fall back to image size taking into account aspect_ratio
            ratio = (1, aspect_ratio)
            output_size = [axis["size"] * r for axis, r in zip(axes, ratio)]
        elif isinstance(output_size, (int, float)):
            output_size = [output_size, output_size * aspect_ratio]

        fig = Figure(figsize=[size / dpi for size in output_size], dpi=dpi)

        # List of format supported by matplotlib
        supported_format = sorted(fig.canvas.get_supported_filetypes())
        if os.path.splitext(filename)[1].replace(".", "") not in supported_format:
            if scalebar:
                raise ValueError(
                    "Exporting image with scalebar is supported "
                    f"only with {', '.join(supported_format)}."
                )
            if output_size:
                raise ValueError(
                    "Setting the output size is only supported "
                    f"with {', '.join(supported_format)}."
                )

    if scalebar:
        # Sanity check of the axes
        # This plugin doesn't support non-uniform axes, we don't need to check
        # if the axes have a scale attribute
        if axes[0]["scale"] != axes[1]["scale"] or axes[0]["units"] != axes[1]["units"]:
            raise ValueError(
                "Scale and units must be the same for each axes "
                "to export images with a scale bar."
            )

    if scalebar or output_size:
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.imshow(data, **imshow_kwds)

        if scalebar:
            # Add scalebar
            axis = axes[0]
            units = axis["units"]
            if units is None:
                units = "px"
                scalebar_kwds["dimension"] = "pixel-length"
            else:
                units = _UREG.Quantity(units)
                if units.check("1/[length]"):
                    scalebar_kwds["dimension"] = "si-length-reciprocal"
                # Standard formatting of units to avoid issue with
                # matplotlib-scalebar
                units = f"{units.units:~C}"

            ax.add_artist(ScaleBar(axis["scale"], units, **scalebar_kwds))

        fig.savefig(filename, dpi=dpi, pil_kwargs=kwds)
    else:
        iio.imwrite(filename, data, **kwds)


file_writer.__doc__ %= (FILENAME_DOC.replace("read", "write to"), SIGNAL_DOC)


def file_reader(filename, **kwds):
    """Read data from any format supported by imageio (PIL/pillow). The file
    format is defined by the file extension that is any one supported by imageio.
    For a list of formats see
    https://imageio.readthedocs.io/en/stable/formats/index.html

    Parameters
    ----------
    %s
    format: str, optional
        The format to use to read the file. By default imageio selects the
        appropriate format based on the filename and its contents.
    **kwds: keyword arguments
        Allows to pass keyword arguments supported by the individual file
        readers as documented at
        https://imageio.readthedocs.io/en/stable/formats/index.html

    %s
    """
    dc = _read_data(filename, **kwds)
    lazy = kwds.pop("lazy", False)
    if lazy:
        # load the image fully to check the dtype and shape, should be cheap.
        # Then store this info for later re-loading when required
        from dask.array import from_delayed
        from dask import delayed

        val = delayed(_read_data, pure=True)(filename)
        dc = from_delayed(val, shape=dc.shape, dtype=dc.dtype)
    return [
        {
            "data": dc,
            "metadata": {
                "General": {"original_filename": os.path.split(filename)[1]},
                "Signal": {"signal_type": ""},
            },
        }
    ]


file_reader.__doc__ %= (FILENAME_DOC, RETURNS_DOC)


def _read_data(filename, **kwds):
    dc = np.squeeze(iio.imread(filename))
    if len(dc.shape) > 2:
        # It may be a grayscale image that was saved in the RGB or RGBA
        # format
        if (dc[:, :, 1] == dc[:, :, 2]).all() and (dc[:, :, 1] == dc[:, :, 2]).all():
            dc = dc[:, :, 0]
        else:
            # HyperSpy uses struct arrays to store RGB data
            from rsciio.utils import rgb_tools

            dc = rgb_tools.regular_array2rgbx(dc)

    return dc
