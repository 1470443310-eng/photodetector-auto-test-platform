import pytest
from src.dut.photodiode_model import Photodiode
from src.instruments.base import CommunicationError, SafetyInterlockError
from src.instruments.simulated_smu import SimulatedSMU

def test_communication_fault_is_error():
    smu = SimulatedSMU(Photodiode.from_profile("T", "communication_error"), 1, .001)
    with pytest.raises(CommunicationError): smu.connect()

def test_voltage_interlock():
    smu = SimulatedSMU(Photodiode.from_profile("T", "normal"), 1, .001, 5.0); smu.connect()
    with pytest.raises(SafetyInterlockError): smu.measure_current(-6.0, 0.0)
