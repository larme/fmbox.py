import numpy as np

from fakebox.stdlib.ba import Parameter
from fmbox.consts import PRESET_SIZE, SECTION_SIZE

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


def copy(src):
    target = np.zeros_like(src)
    target[:] = src
    return target


def copy_section(src_preset, src_section_id,
                 target_preset, target_section_id,
                 section_size=SECTION_SIZE):
    
    src_start = src_section_id * section_size
    src_end = src_start + section_size
    target_start = target_section_id * section_size
    target_end = target_start + section_size
    target_preset[target_start:target_end] = src_preset[src_start:src_end]

    return target_preset


def copy_voice(src_preset, target_preset, section_size=SECTION_SIZE):
    return copy_section(src_preset, 0, target_preset, 0, section_size)


def copy_op(src_preset, src_op_id,
            target_preset, target_op_id,
            section_size=SECTION_SIZE):
    
    src_section_id = src_op_id + 1
    target_section_id = target_op_id + 1

    target_preset = copy_section(src_preset, src_section_id,
                                 target_preset, target_section_id,
                                 section_size)

    return target_preset
