import sys
import subprocess as sbp
from mkdesigner.utils import time_stamp, prepare_cmd, call_log

#This script is no longer used

class MvInputFiles(object):

    def __init__(self, args):
        self.args = args
        self.out = args.project

    def run(self):
        print(time_stamp(),
              'Moving input files to the working directory.',
              flush=True)

        cmd1 = 'cp {} {}/ref/'.format(self.args.ref, self.out)
        
        bams = ' '.join(self.args.bam)
        cmd2 = 'cp {} {}/bam/'.format(bams, self.out)

        cmd1 = prepare_cmd(cmd1)
        cmd2 = prepare_cmd(cmd2)

        try:
            sbp.run(cmd1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            print('Error occored at moving input files to the working directory.',flush=True)
            sys.exit(1)

        try:
            sbp.run(cmd2,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            print('Error occored at moving input files to the working directory.',flush=True)
            sys.exit(1)

        print(time_stamp(),
              'Done.',
              flush=True)