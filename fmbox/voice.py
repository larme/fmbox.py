import numpy as np

from fakebox.dsp import DSPObj, DSPZero, DSPOne, DSPFloat
from fakebox.stdlib.ba import Pipe, Stack, Dup, Bypass, partial
from fakebox.stdlib.env import LineSegs
from fakebox.stdlib.math import Mul, Sum

from fmbox.consts import OP_NUM
from fmbox.parameters import make_voice_pa
from fmbox.presets import current as current_preset
from fmbox.op import Operator


def make_freq_env(voice_pa):

    amp_factor = voice_pa.fmod_env_amp_factor
    durations = voice_pa.fmod_env_durations
    amps = voice_pa.fmod_env_amps
    args = [amp_factor] + durations + amps
    env = LineSegs(8)

    return partial(env, args)


class Voice(DSPObj):

    def __init__(self, op_num=OP_NUM, preset=current_preset):

        # in: trigger
        # out: audio (pre-gain)
        self.in_n = 1
        self.out_n = 1

        self.op_num = op_num
        self.preset = preset
        self.pa = make_voice_pa(self.preset)

        env = make_freq_env(self.pa)
        plus_1 = Sum(DSPOne)
        env_plus_1 = Pipe([env, plus_1])
        self.freq_gen = partial(Mul(), [env_plus_1, self.pa.main_freq])

        # op_idx starts with 0, ends with op_num - 1
        self.ops = [Operator(idx, self.op_num, self.preset)for idx in range(op_num)]

        super().__init__()


    def _tick(self, ins):

        op_num = self.op_num

        trig = ins[0]

        self.freq_gen.in_buffer[0] = trig
        self.freq_gen.tick()
        freq = self.freq_gen.out_buffer[0]

        audio_out = DSPZero
        buf = np.zeros(op_num, dtype=DSPFloat)

        for op in self.ops:
            op.in_buffer[0] = freq
            op.in_buffer[2] = trig
            op.tick()

            audio_out += op.out_buffer[0]
            buf += op.out_buffer[1:op_num+1]

        for op_idx in range(op_num):
            self.ops[op_idx].in_buffer[1] = buf[op_idx]

        return audio_out * self.pa.master_gain.get_value()
