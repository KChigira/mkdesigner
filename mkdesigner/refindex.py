import sys
import os
import subprocess as sbp
from mkdesigner.utils import time_stamp, prepare_cmd, call_log


class RefIndex(object):

    def __init__(self, args):
        self.args = args
        self.out = args.middir
        self.ref = '{}/ref/{}'.format(self.out, os.path.basename(args.ref))

    def run(self):
        print(time_stamp(),
              'Indexing reference fasta.',
              flush=True)

        cmd1 = 'samtools faidx {} \
                >> {}/log/samtools.log \
                2>&1'.format(self.ref, self.out)
        
        cmd2 = 'picard CreateSequenceDictionary R={} \
                >> {}/log/picard.log \
                2>&1'.format(self.ref, self.out)

        cmd1 = prepare_cmd(cmd1)
        cmd2 = prepare_cmd(cmd2)

        try:
            sbp.run(cmd1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'samtools', cmd1)
            sys.exit(1)

        try:
            sbp.run(cmd2,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'picard', cmd2)
            sys.exit(1)

        print(time_stamp(),
              'Done.',
              flush=True)