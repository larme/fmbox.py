from fakebox.dsp import DSPObj
from fakebox.stdlib.ba import Pipe, Stack, Dup, Bypass, partial
from fakebox.stdlib.env import LineSegs
from fakebox.stdlib.math import Mul
from fakebox.stdlib.osc import make_sinosc

from fmbox.consts import SECTION_SIZE, OP_NUM, ENV_SEG_NUM
from fmbox.presets import current as current_preset
from fmbox.parameters import make_op_pa


def make_op_osc(op_pa):

    init_phase = op_pa.phase_lock_value
    phase_lock = op_pa.phase_lock_switch

    # if phase_lock == 0, no trig to osc
    trig = Stack([phase_lock, Bypass()])
    trig = Pipe([trig, Mul()])

    freq = Bypass()

    osc = make_sinosc()
    osc = partial(osc, [init_phase, freq, trig])
    return osc


def make_op_env(op_pa):

    amp_factor = op_pa.env_amp_factor
    durations = op_pa.env_durations
    amps = op_pa.env_amps
    args = [amp_factor] + durations + amps
    env = LineSegs(ENV_SEG_NUM)
    return partial(env, args)


def assemble_core_osc(osc, env):

    # inputs: 0 freq in | 1 trig
    # output: osc mi sig

    # split trig to osc and env
    splitter = Dup()
    router = Stack([Bypass(), splitter])
    o_and_e = Stack([osc, env])
    return Pipe([router, o_and_e, Mul()])


class Operator(DSPObj):

    def __init__(self, op_idx, op_num=OP_NUM, preset=current_preset):

        self.op_idx = op_idx
        self.pa = make_op_pa(op_idx, preset)

        osc = make_op_osc(self.pa)
        env = make_op_env(self.pa)
        self.core_osc = assemble_core_osc(osc, env)

        # 0 main_freq in | 1 freq mod in | 2 trig
        self.in_n = 3
        self.out_n = 1 + op_num

        super().__init__()


    def _tick(self, ins):

        main_freq = ins[0]
        freq_mod = ins[1]
        trig = ins[2]

        harmony_ratio = self.pa.harmony_ratio.get_value()

        base_freq = main_freq * harmony_ratio
        freq = base_freq + freq_mod

        self.core_osc.in_buffer[0] = freq
        self.core_osc.in_buffer[1] = trig
        self.core_osc.tick()
        osc_out = self.core_osc.out_buffer[0]

        audio_out = osc_out * self.pa.audio_out_gain.get_value()
        raw_out = osc_out * freq
        op_outs = [raw_out * gain.get_value() for gain in self.pa.to_op_gains]
        return [audio_out] + op_outs
