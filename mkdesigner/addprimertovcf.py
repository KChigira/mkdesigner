import csv
from multiprocessing import Pool
import os
import subprocess as sbp
import sys
import pandas as pd # type: ignore
from mkdesigner.utils import call_log, prepare_cmd, read_vcf, time_stamp

class AddPrimerToVcf(object):

    additional_info = ['name','num','chr','L_seq','R_seq','L_pos','R_pos','L_TM','R_TM','product_size']
    header = []
    colnames = []
    data = []

    def __init__(self, args):
        self.args = args

        self.out = args.middir
        self.ref = '{}/ref/{}'.format(self.out, os.path.basename(args.ref))
        self.vcf = '{}/vcf/{}_selected.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])
        self.cpu = args.cpu
        self.scope = args.scope
        self.margin = args.margin

        self.output_tmp = '{}/vcf/{}_selected_tmp.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])
        self.output_vcf = '{}/vcf/{}_selected_primer_added.vcf'.format(self.out, os.path.splitext(os.path.basename(args.vcf))[0])

    def run(self):
        print(time_stamp(),
              'Making databases.',
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
        print(time_stamp(),
              'Done.',
              flush=True)
        
        #Read input VCF
        vcf_list = read_vcf(self.vcf)
        self.header = vcf_list[0]
        self.colnames = vcf_list[1]
        self.data = vcf_list[2]
        self.header.append('##addprimertovcf.py_{}'.format(time_stamp()))
        self.data = pd.DataFrame(self.data, columns=self.colnames)
        nrow_all = len(self.data) #This is all candidate variants.
        print(time_stamp(),
              'Input VCF has {} variants.'.format(nrow_all),
              flush=True)
        print(time_stamp(),
              'Removing variants which are impossible to be markers.',
              flush=True)
        self.data = self.delete_impossible_variants(self.data)
        nrow = len(self.data)
        print(time_stamp(),
              '{} variants are selected for making primers.'.format(nrow),
              flush=True)

        print(time_stamp(),
              'Searching primers and checking their specificity '
              'using {} threads.'.format(self.cpu),
              flush=True)
        no_primer = 0
        non_specific = 0
        success = 0
        #Multi processing
        ##############################################
        with Pool(self.cpu) as p:
            results = p.map(self.parallel, range(nrow))
            #Each process returns list,
            #[id(range(nrow)), exit status(0~2), Desciption added to INFO]
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

    def delete_impossible_variants(self, dataframe):
        #Read INFO column of VCF data
        delete_row = []
        for i in range(len(dataframe)):
            info = dataframe['INFO'][i].split(';')
            for elem in info:
                elem_split = elem.split('=')
                if elem_split[0] == 'SPAN':
                    #'span' indicates the distance to the mutations
                    # that exist before and after the current variant.
                    span = elem_split[1].split(',')
                    span = list(map(int, span))
                    break

            #Delete if it is impossible to make primers because span is too small.
            min_span = self.args.primer_min_size + self.margin
            if span[0] <= min_span or span[1] <= min_span:
                delete_row.append(i)
        dataframe_pass = dataframe.drop(dataframe.index[delete_row])
        dataframe_pass = dataframe_pass.reset_index(drop=True)
        return dataframe_pass

    def parallel(self, i):
        #[0]:row number [1]:status(0 means NO_PRIMER, 1 means NON_SPECIFIC, 2 means PASS) [2]description for adding primer infomation
        return_list = [i, 0, ';PRIMER=']

        series = self.data.iloc[i, :]
        st_in = self.samtools_input(series)
        st_out = self.samtools(st_in, i)
        primer3_format_file = self.make_primer3_input(series, st_out)
        '''
        if primer3_format_file == 'N':
            return_list = [i, 0, ';PRIMER=']
            return return_list
        '''
        primer3_result_file = self.primer3(primer3_format_file)
        blastn_data_list = self.make_blastn_input(primer3_result_file)
        if len(blastn_data_list) <= 1:
            return_list = [i, 0, ';PRIMER=']
            return return_list
        blastn_query_file = blastn_data_list[0]
        df_primer_info = blastn_data_list[1]
        blastn_result_file = self.blastn(blastn_query_file)
        df_filtered = self.filter_blastn_result(blastn_result_file, df_primer_info['L_seq'], df_primer_info['R_seq'])
        if df_filtered.shape[0] <= 1:
            return_list = [i, 1, ';PRIMER=']
            return return_list
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
        #Read INFO column of VCF data
        info = series['INFO'].split(';')
        for elem in info:
            elem_split = elem.split('=')
            if elem_split[0] == 'SPAN':
                span = elem_split[1].split(',')
                span = list(map(int, span))
                break

        #Modified to remove impossible variants before multi processing. 230809
        '''
        #if it is impossible to make primers because span is too small, primer3 input file is not made.
        min_span = self.args.primer_min_size + self.args.margin
        if span[0] <= min_span or span[1] <= min_span:
            return 'N'
        '''

        #Make parameters for primer3
        target_start = self.scope - self.margin + 1
        var_len = len(series['REF'])
        target_length = var_len + self.margin * 2
        #Avoid designing primers at surrounding variants.
        exclude = ''
        if span[0] <= self.scope:
            exclude += '{},{}'.format(1, self.scope - span[0] + 1)
        if span[1] <= self.scope + var_len - 1:
            exclude += ' {},{}'.format(self.scope + span[1], self.scope - span[1] + var_len)
        #For SNP markers, designated product length is used.
        #For INDEL markers, product length is determined by 
        # an expression with the size of INDEL as a variable.
        if self.args.type == 'SNP' :
            max_prd = self.args.args.max_prodlen
            opt_prd = self.args.args.opt_prodlen
            min_prd = self.args.args.min_prodlen
        elif self.args.type == 'INDEL' :
            X = abs(len(series['REF']) - len(series['ALT']))
            if len(series['REF']) > len(series['ALT']) :
                ref_shorter = 0
                alt_shorter = X
            else :
                ref_shorter = X
                alt_shorter = 0

            if X < 5 :
                max_prd = 100 - ref_shorter
                opt_prd = 75 - ref_shorter
            else:
                max_prd = round((300 * X) / (10 + X) - ref_shorter)
                opt_prd = round((max_prd * 0.75) - ref_shorter)
            min_prd = 50 + alt_shorter

        primer3_data_list = [
            'SEQUENCE_ID={}\n'.format(st_out[0]),
            'SEQUENCE_TEMPLATE={}\n'.format(st_out[1]),
            'SEQUENCE_TARGET={},{}\n'.format(target_start, target_length),
            'SEQUENCE_EXCLUDED_REGION={}\n'.format(exclude),
            'PRIMER_NUM_RETURN={}\n'.format(self.args.args.primer_num_consider),
            'PRIMER_OPT_SIZE={}\n'.format(self.args.args.primer_opt_size),
            'PRIMER_MIN_SIZE={}\n'.format(self.args.args.primer_min_size),
            'PRIMER_MAX_SIZE={}\n'.format(self.args.args.primer_max_size),
            'PRIMER_PRODUCT_OPT_SIZE={}\n'.format(opt_prd),
            'PRIMER_PRODUCT_SIZE_RANGE={}-{}\n'.format(min_prd, max_prd),
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
        cmd = 'primer3_core --output {} {} \
                >> {}/log/primer3.log 2>&1'.format(name_result, input, self.out)
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

        os.remove(input)
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
                    primer_row = pd.Series(index=self.additional_info, name=str(idnum), dtype=str)
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
        
        os.remove(input)
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

        os.remove(input)
        return name_result

    def filter_blastn_result(self, input, primers_L, primers_R):
        try:
            df = pd.read_csv(input, header=None, sep='\t')
        except pd.errors.EmptyDataError:
            os.remove(input)
            return pd.DataFrame()
        os.remove(input)
        col = ['qaccver', 'saccver', 'pident', 'length', 'mismatch', 'gapopen', 'qstart', 'qend', 'sstart', 'send', 'evalue', 'bitscore', 'qseq', 'sseq', 'sstrand']
        #Example: [test:98-322_0	test	100	20	0	0	41	60	322	303	0.002	33.3	TGGTCCTTCGAGTGGATGGA	TGGTCCTTCGAGTGGATGGA	minus]
        df.columns = col
        nrow = len(df)
        df['idnum'] = range(nrow) #Add id number to last column

        df_selected = None

        idnum = -1
        for j in range(nrow):
            while int(df['qaccver'][j].split('_')[-1]) != idnum:
                idnum += 1
                p_len_L = len(primers_L.iloc[idnum])
                p_len_R = len(primers_R.iloc[idnum])
                p_pos_L = [1, p_len_L]
                p_pos_R = [p_len_L + 20 + 1, p_len_L + 20 + p_len_R]

            df.at[df.index[j], 'idnum'] = idnum
            
            ## 'mm' means mismuch nucleotide number
            ## 'mm_3t' means mismuch nucleotide number in 3' terminal
            if df['qend'][j] < p_pos_R[1]/2: 
                #5' terminal
                if df['qstart'][j] - p_pos_L[0] < 2:
                    mm = df['qstart'][j] - p_pos_L[0]
                else:
                    mm = df['qstart'][j] - p_pos_L[0] - 1
                #If 2 or more bases from the end are not aligned, all are not considered mismatches and 1 is subtracted from the mismatch.
                #3' terminal
                if p_pos_L[1] - df['qend'][j] < 2:
                    mm3t = p_pos_L[1] - df['qend'][j]
                else:
                    mm3t = p_pos_L[1] - df['qend'][j] - 1
                mm = mm + mm3t
            else:
                #5' terminal
                if df['qstart'][j] - p_pos_R[0] < 2:
                    mm = df['qstart'][j] - p_pos_R[0]
                else:
                    mm = df['qstart'][j] - p_pos_R[0] - 1
                #3' terminal
                if p_pos_L[1] - df['qend'][j] < 2:
                    mm3t = p_pos_R[1] - df['qend'][j]
                else:
                    mm3t = p_pos_R[1] - df['qend'][j] - 1
                mm = mm + mm3t

            mm = mm + df['mismatch'][j] # add internal mismuch number
            if mm > self.args.args.mismatch_allowed:
                continue
            if mm3t > self.args.args.mismatch_allowed_3_terminal:
                continue
            
            qseq = df['qseq'][j][-5:]
            sseq = df['sseq'][j][-5:]
            for k in range(5-mm3t):
                if qseq[4-k] != sseq[4-k]:
                    mm3t += 1
            if mm3t > self.args.args.mismatch_allowed_3_terminal:
                continue

            if df_selected is None:
                df_selected = pd.DataFrame([df.iloc[j]])
            else:
                df_selected = pd.concat([df_selected, pd.DataFrame([df.iloc[j]])])
        
        if df_selected is None:
            pd.DataFrame(columns=df.columns)
        
        df_selected.sort_values(by=['idnum','saccver','sstart'], inplace=True) #sort
        
        #Detecting unintended PCR products
        df_output = None
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
                        if df_selected.at[df_selected.index[j+cnt], 'sstart'] - pos < self.args.args.unintended_prod_size_allowed:
                            if df_output is None:
                                df_output = pd.DataFrame([df_selected.iloc[j]])
                            else:
                                df_output = pd.concat([df_output, pd.DataFrame([df_selected.iloc[j]])])
                            df_output = pd.concat([df_output, pd.DataFrame([df_selected.iloc[j+cnt]])])
                        else:
                            break
        if df_output is None:
             df_output = pd.DataFrame(columns=df_selected.columns)
             
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



