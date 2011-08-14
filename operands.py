# Copyright (c) 2011, Gabriele Favalessa
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

class RegisterBase(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return self.name

    def __str__(self):
        return ''

    def __eq__(self, other):
        return isinstance(other, RegisterBase) and self.name == other.name

class M_AC(RegisterBase):
    name = 'A'

class M_XR(RegisterBase):
    name = 'X'

class M_YR(RegisterBase):
    name = 'Y'

class M_PC(RegisterBase):
    name = 'PC'

class M_SP(RegisterBase):
    name = 'SP'

class M_SR(RegisterBase):
    name = 'SR'

class FlagBase(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return self.name

    def __str__(self):
        return ''

class M_FC(FlagBase):
    name = 'C'

class M_FD(FlagBase):
    name = 'D'

class M_FI(FlagBase):
    name = 'I'

class M_FV(FlagBase):
    name = 'V'

class M_IMM(object):
    def __init__(self, **kwargs):
        self.immed = kwargs['immed']

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '#$%02X' % self.immed

class M_INDX(object):
    def __init__(self, **kwargs):
        self.offset = kwargs['offset']

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '($%02X, X)' % self.offset

class M_INDY(object):
    def __init__(self, **kwargs):
        self.offset = kwargs['offset']

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '($%02X),Y' % self.offset

class M_NONE(object):
    def __init__(self, **kwargs):
        pass

    def __eq__(self, other):
        return isinstance(other, M_NONE)

    def __repr__(self):
        return '_'

    def __str__(self):
        return ''

class M_REL(object):
    def __init__(self, **kwargs):
        self.offset = kwargs['offset']

        if self.offset >= 128:
            self.offset -= 256

    def __repr__(self):
        return '.%+d' % self.offset

    def to_string(self, addr, memory):
        addr += self.offset + 2
        return memory.addr_label(addr)

class AddrBase(object):
    def __init__(self, **kwargs):
        self.addr = kwargs['addr']

    def __repr__(self):
        fmt = '$%%0%dX' % self.size

        return fmt % self.addr

    def to_string(self, addr, memory):
        return memory.addr_label(self.addr, size=self.size)

class M_ABS(AddrBase):
    size = 4

class M_ABSX(AddrBase):
    size = 4

    def __repr__(self):
        s = super(M_ABSX, self).__repr__()

        return s + ',X'

    def to_string(self, addr, memory):
        s = super(M_ABSX, self).to_string(addr, memory)

        return s + ',X'

class M_ABSY(AddrBase):
    size = 4

    def __repr__(self):
        s = super(M_ABSY, self).__repr__()

        return s + ',Y'

    def to_string(self, addr, memory):
        s = super(M_ABSY, self).to_string(addr, memory)

        return s + ',Y'

class M_ADDR(AddrBase):
    size = 4

class M_ZERO(AddrBase):
    size = 2

class M_ZERX(AddrBase):
    size = 2

    def to_string(self, addr, memory):
        return super(M_ZERX, self).to_string(addr, memory) + ',X'

class M_ZERY(AddrBase):
    size = 2

    def to_string(self, addr, memory):
        return super(M_ZERY, self).to_string(addr, memory) + ',Y'

class M_AIND(AddrBase):
    """JMP ($00A2)"""
    size = 4

    def to_string(self, addr, memory):
        return '(%s)' % super(M_AIND, self).to_string(addr, memory)
