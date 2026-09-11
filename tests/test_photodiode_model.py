import random
from src.dut.photodiode_model import Photodiode

def test_light_produces_expected_photocurrent():
    dut = Photodiode(noise_std_a=0.0, dut_id="T1")
    dark = dut.current(-2.0, 0.0, random.Random(1), wavelength_nm=900.0)
    light = dut.current(-2.0, 0.001, random.Random(1), wavelength_nm=900.0)
    assert abs((dark - light) / 0.001 - 0.55) < 1e-9

def test_unknown_profile_is_rejected():
    try:
        Photodiode.from_profile("T2", "imaginary")
    except ValueError:
        return
    raise AssertionError("unknown profile was accepted")
