import pytest
import astropy.io.fits as fits
import numpy

import numina.core
import numina.exceptions

from ..stare import StareImageBaseRecipe


def create_frame(val=0, keys=None):
    data = numpy.zeros((10, 10)) + val
    hdu = fits.PrimaryHDU(data)
    if keys:
        for k, v in keys.items():
            hdu.header[k] = v

    return fits.HDUList([hdu])


def create_frame_bpm():
    data = numpy.zeros((10, 10), dtype='uint8')
    hdu = fits.PrimaryHDU(data)
    hdu.header['EMIRUUID'] = '44444444444444444444444444444444'
    return fits.HDUList([hdu])


def create_frame_dark():
    data = numpy.zeros((10, 10))
    hdu = fits.PrimaryHDU(data)
    hdu.header['EMIRUUID'] = '11111111111111111111111111111111'
    return fits.HDUList([hdu])


def create_frame_flat():
    data = numpy.ones((10, 10))
    hdu = fits.PrimaryHDU(data)
    hdu.header['EMIRUUID'] = '22222222222222222222222222222222'
    return fits.HDUList([hdu])


def create_ob(value, nimages, exptime=100.0, starttime=0.0):

    frames = []
    for i in range(nimages):
        base = starttime
        off1 = i * exptime
        off2 = off1 + exptime
        t1 = base + off1
        t2 = base + off2
        keys = {'TSUTC1': t1, 'TSUTC2': t2}
        frame = numina.core.DataFrame(frame=create_frame(val=value, keys=keys))
        frames.append(frame)

    obsresult = numina.core.ObservationResult()
    obsresult.frames = frames
    return obsresult


@pytest.mark.parametrize("nimages", [1,2,3,4])
def test_stare_with_bpm(nimages):

    value = 4
    starttime = 1003000001.00034
    exptime = 102.0
    expected_data = value * numpy.ones((10, 10))
    obsresult = create_ob(value, nimages, exptime, starttime)

    recipe = StareImageBaseRecipe()
    rinput = recipe.create_input(
        obresult=obsresult,
        master_bpm=numina.core.DataFrame(frame= create_frame_bpm()),
        master_dark=numina.core.DataFrame(frame=create_frame_dark()),
        master_flat=numina.core.DataFrame(frame=create_frame_flat())
    )

    result = recipe.run(rinput)
    hdulist = result.frame.open()

    assert 'BPM' in hdulist
    
    hdu = hdulist[0]
    assert hdu.header['NUM-NCOM'] == nimages
    assert hdu.header['NUM-BPM'] == 'uuid:44444444444444444444444444444444'
    assert hdu.header['NUM-DK'] == 'uuid:11111111111111111111111111111111'
    assert hdu.header['NUM-FF'] == 'uuid:22222222222222222222222222222222'
    assert hdu.header['TSUTC1'] == starttime
    assert hdu.header['TSUTC2'] == starttime + nimages * exptime
    assert numpy.allclose(expected_data, hdu.data)


@pytest.mark.parametrize("nimages", [1,2,3,4])
def test_stare(nimages):

    value = 9
    starttime = 1030040001.00034
    exptime = 105.0
    expected_data = value * numpy.ones((10, 10))
    obsresult = create_ob(value, nimages, exptime, starttime)

    recipe = StareImageBaseRecipe()
    rinput = recipe.create_input(
        obresult=obsresult,
        master_dark=numina.core.DataFrame(frame=create_frame_dark()),
        master_flat=numina.core.DataFrame(frame=create_frame_flat())
    )

    result = recipe.run(rinput)
    hdulist = result.frame.open()

    bpm_ext = 0
    try:
        bpm_ext = hdulist['BPM']
    except KeyError:
        pass

    assert bpm_ext != 0, "Wrong BPM extension number"

    hdu = hdulist[0]
    assert hdu.header['NUM-NCOM'] == nimages
    assert hdu.header['NUM-DK'] == 'uuid:11111111111111111111111111111111'
    assert hdu.header['NUM-FF'] == 'uuid:22222222222222222222222222222222'
    assert hdu.header['TSUTC1'] == starttime
    assert hdu.header['TSUTC2'] == starttime + nimages * exptime
    assert numpy.allclose(expected_data, hdu.data)
