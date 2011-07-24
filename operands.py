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

def hx(x, size=2):
    fmt = '$%%0%dX' % size
    return fmt % x

class M_ABS(object):
    def __init__(self, **kwargs):
        pass

class M_ABSX(object):
    def __init__(self, **kwargs):
        pass

class M_ABSY(object):
    def __init__(self, **kwargs):
        pass

class M_AC(object):
    def __init__(self, **kwargs):
        pass

    def __eq__(self, other):
        return isinstance(other, M_AC)

    def __repr__(self):
        return "A"

    def __str__(self):
        return ''

class M_XR(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_YR(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_ADDR(object):
    def __init__(self, **kwargs):
        self.addr = kwargs['addr']

    def __repr__(self):
        return hx(self.addr, 4)

class M_AIND(object):
    def __init__(self, **kwargs):
        pass

class M_FC(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_FD(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_FI(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_FV(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_IMM(object):
    def __init__(self, **kwargs):
        self.immed = kwargs['immed']

    def __repr__(self):
        return '#%s' % hx(self.immed)

class M_INDX(object):
    def __init__(self, **kwargs):
        pass

class M_INDY(object):
    def __init__(self, **kwargs):
        pass

class M_NONE(object):
    def __init__(self, **kwargs):
        pass

    def __eq__(self, other):
        return isinstance(other, M_NONE)

    def __repr__(self):
        return ''

class M_PC(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_REL(object):
    def __init__(self, **kwargs):
        self.offset = kwargs['offset']

        if self.offset >= 128:
            self.offset -= 256

    def __repr__(self):
        return '.%+d' % self.offset

class M_SP(object):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return ''

class M_SR(object):
    def __init__(self, **kwargs):
        pass

class M_ZERO(object):
    def __init__(self, **kwargs):
        self.addr = kwargs['addr']

    def __repr__(self):
        return hx(self.addr)

class M_ZERX(object):
    def __init__(self, **kwargs):
        self.addr = kwargs['addr']

    def __repr__(self):
        return hx(self.addr) + ',X'

class M_ZERY(object):
    def __init__(self, **kwargs):
        self.addr = kwargs['addr']

    def __repr__(self):
        return hx(self.addr) + ',Y'

