import os, csv, re

from fakebox.dsp import DSPFloat
from fakebox.stdlib.ba import Parameter as DSPParam

import fmbox.presets
from fmbox.consts import SECTION_SIZE


class Parameter(object):

    def __init__(self, name, offset, default, min_v, max_v, typ, subtyp, size):
        self.name = name
        self.offset = offset
        self.default = default
        self.typ = typ
        self.min = min_v
        self.max = max_v
        self.subtyp = subtyp
        self.size = size


    def __repr__(self):
        tmpl = 'Parameter(name=%r, offset=%r, default=%r, min=%r, max=%r, typ=%r, subtyp=%r, size=%r)'
        data = (self.name, self.offset, self.default, self.min, self.max, self.typ, self.subtyp, self.size)
        return tmpl % data


    def cal_offset(self, previous_offset=None):

        offset = self.offset if self.offset is not None else previous_offset + 1
        assert(offset is not None)

        return offset


    def expand(self, previous_offset=None):

        offset = self.cal_offset(previous_offset)

        if self.typ != 'list':
            return Parameter(self.name, offset, self.default, self.min, self.max, self.typ, self.subtyp, self.size)

        params = []

        for i in range(self.size):
            p = Parameter(self.name, offset + i, self.default, self.min, self.max, self.subtyp, None, 1)
            params.append(p)

        return params


def parse_typ(s):

    if not s.startswith('list'):
        return s, None, 1

    typ = 'list'
    p = re.compile(r'<(.+):(\d+)>')
    m = p.match(s[4:])

    assert(m)

    subtyp = m.group(1)
    size = int(m.group(2))
    return typ, subtyp, size


def parse_number(s, typ):

    if not s:
        return None

    if typ == 'float':
        typ = DSPFloat
    elif typ == 'int':
        typ = int

    v = typ(s)
    return v


def parse_csv(path):

    params = []
    with open(path, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        field2idx = {field: idx for idx, field in enumerate(headers)}

        for row in reader:
            name = row[field2idx['name']]
            typ = row[field2idx['type']]
            typ, subtyp, size = parse_typ(typ)
            v_typ = typ if typ != 'list' else subtyp
            min_v = parse_number(row[field2idx['min']], v_typ)
            max_v = parse_number(row[field2idx['max']], v_typ)
            default = parse_number(row[field2idx['default']], v_typ)
            offset = parse_number(row[field2idx['offset']], int)

            param = Parameter(name, offset, default, min_v, max_v, typ, subtyp, size)
            params.append(param)

    return params


class DSPParameterAccessor(object):

    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        if name == '_data':
            super().__getattr__(name)
        else:
            
            return self._data[name]

    def __setattr__(self, name, value):
        if name == '_data':
            super().__setattr__(name, value)
        else:
            raise NotImplementedError

    def __dir__(self):
        return super().__dir__() + [str(k) for k in self._data.keys()]


def make_dsp_param(param, base_offset, preset=fmbox.presets.current):
    dsp_param = DSPParam(preset, param.offset + base_offset)
    return dsp_param


def make_dsp_param_accessor(params, base_offset, preset=fmbox.presets.current):

    d = {}

    # default offset for first parameter is 0
    previous_offset = -1
    
    for param in params:

        ps = param.expand(previous_offset)

        try:
            iter(ps)
            name = ps[0].name
            dsp_ps = [make_dsp_param(p, base_offset, preset=preset) for p in ps]
            previous_offset = ps[-1].offset
        except TypeError:
            name = ps.name
            dsp_ps = make_dsp_param(ps, base_offset, preset=preset)
            previous_offset = ps.offset

        name = name.replace('-', '_')
        d[name] = dsp_ps

    return DSPParameterAccessor(d)


def csv2pa(filename, base_offset, preset=fmbox.presets.current):

    this_dir, _ = os.path.split(__file__)
    path = os.path.join(this_dir, 'data', filename)
    params = parse_csv(path)
    pa = make_dsp_param_accessor(params, base_offset, preset)
    return pa


def make_op_pa(op_idx, preset=fmbox.presets.current):
    base_offset = SECTION_SIZE * (op_idx + 1)
    return csv2pa('op_params.csv', base_offset, preset)


def make_voice_pa(preset=fmbox.presets.current):
    base_offset = 0
    return csv2pa('voice_params.csv', base_offset, preset)
