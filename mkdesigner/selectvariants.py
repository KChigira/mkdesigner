import csv
import sys
import os
from mkdesigner.utils import read_vcf, time_stamp

class SelectVariants(object):
    def __init__(self, args):
        self.args = args
        self.out = args.middir
        self.name1 = args.name1
        self.name2 = args.name2
        self.mindep = args.mindep
        self.maxdep = args.maxdep
        self.target = args.target

        self.refidx = '{}/ref/{}.fai'.format(self.out, os.path.basename(args.ref))
        self.vcf = '{}/vcf/{}'.format(self.out, os.path.basename(args.vcf))
        self.outvcf = '{}/vcf/{}_selected.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])

    def run(self):
        print(time_stamp(),
              'Selecting variants which meet the conditions.',
              flush=True)
        
        #Read input VCF
        vcf_list = read_vcf(self.vcf)
        header = vcf_list[0]
        colnames = vcf_list[1]
        data = vcf_list[2]
        header.append('##selectsnp.py_{}'.format(time_stamp()))

        #Get column numbers of focused varieties.
        id_1 = [] #List of Integer
        id_2 = [] #List of Integer
        try:
            for n in self.name1:
                id_1.append(colnames.index(n))
            for n in self.name2:
                id_2.append(colnames.index(n))
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
        
        #240626 added. 
        #Select variants if target position is designated.
        if self.target is not None:
            self.target_chr = []
            self.target_start = []
            self.target_end = []
            for h in range(len(self.target)):
                tmp = self.target[h].split(':')
                if len(tmp) != 2:
                    print(time_stamp(), 'input of "--target" is invalid.', flush=True)
                    sys.exit(1)
                tmp2 = tmp[1].split('-')
                if len(tmp2) != 2:
                    print(time_stamp(), 'input of "--target" is invalid.', flush=True)
                    sys.exit(1)
                self.target_chr.append(tmp[0])
                self.target_start.append(int(tmp2[0]))
                self.target_end.append(int(tmp2[1]))

        #VCF format: [0]#CHROM, [1]POS, [2]ID, [3]REF, [4]ALT, [5]QUAL, [6]FILTER, [7]INFO, [8]FORMAT	
        #'selected' is list of VCF rows filtered by following conditions.
        selected = []
        for i in range(0,len(data)):
            if self.target is not None:
                flag = 0
                for j in range(len(self.target_chr)):
                    if data[i][0] == self.target_chr[j] and \
                    int(data[i][1]) > self.target_start[j] and \
                    int(data[i][1]) < self.target_end[j]:
                        flag = 1
                if flag == 0: #remove variants which are not target
                    continue
                
            if len(data[i][4].split(',')) > 1:
                continue # remove multi allelic variants
            if self.args.type == 'SNP':
                if abs(len(data[i][3]) - len(data[i][4])) != 0:
                    continue #For SNP marker, remove INDEL.
            elif self.args.type == 'INDEL':
                if abs(len(data[i][3]) - len(data[i][4])) == 0:
                    continue #For INDEL marker, remove SNP.
                if abs(len(data[i][3]) - len(data[i][4])) > 50:
                    continue #INDEL larger than 50bp are removed because they are suspecible.
            if data[i][6] != 'PASS':
                continue # remove low quality variants
            if int(data[i][1]) <= self.args.scope:
                continue # remove variants too close to 5' terminal
            if int(data[i][1]) + self.args.scope > int(chrlens[chrnames.index(data[i][0])]):
                continue # remove variants too close to 3' terminal

            #Check haplotype calling format.
            format = data[i][8].split(':')
            geno_1 = [] #List of haplotype calling data of varities 1
            geno_2 = [] #List of haplotype calling data of varities 2
            for j in id_1:
                geno_1.append(data[i][j].split(':'))
            for j in id_2:
                geno_2.append(data[i][j].split(':'))
            try:
                gt_index = format.index('GT')
                dp_index = format.index('DP')
                gt_1 = [] #List of 'GT' value for varieties 1
                          #(genotype, ex. "0/0""0/1""1/1")
                dp_1 = [] #List of 'DP' value for varieties 1
                          #(depth, integer)
                gt_2 = [] #List of 'GT' value for varieties 2
                dp_2 = [] #List of 'DP' value for varieties 2
                for g in geno_1:
                    gt_1.append(g[gt_index])
                    dp_1.append(int(g[dp_index]))
                for g in geno_2:
                    gt_2.append(g[gt_index])
                    dp_2.append(int(g[dp_index]))
            except (ValueError, IndexError):
                continue #Maybe lack of GT or DP data.
            
            #Check combination of genotypes
            if len(set(gt_1)) != 1 or len(set(gt_2)) != 1 \
                                   or gt_1[0] == gt_2[0]:
                #if genotypes of all varieties_1 are same,
                #length of set(gt_1) == 1 because the set data structure
                #does not allow duplicates.
                continue

            #Check homozygous or not
            gt_1_allele = str(gt_1[0]).split('/')
            gt_2_allele = str(gt_2[0]).split('/')
            try:
                if int(gt_1_allele[0]) != int(gt_1_allele[1]):
                    continue
                if int(gt_2_allele[0]) != int(gt_2_allele[1]):
                    continue
            except ValueError:
                continue #Sometimees haplotype like "./." exist.

            #Check depth
            if not (min(dp_1) >= self.mindep and max(dp_1) <= self.maxdep 
                    and min(dp_2) >= self.mindep and max(dp_2) <= self.maxdep):
                continue

            #Get span where we can design primers 
            chrend = int(chrlens[chrnames.index(data[i][0])]) #230921 modified
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
            writer.writerow(colnames)
            writer.writerows(selected)
        
        print(time_stamp(),
              '{} variants are selected from {} candidates.'.format(len(selected), len(data)),
              flush=True)
        print(time_stamp(),
              'Done.',
              flush=True)

        