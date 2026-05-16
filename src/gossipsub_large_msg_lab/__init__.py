"""Research toolkit for Gossipsub large-message handling."""

from .protocol import LargeMessage, Segment, Segmenter
from .reassembly import ReassemblyBuffer
from .simulator import SimulationConfig, SimulationResult, Simulator

__all__ = [
    "LargeMessage",
    "ReassemblyBuffer",
    "Segment",
    "Segmenter",
    "SimulationConfig",
    "SimulationResult",
    "Simulator",
]

__version__ = "0.1.0"
