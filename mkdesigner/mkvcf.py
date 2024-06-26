#!/usr/bin/env python3

import sys
from mkdesigner.params import Params

pm = Params('mkvcf')
args = pm.set_options()


import os
from multiprocessing import Pool
from mkdesigner.utils import prepare_cmd, time_stamp
from mkdesigner.refindex import RefIndex
from mkdesigner.haplocall import HaploCall
from mkdesigner.mergevcf import MergeVcf
#230826 inserted
from mkdesigner.removetoolargeindel import RemoveTooLargeIndel
import subprocess as sbp

class MKVcf(object):

    def __init__(self, args):
        pm.mkvcf_check_args(args)
        self.args = args
        self.ref = args.ref
        self.bam = args.bam
        self.N_bam = len(args.bam)
        self.name = args.name
        self.cpu = args.cpu

        #240626 modified
        #devided output directory to {output}_mkvcf/ and {output}_mkvcf/intermediate/ 
        self.stem = args.output
        self.dir = '{}_mkvcf'.format(self.stem)
        self.middir = '{}_mkvcf/intermediate'.format(self.stem)

    def mkdir(self):
        os.mkdir('{}'.format(self.dir))
        os.mkdir('{}'.format(self.middir))
        os.mkdir('{}/log'.format(self.middir))
        os.mkdir('{}/ref'.format(self.middir))
        #230821 modified not to copy bam files.
        #os.mkdir('{}/bam'.format(self.proj))
        os.mkdir('{}/vcf_1st'.format(self.middir))
        os.mkdir('{}/vcf_2nd'.format(self.middir))

    def command(self):
        #Output command info
        command = ' '.join(sys.argv)
        fn = '{}/command.txt'.format(self.dir)
        with open(fn, 'w') as f:
            f.write('{}\n'.format(command))

    def mvinputfiles(self):
        cmd1 = 'cp {} {}/ref/'.format(self.args.ref, self.middir)
        cmd1 = prepare_cmd(cmd1)
        try:
            sbp.run(cmd1, stdout=sbp.DEVNULL, stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            print('Error occored at moving input files to the working directory.',flush=True)
            sys.exit(1)

    def refindex(self):
        ri = RefIndex(self)
        ri.run()

    def haplocall_1st(self, num):
        hc = HaploCall(self, num, False)
        hc.run()

    def mergevcf_1st(self):
        mv = MergeVcf(self, False)
        mv.run()

    def remove_too_large_indel(self):
        rt = RemoveTooLargeIndel(self)
        rt.run()
        #Removing indels larger than 100 bp to avoid errors.

    def haplocall_2nd(self, num):
        hc = HaploCall(self, num, True)
        hc.run()

    def mergevcf_2nd(self):
        mv = MergeVcf(self, True)
        mv.run()

    def mvoutputfiles(self):
        cmd1 = 'cp {}/vcf_2nd/Merged_filtered_variants.vcf {}/{}_ready_for_mkprimer.vcf'.format(self.middir, self.dir, self.stem)
        cmd1 = prepare_cmd(cmd1)
        try:
            sbp.run(cmd1, stdout=sbp.DEVNULL, stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            print('Error occored at moving output files.',flush=True)
            sys.exit(1)

def main():
    print(time_stamp(), 'MKVcf started.', flush=True)

    prog = MKVcf(args)
    prog.mkdir()
    prog.command()
    prog.mvinputfiles()
    prog.refindex()
    with Pool(prog.cpu) as p:
        p.map(prog.haplocall_1st, range(prog.N_bam))
    prog.mergevcf_1st()
    prog.remove_too_large_indel()
    with Pool(prog.cpu) as p:
        p.map(prog.haplocall_2nd, range(prog.N_bam))
    prog.mergevcf_2nd()
    prog.mvoutputfiles()
    
    print(time_stamp(), 'MKVcf successfully finished.\n', flush=True)

if __name__ == '__main__':
    main()
