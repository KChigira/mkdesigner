import math
import pandas as pd
from mkdesigner.utils import read_vcf, time_stamp
import matplotlib.pyplot as plt

class VisualizeMarker(object):
    def __init__(self, vcf, out_png, fai):
        self.vcf = vcf
        self.png = out_png

        #Prepare chromosome information
        self.fai_data = []
        with open(fai, 'r') as f:
            for row in f:
                row = row.strip()
                self.fai_data.append(row.split('\t'))
        self.colnames = ['chr', 'len', 'A', 'B', 'C']
        self.fai_data = pd.DataFrame(self.fai_data, columns=self.colnames)
        self.fai_data['len'] = self.fai_data['len'].astype(int)

        #Read vcf file
        vcf_list = read_vcf(vcf)
        col = vcf_list[1]
        data = vcf_list[2]
        self.data = pd.DataFrame(data, columns=col)
        self.data['POS'] = self.data['POS'].astype(int)

    def run(self):
        print(time_stamp(),
              'Drawing positions of selected markers.',
              flush=True)
        
        #number of digits in the length of the longest chromosome
        digits = math.floor(math.log10(max(self.fai_data['len'])))
        standard = 10**(digits)
        #if the longest chr length is 23098790,
        #digits = 7
        #standard = 10000000

        if(max(self.fai_data['len']) / standard < 2):
            standard = standard / 5
        elif(max(self.fai_data['len']) / standard < 5):
            standard = int(standard / 2)
        #if the longest chr length is 23098790,
        #standard = 5000000 
        
        y_axis_at = range(0, standard*11, standard)
        y_axis_lab = []
        if(standard >= 100000):
            st_lab = standard/1000000
            sign = 'M'
        elif(standard >= 100):
            st_lab = standard/1000
            sign = 'K'
        else:
            st_lab = standard
            sign = 'bp'
        
        for i in range(11):
            y_axis_lab.append('{}{}'.format(round(st_lab * i, 1), sign))
        
        longest_len = max(self.fai_data['len'])


        # Create a figure
        fig = plt.figure(figsize=(5, 5), dpi=144)
        ax = fig.add_subplot(111,
                             xlim=[-1, len(self.fai_data['chr'])], 
                             xticks=range(len(self.fai_data['chr'])), 
                             xticklabels=self.fai_data['chr'],
                             xlabel="Chromosome",
                             ylim=[longest_len*1.05, -longest_len*0.05],
                             yticks=y_axis_at, 
                             yticklabels=y_axis_lab,
                             ylabel="Position")
        plt.subplots_adjust(left=0.15, right=0.95, bottom=0.15, top=0.95)
        plt.xticks(rotation=45)

        for i in range(len(self.fai_data['chr'])):
            #plot([x1, x2], [y1, y2])
            ax.plot([i, i], [0, self.fai_data['len'][i]], color="black") 
            data_select = self.data[self.data['#CHROM'] == self.fai_data['chr'][i]]
            for j in range(len(data_select)):
                pos = data_select['POS'].iloc[j]
                ax.plot([i-0.3, i+0.3], [pos, pos], color="black", linewidth=0.5)

        plt.xlim(-1, len(self.fai_data['chr']))
        plt.ylim(longest_len*1.05, -longest_len*0.05)

        # Save figure
        fig.savefig(self.png, dpi=144)

        print(time_stamp(),
              'Done.',
              flush=True)
        


