#
# Copyright 2015 Universidad Complutense de Madrid
#
# This file is part of PyEmir
#
# PyEmir is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyEmir is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
#

"""Bar detection procedures for EMIR"""

import logging

import numpy
from scipy.ndimage.filters import median_filter
import scipy.ndimage.measurements as mes
import scipy.ndimage.morphology as morph
from skimage.feature import canny

from numina.array.utils import expand_region
import numina.array.fwhm as fmod
from numina.array.utils import wc_to_pix_1d

from .common import normalize_raw


def find_position(edges, prow, bstart, bend, total=5):
    """Find a EMIR CSU bar position in a edge image.

    Parameters
    ==========
    edges; ndarray,
        a 2d image with 1 where is a border, 0 otherwise
    prow: int,
        reference 'row' of the bars
    bstart: int,
        minimum 'x' position of a bar (0-based)
    bend: int
        maximum 'x' position of a bar (0 based)
    total: int
        number of rows to check near `prow`

    Return
    ======
    list of (x, y) centroids

    """

    nt = total // 2

    # This bar is too near the border
    if prow-nt < 0 or prow + nt >= edges.shape[0]:
        return []

    s2edges = edges[prow-nt:prow+nt+1, bstart:bend]

    structure = morph.generate_binary_structure(2,2) # 8 way conection
    har, num_f = mes.label(s2edges, structure=structure)

    cen_of_mass = mes.center_of_mass(s2edges, labels=har, index=range(1, num_f + 1))

    # center_of_mass returns y, x coordinates

    cen_of_mass_off = [(x + bstart, prow-nt + y) for y,x in cen_of_mass]

    return cen_of_mass_off


def calc_fwhm(img, region, fexpand=3, axis=0):
    """Compute the FWHM in the direction given by axis"""

    # We compute know the FWHM of the slit
    # Given the computed position of the slit
    # Expand 'fexpand' pixels around
    # and cut an slice in the median filtered image

    xpregion = expand_region(region, fexpand, fexpand)
    cslit = img[xpregion]

    # Collapse it
    pslit = cslit.mean(axis=axis)

    # Estimate the background as a flat line
    # starting in pslit[0] and ending in pslit[-1]
    x2 = len(pslit)
    y1, y2 = pslit[0], pslit[-1]
    mslope = (y2-y1) / x2
    # background estimation
    backstim = mslope*numpy.arange(x2) + y1

    # We subtract background
    qslit = pslit-backstim
    # and find the pixel of the maximum
    pidx = numpy.argmax(qslit)
    peak, fwhm = fmod.compute_fwhm_1d_simple(qslit, pidx)
    return fwhm


def simple_prot(x, start):
    """Find the first peak to the right of start"""

    # start must b >= 1

    for i in range(start,len(x)-1):
        a,b,c =  x[i-1], x[i], x[i+1]
        if b - a > 0 and b -c >= 0:
            return i
    else:
        return None


def position_half_h(pslit, cpix, backw=4):
    """Find the position where the value is half of the peak"""

    # Find the first peak to the right of cpix
    next_peak = simple_prot(pslit, cpix)

    if next_peak is None:
        raise ValueError

    dis_peak = next_peak - cpix

    wpos2 = cpix - dis_peak
    wpos1 = wpos2 - backw

    # Compute background in a window of width backw
    # in a position simetrical to the peak
    # around cpix
    left_background = pslit[wpos1:wpos2].min()

    # height of the peak
    height = pslit[next_peak] - left_background


    half_height = left_background + 0.5 * height

    # Position at halg peak, linear interpolation
    vv = pslit[wpos1:next_peak+1] - half_height

    res1, =  numpy.nonzero(numpy.diff(vv > 0))
    i1 = res1[0]

    xint = wpos1 + i1 + (0 - vv[i1]) / (vv[i1+1] - vv[i1])

    return xint, next_peak, wpos1, wpos2, left_background, half_height


def locate_bar_l(icut, epos):
    """Fine position of the left CSU bar"""
    def swap_coor(x):
        return x

    def swap_line(tab):
        return tab

    return _locate_bar_gen(icut, epos,
                           transform1=swap_coor,
                           transform2=swap_line
                           )


def locate_bar_r(icut, epos):
    """Fine position of the right CSU bar"""
    sm = len(icut)

    def swap_coor(x):
        return sm - 1 - x

    def swap_line(tab):
        return tab[::-1]

    return _locate_bar_gen(icut, epos, transform1=swap_coor,
                           transform2=swap_line)


def _locate_bar_gen(icut, epos, transform1, transform2):
    """Generic function for the fine position of the CSU"""

    epos_pix = wc_to_pix_1d(epos)

    # transform ->
    epos_pix_s = transform1(epos_pix)
    icut2 = transform2(icut)
    #

    try:
        res = position_half_h(icut2, epos_pix_s)

        xint_s, next_peak_s, wpos1_s, wpos2_s, background_level, half_height = res
        #

        xint = transform1(xint_s)

        #
        epos_f = xint
        error = 0
    except ValueError:
        error = 2
        epos_f = epos

    return epos, epos_f, error