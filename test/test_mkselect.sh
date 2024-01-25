#! /bin/sh

#pip install -e .
#conda install bcftools
#conda install bgzip
#conda install r-base -c conda-forge

mkselect -i test_mkprimer_snp/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000

mkselect -i test_mkprimer_snp/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 30

mkselect -i test_mkprimer_indel/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000

mkselect -i test_mkprimer_indel/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10

mkselect -i test_mkprimer_snp/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20000 --avoid_lowercase

mkselect -i test_mkprimer_indel/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20000 --avoid_lowercase

mkselect -i test_mkprimer_snp/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20000 --avoid_lowercase

mkselect -i test_mkprimer_snp/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20000 --avoid_lowercase \
         -t test:300000-400000

mkselect -i test_mkprimer_snp/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20000 --avoid_lowercase \
         -t test:0-100000

mkselect -i test_mkprimer_snp/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 5 --avoid_lowercase \
         -t test:0-100000

mkselect -i test_mkprimer_indel/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20000 --avoid_lowercase

mkselect -i test_mkprimer_indel/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20000 --avoid_lowercase \
         --mindif 10 --maxdif 50


#230922 ver.0.3.1
mkselect -i test_mkprimer_snp_3/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp_3/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000 --avoid_lowercase
mkselect -i test_mkprimer_snp_3/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp_3/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20 --avoid_lowercase
mkselect -i test_mkprimer_indel_3/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel_3/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000 --avoid_lowercase
mkselect -i test_mkprimer_indel_3/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel_3/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000 --avoid_lowercase \
         --mindif 10 --maxdif 50

#240125 ver.0.3.2
mkselect -i test_mkprimer_snp_4/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp_4/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000 --avoid_lowercase
mkselect -i test_mkprimer_snp_4/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp_4/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20 --avoid_lowercase
mkselect -i test_mkprimer_indel_4/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel_4/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000 --avoid_lowercase
mkselect -i test_mkprimer_indel_4/ref/test_ref.fasta.fai \
         -V test_mkprimer_indel_4/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 10000 --avoid_lowercase \
         --mindif 10 --maxdif 50

#240125 ver.0.3.3
mkselect -i test_mkprimer_snp_4/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp_4/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20 --avoid_lowercase
mkselect -i test_mkprimer_snp_4/ref/test_ref.fasta.fai \
         -V test_mkprimer_snp_4/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 20 -d ./density.tsv --avoid_lowercase