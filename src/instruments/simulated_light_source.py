"""Virtual light source with range validation."""
from .base import LightSource, CommunicationError, SafetyInterlockError

class SimulatedLightSource(LightSource):
    def __init__(self, max_power_w: float = 0.01):
        self.max_power_w, self.power_w = max_power_w, 0.0
        self.enabled = False
        self.connected = False
    def connect(self) -> None:
        self.connected = True
    def set_power(self, power_w: float) -> None:
        if not self.connected:
            raise CommunicationError("light source is not connected")
        if power_w < 0 or power_w > self.max_power_w:
            raise SafetyInterlockError("optical power is outside the configured safe range")
        self.power_w = power_w
    def output(self, enabled: bool) -> None:
        if not self.connected:
            raise CommunicationError("light source is not connected")
        self.enabled = enabled
    def disconnect(self) -> None:
        self.enabled, self.connected = False, False
