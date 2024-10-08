#! /bin/sh

###For developmant. Please ignore.
#pip install -e .
#conda activate mkdesigner
#cd test

mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -p test_mkvcf --cpu 4
      

#230922 ver. 0.3.1
mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -p test_mkvcf_3 --cpu 4

#240125 ver. 0.3.4
mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -p test_mkvcf_4 --cpu 4

#240624 ver. 0.3.4
mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -p test_mkvcf_4 --cpu 4

#240626 ver. 0.4.1
mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -O test041 --cpu 4

#240626 ver. 0.4.2
mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -O test042 --cpu 4