import numpy as np

from fakebox.stdlib.ba import Parameter
from fmbox.consts import PRESET_SIZE

presets = np.zeros(PRESET_SIZE * 1024)
current = np.zeros(PRESET_SIZE)

def read(preset_idx):

    start = preset_idx * PRESET_SIZE
    end = (preset_idx + 1) * PRESET_SIZE
    current = np.copy(presets[start:end])


def write(preset_idx):

    start = preset_idx * PRESET_SIZE
    end = (preset_idx + 1) * PRESET_SIZE
    presets[start:end] = np.copy(current)
