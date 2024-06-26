#!/usr/bin/env python3

import csv
import os
import pandas as pd # type: ignore
import sys
import subprocess as sbp
from mkdesigner.utils import read_vcf, time_stamp, prepare_cmd
from mkdesigner.params import Params
from mkdesigner.visualize_marker import VisualizeMarker

pm = Params('mkselect')
args = pm.set_options()

class MKSelect(object):
    def __init__(self, args):
        pm.mkselect_check_args(args)
        self.args = args
        self.vcf = args.vcf
        self.fai = args.fai
        self.num_marker = args.num_marker
        self.target = args.target
        self.density = args.density
        self.mindif = args.mindif
        self.maxdif = args.maxdif

        self.stem = args.output
        self.dir = '{}_mkselect'.format(self.stem)
        os.mkdir(self.dir)

        #VCF data
        self.header = [] #VCF header
        self.colnames = [] #VCF colnames
        self.data = [] #VCF content
        self.data_s = [] #VCF content selected
        self.primers = [] #Primer information of selected variants
        self.out_table = [] #Output table, easy to read
        if self.density is None:
            self.den_table = None
        else:
            self.den_table = pd.read_csv(self.density, sep='\t') 
        #Marker density data

    def command(self):
        #Output command info
        command = ' '.join(sys.argv)
        fn = '{}/command.txt'.format(self.dir)
        with open(fn, 'w') as f:
            f.write('{}\n'.format(command))

    def readvcf(self):
        #Read input VCF
        vcf_list = read_vcf(self.vcf)
        self.header = vcf_list[0]
        self.colnames = vcf_list[1]
        self.data = vcf_list[2]
        self.header.append('##mkselect.py_{},num_primer={},target={}'.format(time_stamp(), self.num_marker, self.target))
        self.data = pd.DataFrame(self.data, columns=self.colnames)

    def filtervcf(self):
        #Select variants FILTER = PASS_P
        data_pass = self.data[self.data['FILTER'] == 'PASS_P']

        #Avoid lowercase
        if self.args.avoid_lowercase:
            print(time_stamp(), 'Removing markers with primers containing lowercase sequences.', flush=True)
            #Correct infomation of primers
            check_primers = self.get_info_primers(data_pass)
            #col = ['name','num','chr','L_seq','R_seq','L_pos','R_pos','L_TM','R_TM','product_size']
            delete_row = [] #row indexes to delete
            for i in range(len(check_primers)):
                if check_primers['L_seq'][i].isupper() and \
                   check_primers['R_seq'][i].isupper():
                    #if all characters are uppercase, TRUE
                    pass
                else:
                    delete_row.append(i)
            data_pass = data_pass.drop(data_pass.index[delete_row])
            
        #Select variants by --mindif and --maxdif
        str_len_ref = data_pass['REF'].str.len()
        str_len_alt = data_pass['ALT'].str.len()
        dif = str_len_ref - str_len_alt
        dif_abs = dif.abs()
        data_pass = data_pass[(dif_abs >= self.mindif) & (dif_abs <= self.maxdif)]
        
        #Reset index number (row)
        data_pass = data_pass.reset_index(drop=True)
        
        #Select variants if target position is designated.
        if self.target is not None:
            pass_row = [] #row indexes passed

            for h in range(len(self.target)):
                tmp = self.target[h].split(':')
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
                
                for i in range(len(data_pass)):
                    if data_pass['#CHROM'][i] == target_chr and \
                    int(data_pass['POS'][i]) > target_start and \
                    int(data_pass['POS'][i]) < target_end:
                        pass_row.append(i)

            #remove duplication and sort
            pass_row = list(set(pass_row))
            pass_row.sort()

            #Select only designated position
            data_pass = data_pass.iloc[pass_row]
            #Reset index number (row)
            data_pass = data_pass.reset_index(drop=True)

        #Make dataset for select markers
        intervals = [] 
        cur_chr = ''

        for i in range(len(data_pass)):
            if data_pass.at[data_pass.index[i], '#CHROM'] != cur_chr:
                #When chromosome of [i] is different to [i+1]
                intervals.append(10**20) #use 10**20 as instead of infinity
                cur_chr = data_pass.at[data_pass.index[i], '#CHROM']
                if self.den_table is not None:
                    cur_den = self.den_table[self.den_table['chr'] == cur_chr]
                    cur_den = cur_den.reset_index(drop=True)
            else:
                real_pos = [int(data_pass.at[data_pass.index[i-1], 'POS'])
                            , int(data_pass.at[data_pass.index[i], 'POS'])]

                #When there is no density information
                if self.den_table is None:
                    intervals.append(real_pos[1] - real_pos[0])
                else: #with density information, adjust position
                    adj_pos = []
                    for pos in real_pos:
                        new_pos = 0
                        for j in range(len(cur_den)):
                            st = int(cur_den.at[cur_den.index[j], 'start']) - 1
                            en = int(cur_den.at[cur_den.index[j], 'end'])
                            dn = float(cur_den.at[cur_den.index[j], 'density'])
                            if st < pos:
                                if pos < en:
                                    new_pos = new_pos + int((pos - st) * dn)
                                    break
                                else:
                                    new_pos = new_pos + int((en - st) * dn)
                        adj_pos.append(new_pos)
                    intervals.append(adj_pos[1] - adj_pos[0])

        intervals.append(10**20) #length of list is len(data_s) + 1
        #data_s       0   1   2   3   4   5
        #intervals  0   1   2   3   4   5   6 #[0] and [6] are infinity

        #Decrease markers to a specified number (-n)
        use_index = list(range(len(data_pass)))

        while self.num_marker < len(use_index):
            shortest = intervals.index(min(intervals))

            if intervals[shortest - 1] < intervals[shortest + 1]:
                intervals[shortest-1]=intervals[shortest-1]+intervals[shortest]
                del use_index[shortest - 1]
            else:
                intervals[shortest+1]=intervals[shortest+1]+intervals[shortest]
                del use_index[shortest]

            del intervals[shortest]
        
        self.data_s = data_pass.iloc[use_index]
        self.data_s = self.data_s.reset_index(drop=True)

        #Correct infomation of primers
        self.primers = self.get_info_primers(self.data_s)

    def get_info_primers(self, vcfdata):
        primers_list = []
        for i in range(len(vcfdata)):
            info = str(vcfdata.at[vcfdata.index[i], 'INFO'])
            info_spl = info.split(';')
            for j in range(len(info_spl)):
                elem = info_spl[j].split('=')
                if elem[0] == 'PRIMER':
                    pri = elem[1].split('|')
                    primers_list.append(pri)
        primers_col = ['name','num','chr','L_seq','R_seq','L_pos','R_pos','L_TM','R_TM','product_size']
        return pd.DataFrame(primers_list, columns=primers_col)

    def maketable(self):
        name_line = self.data_s.columns[9:]
        out_table_col = ['Chr','Pos','ID','Left','Right','L_TM','R_TM','Dif']
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

            #Product size
            prod_size = int(self.primers.at[self.primers.index[i], 'product_size'])
            len_alt = len(self.data_s.at[self.data_s.index[i], 'ALT'])
            len_ref = len(self.data_s.at[self.data_s.index[i], 'REF'])
            out_row.append(abs(len_alt-len_ref)) #'Dif'

            for line in name_line:
                line_info = self.data_s.at[self.data_s.index[i], line]
                #ex. 1/1:0,6:6:18:270,18,0
                if line_info[0:3] == '0/0':
                    out_row.append(prod_size)
                elif line_info[0:3] == '1/1':
                    size = (prod_size + len_alt - len_ref)
                    out_row.append(size)
            out_list.append(out_row)
        self.out_table = pd.DataFrame(out_list, columns=out_table_col)

    def output(self):
        #1. output VCF
        out_vcf_name = '{}/{}.vcf'.format(self.dir, self.stem)
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
        self.out_table.to_csv('{}/{}_primer_data.tsv'.format(self.dir, self.stem), sep='\t', header=True, index=False)

        print(time_stamp(), '{} markers were selected.\n'.format(len(self.data_s)), flush=True)

    def draw(self):
        out_vcf_name = '{}/{}.vcf'.format(self.dir, self.stem)
        out_png_name = '{}/{}.png'.format(self.dir, self.stem)

        vm = VisualizeMarker(out_vcf_name, out_png_name, self.fai)
        vm.run()
    

def main():
    print(time_stamp(), 'MKSelect started.', flush=True)

    prog = MKSelect(args)
    prog.command()
    prog.readvcf()
    prog.filtervcf()
    prog.maketable()
    prog.output()
    prog.draw()

    print(time_stamp(), 'MKSelect successfully finished.\n', flush=True)

if __name__ == '__main__':
    main()
    
