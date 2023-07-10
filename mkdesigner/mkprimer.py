#!/usr/bin/env python3

from mkdesigner.addprimertovcf import AddPrimerToVcf
from mkdesigner.params import Params
from mkdesigner.refindex import RefIndex
from mkdesigner.selectvariants import SelectVariants

pm = Params('mkprimer')
args = pm.set_options()

import os
import sys
import subprocess as sbp
from mkdesigner.utils import time_stamp, prepare_cmd

class MKPrimer(object):
    def __init__(self, args):
        pm.mkprimer_check_args(args)
        self.args = args
        self.ref = args.ref
        self.vcf = args.vcf
        self.name1 = args.name1
        self.name2 = args.name2
        self.type = args.type
        self.proj = args.project
        self.cpu = args.cpu

    def mkdir(self):
        os.mkdir('{}'.format(self.proj))
        os.mkdir('{}/log'.format(self.proj))
        os.mkdir('{}/ref'.format(self.proj))
        os.mkdir('{}/vcf'.format(self.proj))
        os.mkdir('{}/intermediate'.format(self.proj))

    def mvinputfiles(self):
        cmd1 = 'cp {} {}/ref/'.format(self.ref, self.proj)
        cmd2 = 'cp {} {}/vcf/'.format(self.vcf, self.proj)
        cmd1 = prepare_cmd(cmd1)
        cmd2 = prepare_cmd(cmd2)
        try:
            sbp.run(cmd1, stdout=sbp.DEVNULL, stderr=sbp.DEVNULL,
                    shell=True, check=True)
            sbp.run(cmd2, stdout=sbp.DEVNULL, stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            print('Error occored at moving input files to the working directory.',flush=True)
            sys.exit(1)

    def refindex(self):
        ri = RefIndex(self.args)
        ri.run()

    def selectvariants(self):
        ss = SelectVariants(self.args)
        ss.run()

    def addprimertovcf(self):
        ad = AddPrimerToVcf(self.args)
        ad.run()

def main():
    print(time_stamp(), 'MKPrimer started.', flush=True)

    prog = MKPrimer(args)
    prog.mkdir()
    prog.mvinputfiles()
    prog.refindex()
    prog.selectvariants()
    prog.addprimertovcf()
    
    print(time_stamp(), 'MKPrimer successfully finished.\n', flush=True)

if __name__ == '__main__':
    main()
    