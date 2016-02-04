import random
from common import *

class test_a64_cbnz(TemplateTest):
    
    def gen_rand(self):
        regs = list(set(GPREGS) - {'x0', 'w0'})
        while True:
            yield {'insn' : random.choice(['cbz', 'cbnz']),
                   'reg'  : random.choice(regs),
                   'val'  : random.randint(0,1),
                   'label_idx': random.randint(0, self.__label_count - 1)}

    def __init__(self):
        self.__label_count = 8
        self.symbols = [ __name__ + '_addr_' + str(i) for i in xrange(self.__label_count) ]
        randvals = random.sample(xrange(0, 0xfffffffffffffff), 2*self.__label_count)
        self.branch = randvals[:self.__label_count]
        self.nobranch = randvals[self.__label_count:]

    def test_begin(self):
        yield '    .arch armv8-a'
        yield '    .align 2'
        yield '    .text'
        for i in xrange(0, len(self.symbols), 2):
            yield self.symbols[i] + ':'
            yield '    ldr\t\tx0, ={0}'.format(hex(self.branch[i]))
            yield '    ret'
            yield '    .skip %d' % random.randrange(512, 2048, 4)

    def gen_testcase(self, nr, insn, reg, val, label_idx):
        label = self.symbols[label_idx]
        ret_label = self.testcase_name(nr) + '_ret'
        if val != 0:
            val = random.randint(1,0xffffffff)
        state = ProcessorState(setreg={reg:val,
                                       'x0':self.nobranch[label_idx],
                                       'x30':ret_label},
                                       reserve=['x0'])        
        yield state.prepare()
        space = '\t' if insn == 'cbnz' else '\t\t'
        yield self.testcase_insn(nr, '{insn}{space}{reg}, {label}'.format(**locals()))
        yield ret_label + ':'
        if (insn == 'cbz' and val == 0) or (insn == 'cbnz' and val != 0):
            yield '    // should jump'
            x0 = self.branch[label_idx]
        else:
            yield '    // shouldn\'t jump'
            x0 = self.nobranch[label_idx]
        yield state.check({'x0':x0})
        yield state.restore()
        
    def test_end(self):
        for i in xrange(1, len(self.symbols), 2):
            yield '    .skip %d' % random.randrange(512, 2048, 4)
            yield self.symbols[i] + ':'
            yield '    ldr\t\tx0, ={0}'.format(hex(self.branch[i]))
            yield '    ret'
