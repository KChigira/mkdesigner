#! /bin/sh

#pip install -e .
#conda install bcftools
#conda install bgzip


mkprimer -r test_ref.fasta \
         -V test03/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test08 -t SNP \
         --mindep 5 --maxdep 120 --cpu 4 \
         --min_prodlen 150 --max_prodlen 280 \
         --search_span 140
