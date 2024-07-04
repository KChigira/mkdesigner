import sys
import subprocess as sbp
from mkdesigner.utils import time_stamp, prepare_cmd, call_log


class MergeVcf(object):

    def __init__(self, args, is2nd=False):
        self.args = args
        self.out = args.middir
        self.name = args.name

        if is2nd:
            self.vcfdir = '{}/vcf_2nd/'.format(self.out)
        else: #1st
            self.vcfdir = '{}/vcf_1st/'.format(self.out)

    def run(self):
        print(time_stamp(),
              'Merging vcf files.',
              flush=True)
        
        vcf_all = [self.vcfdir + s + '_filtered_variants.vcf.gz' for s in self.name]
        vcf_con = ' '.join(vcf_all)

        with open('{}sample_names.txt'.format(self.vcfdir), 'w') as o:
            for j in range(len(self.name)):
                o.write('{}\n'.format(self.name[j]))

        cmd1 = 'bcftools merge -o {}Merged_filtered_variants_raw.vcf.gz -O z --force-samples \
                {} \
                >> {}/log/bcftools.log \
                2>&1'.format(self.vcfdir, vcf_con, self.out)
        cmd1_1 = 'bcftools reheader -o {}Merged_filtered_variants.vcf.gz -s {}sample_names.txt \
                {}Merged_filtered_variants_raw.vcf.gz \
                >> {}/log/bcftools.log \
                2>&1'.format(self.vcfdir, self.vcfdir, self.vcfdir, self.out)

        #cmd2 = 'bcftools index {}Merged_filtered_variants.vcf.gz \
        #        >> {}/log/bcftools.log 2>&1'.format(self.vcfdir, self.out)
        cmd2 = 'gatk IndexFeatureFile -I {}Merged_filtered_variants.vcf.gz \
                >> {}/log/gatk.log 2>&1'.format(self.vcfdir, self.out)

        cmd3 = 'gunzip -c {}Merged_filtered_variants.vcf.gz > {}Merged_filtered_variants.vcf'.format(self.vcfdir, self.vcfdir)

        cmd1 = prepare_cmd(cmd1)
        cmd1_1 = prepare_cmd(cmd1_1)
        cmd2 = prepare_cmd(cmd2)
        cmd3 = prepare_cmd(cmd3)

        try:
            sbp.run(cmd1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bcftools', cmd1)
            sys.exit(1)

        try:
            sbp.run(cmd1_1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bcftools', cmd1_1)
            sys.exit(1)

        try:
            sbp.run(cmd2,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'gatk', cmd2)
            sys.exit(1)

        try:
            sbp.run(cmd3,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'gunzip', cmd3)
            sys.exit(1)

        print(time_stamp(),
              'Done.',
              flush=True)

