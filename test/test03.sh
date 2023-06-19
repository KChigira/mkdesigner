#! /bin/sh

#pip install -e .
#conda install bcftools
#conda install bgzip

mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -p test03 --cpu 4
      
