from datetime import datetime


def time_stamp():
    return '[mkdesigner:{}]'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def prepare_cmd(cmd):
    #this function make the command arguments splitted by only space.
    return ' '.join(cmd.split())

def call_log(out_dir, name, cmd):
    print(time_stamp(), 
          '!!ERROR!! {}\n'.format(cmd), 
          flush=True)

    print('please check {}/log/{}.log\n'.format(out_dir, name))

#returns list consisted from 3 elements [header, colnames, data]
def read_vcf(vcf_file):
    header = []
    colnames = []
    data = []
    with open(vcf_file, 'r') as v:
        for row in v:
            row = row.strip()
            if row[0:2] == '##':
                header.append(row)
            elif row[0:1] == '#':
                colnames = row.split('\t')
            else:
                data.append(row.split('\t'))
    return [header, colnames, data]
