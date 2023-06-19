import csv
from multiprocessing import Pool
import os
import subprocess as sbp
import sys
import pandas as pd
from mkdesigner.utils import call_log, prepare_cmd, read_vcf, time_stamp

class AddPrimerToVcf(object):

    additional_info = ['name','num','chr','L_seq','R_seq','L_pos','R_pos','L_TM','R_TM','product_size']
    header = []
    colnames = []
    data = []

    def __init__(self, args):
        self.args = args

        self.out = args.project
        self.ref = '{}/ref/{}'.format(self.out, os.path.basename(args.ref))
        self.vcf = '{}/vcf/{}_selected.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])
        self.cpu = args.cpu
        self.scope = args.search_span
        self.margin = args.margin

        self.output_tmp = '{}/vcf/{}_selected_tmp.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])
        self.output_vcf = '{}/vcf/{}_selected_primer_added.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])

    def run(self):
        print(time_stamp(),
              'Making primer sets for each variants.',
              flush=True)
        
        #Make database files needed for blastn
        cmd0 = 'makeblastdb -in {} \
                -parse_seqids \
                -dbtype nucl \
                >> {}/log/blastn.log 2>&1'.format(self.ref, self.out)
        cmd0 = prepare_cmd(cmd0)
        try:
            sbp.run(cmd0,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'blastn', cmd0)
            sys.exit(1) 

        #Read input VCF
        vcf_list = read_vcf(self.vcf)
        self.header = vcf_list[0]
        self.colnames = vcf_list[1]
        self.data = vcf_list[2]
        self.header.append('##addprimertovcf.py_{}'.format(time_stamp()))
        self.data = pd.DataFrame(self.data, columns=self.colnames)
        nrow = len(self.data)

        no_primer = 0
        non_specific = 0
        success = 0
        #Multi processing
        ##############################################
        with Pool(self.cpu) as p:
            results = p.map(self.parallel, range(nrow))
        #############################################
        for res in results:
            id = res[0]
            status = res[1]
            add_str = res[2]
            if status == 0:
                no_primer += 1
                self.data.at[self.data.index[id], 'FILTER'] = 'NO_PRIMER'
            elif status == 1:
                non_specific += 1
                self.data.at[self.data.index[id], 'FILTER'] = 'NON_SPECIFIC'
            elif status == 2:
                success += 1
                self.data.at[self.data.index[id], 'FILTER'] = 'PASS_P'
            self.data.at[self.data.index[id], 'INFO'] += add_str

        with open(self.output_vcf, 'w') as o:
            for h in self.header:
                o.write('{}\n'.format(h))
            writer = csv.writer(o, delimiter='\t')
            #writer.writerows(header)
            writer.writerow(self.colnames)
        
        self.data.to_csv(self.output_tmp, sep='\t', header=False, index=False)
        cmd1 = 'cat {} >> {}'.format(self.output_tmp, self.output_vcf)
        cmd1 = prepare_cmd(cmd1)
        try:
            sbp.run(cmd1,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            print(time_stamp(),
              'Error occured writing vcf data.',
              flush=True)
            sys.exit(1) 

        print(time_stamp(),
              'Selecting primer has been finished.\n{} variants are selected from {} candidates.\n(No primer: {} variants, Only non-specific primer: {} variants)'.format(success, nrow, no_primer,non_specific),
              flush=True)
        print(time_stamp(),
              'Done.',
              flush=True)


    def parallel(self, i):
        #[0]:row number [1]:status(0 means NO_PRIMER, 1 means NON_SPECIFIC, 2 means PASS) [2]description for adding primer infomation
        return_list = [i, 0, ';PRIMER=']

        series = self.data.iloc[i, :]
        st_in = self.samtools_input(series)
        st_out = self.samtools(st_in, i)
        primer3_format_file = self.make_primer3_input(series, st_out)
        primer3_result_file = self.primer3(primer3_format_file)
        blastn_data_list = self.make_blastn_input(primer3_result_file)
        if len(blastn_data_list) <= 1:
            return_list = [i, 0, ';PRIMER=']
            return return_list
        blastn_query_file = blastn_data_list[0]
        df_primer_info = blastn_data_list[1]
        blastn_result_file = self.blastn(blastn_query_file)
        df_filtered = self.filter_blastn_result(blastn_result_file, df_primer_info['L_seq'], df_primer_info['R_seq'])
        use_primer_set = self.select_primer_set(df_primer_info, df_filtered)
        if use_primer_set == -1:
            return_list = [i, 1, ';PRIMER=']
            return return_list
        else:
            add_list = df_primer_info.iloc[use_primer_set].values.tolist()
            add_list = map(str, add_list)
            add = ';PRIMER={}'.format('|'.join(add_list))
            return_list = [i, 2, add]
            return return_list

    def samtools_input(self, series):
        chr = str(series['#CHROM'])
        ref_len = len(str(series['REF']))
        start = int(series['POS']) - self.scope
        end = int(series['POS']) + (ref_len - 1) + self.scope
        return_str = '{}:{}-{}'.format(chr, start, end)
        return return_str

    def samtools(self, st_in, i):
        cmd = 'samtools faidx {} {}'.format(self.ref, st_in, self.out, i)
        cmd = prepare_cmd(cmd)
        try:
            str = sbp.run(cmd, capture_output=True, text=True,
                          shell=True, check=True).stdout
        except sbp.CalledProcessError:
            call_log(self.out, 'samtools', cmd)
            sys.exit(1)
        str_tmp = str.split('\n')
        str_list = [str_tmp[0][1:], ''.join(str_tmp[1:])]
        return str_list
    
    def make_primer3_input(self, series, st_out):
        info = series['INFO'].split(';')
        for elem in info:
            elem_split = elem.split('=')
            if elem_split[0] == 'SPAN':
                span = elem_split[1].split(',')
                span = list(map(int, span))
                break

        target_start = self.scope - self.args.margin + 1
        var_len = len(series['REF'])
        target_length = var_len + self.margin * 2
        exclude = ''
        if span[0] <= self.scope:
            exclude += '{},{}'.format(1, self.scope - span[0] + 1)
        if span[1] <= self.scope + var_len - 1:
            exclude += ' {},{}'.format(self.scope + span[1], self.scope - span[1] + var_len)

        primer3_data_list = [
            'SEQUENCE_ID={}\n'.format(st_out[0]),
            'SEQUENCE_TEMPLATE={}\n'.format(st_out[1]),
            'SEQUENCE_TARGET={},{}\n'.format(target_start, target_length),
            'SEQUENCE_EXCLUDED_REGION={}\n'.format(exclude),
            'PRIMER_NUM_RETURN={}\n'.format(self.args.primer_num_consider),
            'PRIMER_OPT_SIZE={}\n'.format(self.args.primer_opt_size),
            'PRIMER_MIN_SIZE={}\n'.format(self.args.primer_min_size),
            'PRIMER_MAX_SIZE={}\n'.format(self.args.primer_max_size),
            'PRIMER_PRODUCT_OPT_SIZE={}\n'.format(self.args.opt_prodlen),
            'PRIMER_PRODUCT_SIZE_RANGE={}-{}\n'.format(self.args.min_prodlen, self.args.max_prodlen),
            'PRIMER_OPT_GC_PERCENT=50.0\n',
            'PRIMER_MIN_GC=30.0\n',
            'PRIMER_MAX_GC=70.0\n',
            'PRIMER_MIN_TM=55.0\n',
            'PRIMER_OPT_TM=61.0\n',
            'PRIMER_MAX_TM=67.0\n',
            'PRIMER_PAIR_MAX_DIFF_TM=5.0\n',
            'PRIMER_MAX_SELF_ANY=5\n',
            'PRIMER_MAX_SELF_END=2\n',
            'PRIMER_MAX_POLY_X=4\n',
            'PRIMER_EXPLAIN_FLAG=1\n',
            '=\n']
        primer3_data = ''.join(primer3_data_list)

        name_format = '{}/intermediate/format_{}_{}.txt'.format(self.out, series['#CHROM'], series['POS'])
        with open(name_format, 'w') as o:
            o.write(primer3_data)

        return name_format

    def primer3(self, input):
        name_result = str(input).replace('/format_', '/result_')
        cmd = '{}primer3_core --output {} {} \
                >> {}/log/primer3.log 2>&1'.format(self.args.primer3_loc, name_result, input, self.out)
        cmd = prepare_cmd(cmd)
        try:
            sbp.run(cmd,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True,
                    check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'primer3', cmd)
            sys.exit(1)

        return name_result

    def make_blastn_input(self, input):
        sequence_id = ''
        chr = ''
        start_pos = 0
        idnum = 0
        primer_info = pd.DataFrame(columns=self.additional_info)
        with open(input, 'r') as inp:
            for line in inp:
                tmp = line.split('=')
                if len(tmp) < 2:
                    continue
                if tmp[0] == 'SEQUENCE_ID':
                    sequence_id = tmp[1].strip()
                    chr = sequence_id.split(':')[0]
                    start_pos = int(sequence_id.split(':')[1].split('-')[0])
                if tmp[0] == 'PRIMER_LEFT_{}_SEQUENCE'.format(idnum):
                    primer_row = pd.Series(index=self.additional_info, name=str(idnum))
                    primer_row['name'] = sequence_id
                    primer_row['num'] = idnum
                    primer_row['chr'] = chr
                    primer_row['L_seq'] = tmp[1].strip()
                if tmp[0] == 'PRIMER_RIGHT_{}_SEQUENCE'.format(idnum):
                    primer_row['R_seq'] = tmp[1].strip()
                if tmp[0] == 'PRIMER_LEFT_{}'.format(idnum):
                    L_pos = int(tmp[1].split(',')[0])
                    primer_row['L_pos'] = start_pos + L_pos
                if tmp[0] == 'PRIMER_RIGHT_{}'.format(idnum):
                    R_pos = int(tmp[1].split(',')[0])
                    primer_row['R_pos'] = start_pos + R_pos
                if tmp[0] == 'PRIMER_LEFT_{}_TM'.format(idnum):
                    primer_row['L_TM'] = tmp[1].strip()
                if tmp[0] == 'PRIMER_RIGHT_{}_TM'.format(idnum):
                    primer_row['R_TM'] = tmp[1].strip()
                if tmp[0] == 'PRIMER_PAIR_{}_PRODUCT_SIZE'.format(idnum):
                    primer_row['product_size'] = tmp[1].strip()
                    primer_info = pd.concat([primer_info, pd.DataFrame([primer_row])])
                    idnum += 1
        if idnum == 0:
            return ''
        
        name_query = str(input).replace('/result_', '/query_')
        with open(name_query, 'w') as o:
            for j in range(idnum):
                o.write('>{}:{}-{}_{}\n'.format(chr, primer_info.at[primer_info.index[j], 'L_pos'], primer_info.at[primer_info.index[j], 'R_pos'], j))
                o.write('{}NNNNNNNNNNNNNNNNNNNN{}\n'.format(primer_info.at[primer_info.index[j], 'L_seq'], primer_info.at[primer_info.index[j], 'R_seq']))
        
        return_list = [name_query, primer_info]
        return return_list

    def blastn(self, input):
        name_result = str(input).replace('/query_', '/blastn_')
        cmd = 'blastn -db {} -query {} -out {} \
                -outfmt "6 std qseq sseq sstrand" \
                -evalue 30000 -word_size 7 \
                -num_alignments 50000 \
                -penalty -1 -reward 1 \
                -ungapped >> {}/log/blastn.log 2>&1'.format(self.ref, input,name_result, self.out)
        cmd = prepare_cmd(cmd)
        try:
            sbp.run(cmd,
                    stdout=sbp.DEVNULL,
                    stderr=sbp.DEVNULL,
                    shell=True, check=True)
        except sbp.CalledProcessError:
            call_log(self.out, 'blastn', cmd)
            sys.exit(1)

        return name_result

    def filter_blastn_result(self, input, primers_L, primers_R):
        df = pd.read_csv(input, header=None, sep='\t')
        col = ['qaccver', 'saccver', 'pident', 'length', 'mismatch', 'gapopen', 'qstart', 'qend', 'sstart', 'send', 'evalue', 'bitscore', 'qseq', 'sseq', 'sstrand']
        #Example: [test:98-322_0	test	100	20	0	0	41	60	322	303	0.002	33.3	TGGTCCTTCGAGTGGATGGA	TGGTCCTTCGAGTGGATGGA	minus]
        df.columns = col
        nrow = len(df)
        df['idnum'] = range(nrow) #Add id number to last column

        df_selected = pd.DataFrame(columns=df.columns)

        idnum = -1
        for j in range(nrow):
            while int(df['qaccver'][j].split('_')[-1]) != idnum:
                idnum += 1
                p_len_L = len(primers_L[idnum])
                p_len_R = len(primers_R[idnum])
                p_pos_L = [1, p_len_L]
                p_pos_R = [p_len_L + 20 + 1, p_len_L + 20 + p_len_R]

            df.at[df.index[j], 'idnum'] = int(df['qaccver'][j].split('_')[-1])
            
            ## 'mm' means mismuch nucleotide number
            if df['qend'][j] < p_pos_R[1]/2:
                mm = (df['qstart'][j] - p_pos_L[0]) + (p_pos_L[1] - df['qend'][j])
            else:
                mm = (df['qstart'][j] - p_pos_R[0]) + (p_pos_R[1] - df['qend'][j])
            mm = mm + df['mismatch'][j] # add internal mismuch number
            if mm > self.args.mismatch_allowed:
                continue

            ## 'mm_3t' means mismuch nucleotide number in 3' terminal
            if df['qend'][j] < p_pos_R[1]/2:
                mm3t = p_pos_L[1] - df['qend'][j]
            else:
                mm3t = df['qstart'][j] - p_pos_R[0]
            if mm3t > self.args.mismatch_allowed_3_terminal:
                continue
            qseq = df['qseq'][j][-5:]
            sseq = df['sseq'][j][-5:]
            for k in range(5-mm3t):
                if qseq[4-k] != sseq[4-k]:
                    mm3t += 1
            if mm3t > self.args.mismatch_allowed_3_terminal:
                continue

            df_selected = pd.concat([df_selected, pd.DataFrame([df.iloc[j]])])
        
        df_selected = df_selected.sort_values('sstart') #sort by position
        df_selected = df_selected.sort_values('saccver') #sort by chromosome
        df_selected = df_selected.sort_values('idnum') #sort by dataset

        #Detecting unintended PCR products
        df_output = pd.DataFrame(columns=df_selected.columns)
        for j in range(len(df_selected)):
            if df_selected.at[df_selected.index[j], 'sstrand'] == 'plus':
                pri = df_selected.at[df_selected.index[j], 'qaccver']
                chr = df_selected.at[df_selected.index[j], 'saccver']
                pos = df_selected.at[df_selected.index[j], 'sstart']
                cnt = 0
                while True:
                    cnt += 1
                    if j + cnt >= len(df_selected): break
                    if df_selected.at[df_selected.index[j+cnt], 'qaccver'] != pri: break
                    if df_selected.at[df_selected.index[j+cnt], 'saccver'] != chr: break
                    if df_selected.at[df_selected.index[j+cnt], 'sstrand'] == 'minus':
                        if df_selected.at[df_selected.index[j+cnt], 'sstart'] - pos < self.args.unintended_prod_size_allowed:
                            df_output = pd.concat([df_output, pd.DataFrame([df_selected.iloc[j]])])
                            df_output = pd.concat([df_output, pd.DataFrame([df_selected.iloc[j+cnt]])])
                        else:
                            break
        
        name_blastn_filtered = str(input).replace('/blastn_', '/blastn_filtered_')
        df_output.to_csv(name_blastn_filtered, sep='\t', header=False, index=False)
        df_output.reset_index(drop=True)

        return df_output

    def select_primer_set(self, df_primer_info, df_blastn_info):
        use_primer = -1 #"-1" means "No specific primer set"
        #If Useful primer set was found, this parameter will be natural number.
        for j in range(len(df_primer_info)):
            id = '{}:{}-{}_{}'.format(
                    df_primer_info.at[df_primer_info.index[j], 'chr'],
                    df_primer_info.at[df_primer_info.index[j], 'L_pos'],df_primer_info.at[df_primer_info.index[j], 'R_pos'],df_primer_info.at[df_primer_info.index[j], 'num'])
            hit_cnt = 0
            match_cnt = 0
            for k in range(len(df_blastn_info)):
                if id == str(df_blastn_info.at[df_blastn_info.index[k], 'qaccver']):
                    hit_cnt += 1
                    if df_blastn_info.at[df_blastn_info.index[k], 'sstrand'] == 'plus':
                        if df_primer_info.at[df_primer_info.index[j], 'L_pos'] == df_blastn_info.at[df_blastn_info.index[k], 'sstart']:
                            match_cnt += 1
                    else:
                        if df_primer_info.at[df_primer_info.index[j], 'R_pos'] == df_blastn_info.at[df_blastn_info.index[k], 'sstart']:
                            match_cnt += 1
            if hit_cnt == 2 and match_cnt == 2:
                use_primer = j
                break
        return use_primer


