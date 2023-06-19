#! /bin/sh

#pip install -e .
#conda install bcftools
#conda install bgzip
#conda install r-base -c conda-forge

mkselect -i test08/ref/test_ref.fasta.fai \
         -V test08/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 30

