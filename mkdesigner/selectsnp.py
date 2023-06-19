import csv
import sys
import os
from mkdesigner.utils import read_vcf, time_stamp

class SelectSnp(object):
    def __init__(self, args):
        self.args = args
        self.out = args.project
        self.name1 = args.name1
        self.name2 = args.name2
        self.mindep = args.mindep
        self.maxdep = args.maxdep

        self.refidx = '{}/ref/{}.fai'.format(self.out, os.path.basename(args.ref))
        self.vcf = '{}/vcf/{}'.format(self.out, os.path.basename(args.vcf))
        self.outvcf = '{}/vcf/{}_selected.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])

    def run(self):
        print(time_stamp(),
              'Selecting SNPs that meet the conditions.',
              flush=True)
        
        #Read input VCF
        vcf_list = read_vcf(self.vcf)
        header = vcf_list[0]
        colnames = vcf_list[1]
        data = vcf_list[2]
        header.append('##selectsnp.py_{}'.format(time_stamp()))

        try:
            id_1 = colnames.index(self.name1)
            id_2 = colnames.index(self.name2)
        except ValueError:
            print(time_stamp(), '!!ERROR!! Specified line does not exist in the VCF file\n', flush=True)
            sys.exit(1)

        #Read input reference fasta.fai
        chrnames = []
        chrlens = []
        with open(self.refidx, 'r') as r:
            reader = csv.reader(r, delimiter='\t')
            for row in reader:
                chrnames.append(row[0])
                chrlens.append(row[1])

        #VCF format: [0]#CHROM, [1]POS, [2]ID, [3]REF, [4]ALT, [5]QUAL, [6]FILTER, [7]INFO, [8]FORMAT	
        selected = []
        for i in range(0,len(data)):
            if len(data[i][4].split(',')) > 1:
                continue # remove multi allelic variants
            if len(data[i][3]) > 1 or len(data[i][4]) > 1:
                continue # remove InDels
            if data[i][6] != 'PASS':
                continue # remove low quality variants
            if int(data[i][1]) <= self.args.search_span:
                continue # remove variants too close to 5' terminal
            if int(data[i][1]) + self.args.search_span > int(chrlens[chrnames.index(data[i][0])]):
                continue # remove variants too close to 3' terminal

            format = data[i][8].split(':')
            geno_1 = data[i][id_1].split(':')
            geno_2 = data[i][id_2].split(':')

            try:
                gt_index = format.index('GT')
                dp_index = format.index('DP')
                gt = [geno_1[gt_index], geno_2[gt_index]]
                dp = [int(geno_1[dp_index]), int(geno_2[dp_index])]
            except ValueError:
                continue
            
            if not ((gt == ['0/0', '1/1'] or gt == ['1/1', '0/0']) and (dp[0] >= self.mindep and dp[0] <= self.maxdep) and (dp[1] >= self.mindep and dp[1] <= self.maxdep)):
                continue # remove variants which are not allelic between 2 lines

            #Get span where we can design primers 
            chrend = chrlens[chrnames.index(data[i][0])]
            if i == 0:
                chr_3 = ['', data[i][0], data[i+1][0]]
            elif i == len(data) - 1:
                chr_3 = [data[i-1][0], data[i][0], '']
            else:
                chr_3 = [data[i-1][0], data[i][0], data[i+1][0]]

            if chr_3[0] != chr_3[1] and chr_3[1] == chr_3[2]:
                pos_3 = [0, int(data[i][1]), int(data[i+1][1])]
            elif chr_3[0] == chr_3[1] and chr_3[1] != chr_3[2]:
                pos_3 = [int(data[i-1][1]), int(data[i][1]), chrend]
            elif chr_3[0] != chr_3[1] and chr_3[1] != chr_3[2]:
                pos_3 = [0, int(data[i][1]), chrend]
            else:
                pos_3 = [int(data[i-1][1]), int(data[i][1]), int(data[i+1][1])]

            data[i][7] = '{};SPAN={},{}'.format(data[i][7], pos_3[1]-pos_3[0], pos_3[2]-pos_3[1])

            selected.append(data[i])

        with open(self.outvcf, 'w') as o:
            for h in header:
                o.write('{}\n'.format(h))
            writer = csv.writer(o, delimiter='\t')
            #writer.writerows(header)
            writer.writerow(colnames)
            writer.writerows(selected)
        
        print(time_stamp(),
              '{} variants are selected from {} candidates.'.format(len(selected), len(data)),
              flush=True)
        print(time_stamp(),
              'Done.',
              flush=True)

        