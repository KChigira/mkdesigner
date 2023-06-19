#!/usr/bin/env python3

import csv
import os
import pandas as pd
import sys
import subprocess as sbp
from mkdesigner.utils import read_vcf, time_stamp, prepare_cmd
from mkdesigner.params import Params

pm = Params('mkselect')
args = pm.set_options()

class MKSelect(object):
    def __init__(self, args):
        self.args = args
        self.vcf = args.vcf
        self.fai = args.fai
        self.num_marker = args.num_marker
        self.target = args.target
        self.mindif = args.mindif
        self.maxdif = args.maxdif

        #VCF data
        self.header = [] #VCF header
        self.colnames = [] #VCF colnames
        self.data = [] #VCF content
        self.data_s = [] #VCF content selected
        self.primers = [] #Primer information of selected variants
        self.out_table = [] #Output table, easy to read

    def readvcf(self):
        #Read input VCF
        vcf_list = read_vcf(self.vcf)
        self.header = vcf_list[0]
        self.colnames = vcf_list[1]
        self.data = vcf_list[2]
        self.header.append('##mkselect.py_{},num_primer={},target={}'.format(time_stamp(), self.num_marker, self.target))
        self.data = pd.DataFrame(self.data, columns=self.colnames)

    '''    
    def readfai(self):
        #Import data from fasta index file
        fai_list = []
        with open(self.fai, 'r') as v:
            reader = csv.reader(v, delimiter='\t')
            for row in reader:
                fai_list.append(row)
        self.df_fai = pd.DataFrame(fai_list, columns=['chr','len','2','3','4'])
    '''

    def filtervcf(self):
        #Select variants FILTER = PASS_P
        self.data_s = self.data[self.data['FILTER'] == 'PASS_P']
        if self.target != '':
            tmp = self.target.split(':')
            if len(tmp) != 2:
                print(time_stamp(), 'input of "--target" is invalid.', flush=True)
                sys.exit(1)
            tmp2 = tmp[1].split('-')
            if len(tmp2) != 2:
                print(time_stamp(), 'input of "--target" is invalid.', flush=True)
                sys.exit(1)
            target_chr = tmp[0]
            target_start = int(tmp2[0])
            target_end = int(tmp2[1])
            self.data_s = self.data_s[self.data_s['#CHROM'] == target_chr and
                            self.data_s['POS'] > target_start and
                            self.data_s['POS'] < target_end]

        #Decrease markers to a specified number (-n)
        while self.num_marker < len(self.data_s):
            intervals = [10**20] #use 10**20 as insted of infinity
            current_chr = self.data_s.at[self.data_s.index[0], '#CHROM']
            for i in range(len(self.data_s) - 1):
                if self.data_s.at[self.data_s.index[i], '#CHROM'] != current_chr:
                    intervals.append(10**20) #use 10**20 as instead of infinity
                else:
                    interval = (int(self.data_s.at[self.data_s.index[i+1],'POS']) - int(self.data_s.at[self.data_s.index[i], 'POS']))
                    intervals.append(interval)
            intervals.append(10**20) #length of list is len(data_s) + 1
            #data_s       0   1   2   3   4   5
            #intervals  0   1   2   3   4   5   6 #[0] and [6] are infinity
            shortest = intervals.index(min(intervals))
            if intervals[shortest - 1] < intervals[shortest + 1]:
                remove_index = shortest - 1
            else:
                remove_index = shortest - 1
            self.data_s = self.data_s.drop(self.data_s.index[remove_index])

        #Correct infomation of primers
        primers_list = []
        for i in range(len(self.data_s)):
            info = str(self.data_s.at[self.data_s.index[i], 'INFO'])
            info_spl = info.split(';')
            for j in range(len(info_spl)):
                elem = info_spl[j].split('=')
                if elem[0] == 'PRIMER':
                    pri = elem[1].split('|')
                    primers_list.append(pri)
        primers_col = ['name','num','chr','L_seq','R_seq','L_pos','R_pos','L_TM','R_TM','product_size']
        self.primers = pd.DataFrame(primers_list, columns=primers_col)

    def maketable(self):
        name_line = self.data_s.columns[9:]
        out_table_col = ['Chr','Pos','ID','Left','Right','L_TM','R_TM']
        for str_n in name_line:
            out_table_col.append('{}_Size'.format(str_n))

        out_list = []
        for i in range(len(self.data_s)):
            out_row = []
            out_row.append(self.data_s.at[self.data_s.index[i], '#CHROM'])
            out_row.append(self.data_s.at[self.data_s.index[i], 'POS'])
            out_row.append(self.primers.at[self.primers.index[i], 'name'])
            out_row.append(self.primers.at[self.primers.index[i], 'L_seq'])
            out_row.append(self.primers.at[self.primers.index[i], 'R_seq'])
            out_row.append(self.primers.at[self.primers.index[i], 'L_TM'])
            out_row.append(self.primers.at[self.primers.index[i], 'R_TM'])
            for line in name_line:
                line_info = self.data_s.at[self.data_s.index[i], line]
                #ex. 1/1:0,6:6:18:270,18,0
                if line_info[0:3] == '0/0':
                    out_row.append(self.primers.at[self.primers.index[i], 'product_size'])
                elif line_info[0:3] == '1/1':
                    size = (int(self.primers.at[self.primers.index[i], 'product_size']) +
                            len(self.data_s.at[self.data_s.index[i], 'ALT']) - 
                            len(self.data_s.at[self.data_s.index[i], 'REF']))
                    out_row.append(size)
            out_list.append(out_row)
        self.out_table = pd.DataFrame(out_list, columns=out_table_col)

    def output(self):
        #1. output VCF
        out_vcf_name = str(self.vcf).replace('.vcf', '_{}mk_selected_{}.vcf'.format(self.num_marker, self.target))
        with open(out_vcf_name, 'w') as o:
            for h in self.header:
                o.write('{}\n'.format(h))
            writer = csv.writer(o, delimiter='\t')
            writer.writerow(self.colnames)

        out_vcf_name_tmp = '{}.tmp'.format(out_vcf_name)
        self.data_s.to_csv(out_vcf_name_tmp, sep='\t', header=False, index=False)
        cmd1 = 'cat {} >> {}'.format(out_vcf_name_tmp, out_vcf_name)
        cmd2 = 'rm {}'.format(out_vcf_name_tmp)
        cmd1 = prepare_cmd(cmd1)
        cmd2 = prepare_cmd(cmd2)
        try:
            sbp.run(cmd1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True, check=True)
            sbp.run(cmd2,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            print(time_stamp(),
              'Error occured writing vcf data.',
              flush=True)
            sys.exit(1) 

        #2. output primer data
        out_table_name = str(self.vcf).replace('.vcf', '_{}mk_selected_{}.txt'.format(self.num_marker, self.target))
        self.out_table.to_csv(out_table_name, sep='\t', header=True, index=False)

        print(time_stamp(), '{} markers were selected.\n'.format(len(self.data_s)), flush=True)

    def draw(self):
        out_vcf_name = str(self.vcf).replace('.vcf', '_{}mk_selected_{}.vcf'.format(self.num_marker, self.target))
        out_png_name = str(self.vcf).replace('.vcf', '_{}mk_selected_{}.png'.format(self.num_marker, self.target))
        path = os.path.dirname(os.path.abspath(__file__))
        print(out_vcf_name)
        print(out_png_name)
        print(path)
        cmd1 = 'Rscript {}/visualize_marker.R {} {} {}'.format(path, out_vcf_name, self.fai, out_png_name)
        cmd1 = prepare_cmd(cmd1)
        try:
            sbp.run(cmd1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            print(time_stamp(),
              'Error occured drawing marker position.',
              flush=True)
            sys.exit(1) 
        

def main():
    print(time_stamp(), 'MKSelect started.', flush=True)

    prog = MKSelect(args)
    prog.readvcf()
    prog.filtervcf()
    prog.maketable()
    prog.output()
    prog.draw()

    print(time_stamp(), 'MKSelect successfully finished.\n', flush=True)

if __name__ == '__main__':
    main()
    