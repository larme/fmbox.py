from operator import itemgetter

import numpy as np

from fmbox.consts import OP_NUM, PRESET_SIZE
from fmbox.presets import copy_op, copy_voice
from fmbox.parameters import make_op_pa, make_voice_pa


def uniquify_preset(preset, op_num=OP_NUM):

    # sort op: max audio out first, max op outs last

    op_stats = {}

    for op_idx in range(op_num):
        op_pa = make_op_pa(op_idx, preset=preset)
        audio_out_gain = op_pa.audio_out_gain.get_value()
        op_gains_sum = sum(param.get_value() for param in op_pa.to_op_gains)
        op_stats[op_idx] = (-audio_out_gain, op_gains_sum)

    sops = sorted(op_stats.items(), key=itemgetter(1))

    old_op_idx2new_op_idx = {t[0]: new_idx
                             for new_idx, t in enumerate(sops)}

    # rearrange op

    new_preset = np.zeros_like(preset)

    copy_voice(preset, new_preset)

    for old_idx, new_idx in old_op_idx2new_op_idx.items():

        copy_op(preset, old_idx, new_preset, new_idx)

        old_op_pa = make_op_pa(old_idx, preset)
        new_op_pa = make_op_pa(new_idx, new_preset)
        for old_idx2 in range(op_num):
            new_idx2 = old_op_idx2new_op_idx[old_idx2]
            v = old_op_pa.to_op_gains[old_idx2].get_value()
            new_op_pa.to_op_gains[new_idx2].set_value(v)

    return new_preset


def _cal_packed2unpacked_mapping(op_num=OP_NUM):

    packed = []

    def cal_param_mapping(pa, field):
        param = pa._data[field]
        try:
            params = [p for p in param]
        except TypeError:
            params = [param]

        vs = [p.ptr for p in params]
        packed.extend(vs)

    voice_pa = make_voice_pa()
    for field in ('main_freq', 'master_gain'):
        cal_param_mapping(voice_pa, field)

    for op_idx in range(op_num):
        op_pa = make_op_pa(op_idx)
        for field in ('harmony_ratio', 'phase_lock_value',
                      'env_amp_factor', 'env_durations', 'env_amps',
                      'audio_out_gain', 'to_op_gains'):
            cal_param_mapping(op_pa, field)

    p2up = {p_idx: up_idx for p_idx, up_idx in enumerate(packed)}
    return p2up


def pack_preset(preset, op_num=OP_NUM):
    """extract useful parameter from preset, return a compact preset"""

    p2up = _cal_packed2unpacked_mapping(op_num)
    packed = np.zeros(len(p2up))
    for p_idx, up_idx in p2up.items():
        packed[p_idx] = preset[up_idx]
    return np.array(packed)


def unpack_preset(packed, op_num=OP_NUM):
    preset = np.zeros(PRESET_SIZE)
    p2up = _cal_packed2unpacked_mapping(op_num)
    for p_idx, up_idx in p2up.items():
         preset[up_idx] = packed[p_idx]

    return preset
