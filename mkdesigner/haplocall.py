import sys
import os
import subprocess as sbp
from mkdesigner.utils import time_stamp, prepare_cmd, call_log


class HaploCall(object):

    def __init__(self, args, num, is2nd=False):
        self.args = args
        self.out = args.middir
        self.name = args.name[num]
        self.is2nd = is2nd

        self.ref = '{}/ref/{}'.format(self.out, os.path.basename(args.ref))
        #self.bam = '{}/bam/{}'.format(self.out, os.path.basename(args.bam[num]))
        #230821 modified not to copy bam file.
        self.bam = args.bam[num]

        if is2nd:
            self.vcfdir = '{}/vcf_2nd/{}'.format(self.out, self.name)
        else: #1st
            self.vcfdir = '{}/vcf_1st/{}'.format(self.out, self.name)

    def run(self):
        if self.is2nd:
            print(time_stamp(),
                '2nd haplotype calling for "{}".'.format(self.name),
                flush=True)

            cmd1 = ':'

            cmd2 = 'gatk HaplotypeCaller \
                    -R {} -I {} -O {}_raw_variants.vcf \
                    --alleles {}/vcf_1st/Merged_filtered_variants_too_large_indel_removed.vcf \
                    >> {}/log/gatk.log 2>&1'.format(self.ref, self.bam, self.vcfdir, self.out, self.out)
        else: #1st
            print(time_stamp(),
                '1st haplotype calling for "{}".'.format(self.name),
                flush=True)

            cmd1 = 'samtools index {} \
                    >> {}/log/samtools.log \
                    2>&1'.format(self.bam, self.out)
            
            cmd2 = 'gatk HaplotypeCaller \
                    -R {} -I {} -O {}_raw_variants.vcf \
                    >> {}/log/gatk.log 2>&1'.format(self.ref, self.bam, self.vcfdir, self.out)

        cmd3 = 'gatk SelectVariants \
                -R {} -V {}_raw_variants.vcf \
                -select-type SNP \
                -O {}_raw_snps.vcf \
                >> {}/log/gatk.log 2>&1'.format(self.ref, self.vcfdir, self.vcfdir, self.out)

        cmd4 = 'gatk SelectVariants \
                -R {} -V {}_raw_variants.vcf \
                -select-type INDEL \
                -O {}_raw_indels.vcf \
                >> {}/log/gatk.log 2>&1'.format(self.ref, self.vcfdir, self.vcfdir, self.out)

        cmd5 = 'gatk VariantFiltration \
                -R {} -V {}_raw_snps.vcf \
                -O {}_filtered_snps.vcf \
                -filter-name "QD_filter" -filter "QD < 20.0" \
                -filter-name "FS_filter" -filter "FS > 60.0" \
                -filter-name "MQ_filter" -filter "MQ < 40.0" \
                -filter-name "SOR_filter" -filter "SOR > 4.0" \
                -filter-name "MQRankSum_filter" -filter "MQRankSum < -12.5" \
                -filter-name "ReadPosRankSum_filter" -filter "ReadPosRankSum < -8.0" \
                >> {}/log/gatk.log 2>&1'.format(self.ref, self.vcfdir, self.vcfdir, self.out)

        cmd6 = 'gatk VariantFiltration \
                -R {} -V {}_raw_indels.vcf \
                -O {}_filtered_indels.vcf \
                -filter-name "QD_filter" -filter "QD < 20.0" \
                -filter-name "FS_filter" -filter "FS > 200.0" \
                -filter-name "SOR_filter" -filter "SOR > 10.0" \
                >> {}/log/gatk.log 2>&1'.format(self.ref, self.vcfdir, self.vcfdir, self.out)

        cmd7 = 'bgzip -c {}_filtered_snps.vcf \
                > {}_filtered_snps.vcf.gz'.format(self.vcfdir, self.vcfdir)

        cmd8 = 'bcftools index {}_filtered_snps.vcf.gz \
                >> {}/log/bcftools.log 2>&1'.format(self.vcfdir, self.out)

        cmd9 = 'bgzip -c {}_filtered_indels.vcf \
                > {}_filtered_indels.vcf.gz'.format(self.vcfdir, self.vcfdir)

        cmd10 = 'bcftools index {}_filtered_indels.vcf.gz \
                 >> {}/log/bcftools.log 2>&1'.format(self.vcfdir, self.out)

        cmd11 = 'bcftools concat -o {}_filtered_variants.vcf.gz \
                 -a -O z \
                 {}_filtered_snps.vcf.gz \
                 {}_filtered_indels.vcf.gz \
                 >> {}/log/bcftools.log 2>&1'.format(self.vcfdir, self.vcfdir, self.vcfdir, self.out)

        cmd12 = 'bcftools index {}_filtered_variants.vcf.gz \
                 >> {}/log/bcftools.log 2>&1'.format(self.vcfdir, self.out)

        cmd1 = prepare_cmd(cmd1)
        cmd2 = prepare_cmd(cmd2)
        cmd3 = prepare_cmd(cmd3)
        cmd4 = prepare_cmd(cmd4)
        cmd5 = prepare_cmd(cmd5)
        cmd6 = prepare_cmd(cmd6)
        cmd7 = prepare_cmd(cmd7)
        cmd8 = prepare_cmd(cmd8)
        cmd9 = prepare_cmd(cmd9)
        cmd10 = prepare_cmd(cmd10)
        cmd11 = prepare_cmd(cmd11)
        cmd12 = prepare_cmd(cmd12)

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
            call_log(self.out, 'gatk', cmd2)
            sys.exit(1)
        try:
            sbp.run(cmd3,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'gatk', cmd3)
            sys.exit(1)

        try:
            sbp.run(cmd4,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'gatk', cmd4)
            sys.exit(1)

        try:
            sbp.run(cmd5,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'gatk', cmd5)
            sys.exit(1)

        try:
            sbp.run(cmd6,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'gatk', cmd6)
            sys.exit(1)

        try:
            sbp.run(cmd7,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bgzip', cmd7)
            sys.exit(1)

        try:
            sbp.run(cmd8,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bcftools', cmd8)
            sys.exit(1)

        try:
            sbp.run(cmd9,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bgzip', cmd9)
            sys.exit(1)

        try:
            sbp.run(cmd10,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bcftools', cmd10)
            sys.exit(1)

        try:
            sbp.run(cmd11,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bcftools', cmd11)
            sys.exit(1)

        try:
            sbp.run(cmd12,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'bcftools', cmd12)
            sys.exit(1)


        print(time_stamp(),
              'Done ({}).'.format(self.name),
              flush=True)
