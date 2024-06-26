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
        self.target = args.target
        self.cpu = args.cpu
        self.mindep = args.mindep
        self.maxdep = args.maxdep
        self.scope = args.search_span
        self.margin = args.margin
        self.primer_min_size = args.primer_min_size

        #240626 modified
        #devided output directory to {output}_mkprimer/ and {output}_mkprimer/intermediate/ 
        self.stem = args.output
        self.dir = '{}_mkprimer'.format(self.stem)
        self.middir = '{}_mkprimer/intermediate'.format(self.stem)

    def mkdir(self):
        os.mkdir('{}'.format(self.dir))
        os.mkdir('{}'.format(self.middir))
        os.mkdir('{}/log'.format(self.middir))
        os.mkdir('{}/ref'.format(self.middir))
        os.mkdir('{}/vcf'.format(self.middir))
        os.mkdir('{}/intermediate'.format(self.middir))

    def command(self):
        #Output command info
        command = ' '.join(sys.argv)
        fn = '{}/command.txt'.format(self.dir)
        with open(fn, 'w') as f:
            f.write('{}\n'.format(command))

    def mvinputfiles(self):
        cmd1 = 'cp {} {}/ref/'.format(self.ref, self.middir)
        cmd2 = 'cp {} {}/vcf/'.format(self.vcf, self.middir)
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
        ri = RefIndex(self)
        ri.run()

    def selectvariants(self):
        ss = SelectVariants(self)
        ss.run()

    def addprimertovcf(self):
        ad = AddPrimerToVcf(self)
        ad.run()

    def mvoutputfiles(self):
        output_vcf = '{}/vcf/{}_selected_primer_added.vcf'.format(self.middir, os.path.splitext(os.path.basename(self.vcf))[0])
        output_fai = '{}/ref/{}.fai'.format(self.middir, os.path.basename(self.ref))
        cmd1 = 'cp {} {}/{}_primer_added.vcf'.format(output_vcf, self.dir, self.stem)
        cmd2 = 'cp {} {}/for_draw.fai'.format(output_fai, self.dir)
        cmd1 = prepare_cmd(cmd1)
        cmd2 = prepare_cmd(cmd2)
        try:
            sbp.run(cmd1, stdout=sbp.DEVNULL, stderr=sbp.DEVNULL,
                    shell=True, check=True)
            sbp.run(cmd2, stdout=sbp.DEVNULL, stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            print('Error occored at moving output files.',flush=True)
            sys.exit(1)

def main():
    print(time_stamp(), 'MKPrimer started.', flush=True)

    prog = MKPrimer(args)
    prog.mkdir()
    prog.command()
    prog.mvinputfiles()
    prog.refindex()
    prog.selectvariants()
    prog.addprimertovcf()
    prog.mvoutputfiles()
    
    print(time_stamp(), 'MKPrimer successfully finished.\n', flush=True)

if __name__ == '__main__':
    main()
    