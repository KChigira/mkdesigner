import csv
import subprocess as sbp
import sys
from mkdesigner.utils import call_log, prepare_cmd, read_vcf, time_stamp

class RemoveTooLargeIndel(object):
    def __init__(self, args):
        self.args = args
        self.out = args.middir
        self.vcf = '{}/vcf_1st/Merged_filtered_variants.vcf'.format(self.out)
        self.outvcf = '{}/vcf_1st/Merged_filtered_variants_too_large_indel_removed.vcf'.format(self.out)
        
        self.maxsize = 100

    def run(self):
        print(time_stamp(),
              'Removing too large indels.',
              flush=True)
        
        #Read input VCF
        vcf_list = read_vcf(self.vcf)
        header = vcf_list[0]
        colnames = vcf_list[1]
        data = vcf_list[2]


        #VCF format: [0]#CHROM, [1]POS, [2]ID, [3]REF, [4]ALT, [5]QUAL, [6]FILTER, [7]INFO, [8]FORMAT	
        #'selected' is list of VCF rows filtered by following conditions.
        selected = []
        for i in range(0,len(data)):
            flag = 0
            ref = data[i][3].split(',')
            alt = data[i][4].split(',')
            for j in range(0,len(ref)):
                if len(ref[j]) > self.maxsize:
                    flag = 1
            for j in range(0,len(alt)):
                if len(alt[j]) > self.maxsize:
                    flag = 1
            if flag == 1:
                continue

            selected.append(data[i])

        with open(self.outvcf, 'w') as o:
            for h in header:
                o.write('{}\n'.format(h))
            writer = csv.writer(o, delimiter='\t')
            writer.writerow(colnames)
            writer.writerows(selected)
        
        cmd1 = 'gatk IndexFeatureFile -I {} \
                >> {}/log/gatk.log 2>&1'.format(self.outvcf, self.out)
        cmd1 = prepare_cmd(cmd1)
        try:
            sbp.run(cmd1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'gatk', cmd1)
            sys.exit(1)

        print(time_stamp(),
              '{} variants are selected from {} candidates.'.format(len(selected), len(data)),
              flush=True)
        print(time_stamp(),
              'Done.',
              flush=True)

        
