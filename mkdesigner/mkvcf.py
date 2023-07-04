#!/usr/bin/env python3

from mkdesigner.params import Params

pm = Params('mkvcf')
args = pm.set_options()


import os
from multiprocessing import Pool
from mkdesigner.utils import time_stamp
from mkdesigner.mvinputfiles import MvInputFiles
from mkdesigner.refindex import RefIndex
from mkdesigner.haplocall import HaploCall
from mkdesigner.mergevcf import MergeVcf

class MKVcf(object):

    def __init__(self, args):
        pm.mkvcf_check_args(args)
        self.args = args
        self.bam = args.bam
        self.N_bam = len(args.bam)
        self.name = args.name
        self.proj = args.project
        self.cpu = args.cpu

    def mkdir(self):
        os.mkdir('{}'.format(self.proj))
        os.mkdir('{}/log'.format(self.proj))
        os.mkdir('{}/ref'.format(self.proj))
        os.mkdir('{}/bam'.format(self.proj))
        os.mkdir('{}/vcf_1st'.format(self.proj))
        os.mkdir('{}/vcf_2nd'.format(self.proj))

    def mvinputfiles(self):
        mi = MvInputFiles(self.args)
        mi.run()

    def refindex(self):
        ri = RefIndex(self.args)
        ri.run()

    def haplocall_1st(self, num):
        hc = HaploCall(self.args, num, False)
        hc.run()

    def mergevcf_1st(self):
        mv = MergeVcf(self.args, False)
        mv.run()

    def haplocall_2nd(self, num):
        hc = HaploCall(self.args, num, True)
        hc.run()

    def mergevcf_2nd(self):
        mv = MergeVcf(self.args, True)
        mv.run()
        
def main():
    print(time_stamp(), 'MKVcf started.', flush=True)

    prog = MKVcf(args)
    prog.mkdir()
    prog.mvinputfiles()
    prog.refindex()
    with Pool(prog.cpu) as p:
        p.map(prog.haplocall_1st, range(prog.N_bam))
    prog.mergevcf_1st()
    with Pool(prog.cpu) as p:
        p.map(prog.haplocall_2nd, range(prog.N_bam))
    prog.mergevcf_2nd()
    
    print(time_stamp(), 'MKVcf successfully finished.\n', flush=True)

if __name__ == '__main__':
    main()
