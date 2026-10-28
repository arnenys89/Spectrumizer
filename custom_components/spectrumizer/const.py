"""Constants for Spectrumizer."""

from typing import Final

DOMAIN: Final = "spectrumizer"
CONF_SOURCE_ENTITY: Final = "source_entity"
CONF_NAME: Final = "name"
CONF_SAMPLING_RATE: Final = "sampling_rate"
CONF_WINDOW_SIZE: Final = "window_size"
DEFAULT_NAME: Final = "Spectrum"
DEFAULT_SAMPLING_RATE: Final = 10.0
DEFAULT_WINDOW_SIZE: Final = 256
MIN_SAMPLING_RATE: Final = 0.1
MAX_SAMPLING_RATE: Final = 100.0
ALLOWED_WINDOW_SIZES: Final = [32, 64, 128, 256, 512, 1024]
PLATFORMS: Final = ["sensor"]
