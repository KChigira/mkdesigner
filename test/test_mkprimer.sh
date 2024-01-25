#! /bin/sh

###For developmant. Please ignore.
#pip install -e .
#conda activate mkdesigner
#cd test

#SNP
mkprimer -r test_ref.fasta \
         -V test_mkvcf/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_snp -t SNP \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --min_prodlen 150 --opt_prodlen 180 --max_prodlen 280 \
         --search_span 140 --primer_min_size 24 \
         --primer_opt_size 24 --primer_max_size 24

#INDEL
mkprimer -r test_ref.fasta \
         -V test_mkvcf/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_indel -t INDEL \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --search_span 250 --primer_min_size 18 \
         --primer_opt_size 20 --primer_max_size 26

#230809 modified
#SNP
mkprimer -r test_ref.fasta \
         -V test_mkvcf/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_snp_2 -t SNP \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --min_prodlen 150 --opt_prodlen 180 --max_prodlen 280 \
         --search_span 140 --primer_min_size 24 \
         --primer_opt_size 24 --primer_max_size 24

#INDEL
mkprimer -r test_ref.fasta \
         -V test_mkvcf/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_indel_2 -t INDEL \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --search_span 250 --primer_min_size 18 \
         --primer_opt_size 20 --primer_max_size 26

#230922 ver.0.3.1
#SNP
mkprimer -r test_ref.fasta \
         -V test_mkvcf_3/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_snp_3 -t SNP \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --min_prodlen 150 --opt_prodlen 180 --max_prodlen 280 \
         --search_span 140 --primer_min_size 24 \
         --primer_opt_size 24 --primer_max_size 24

#INDEL
mkprimer -r test_ref.fasta \
         -V test_mkvcf_3/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_indel_3 -t INDEL \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --search_span 250 --primer_min_size 18 \
         --primer_opt_size 20 --primer_max_size 26

#240125 ver.0.3.2
#SNP
mkprimer -r test_ref.fasta \
         -V test_mkvcf_4/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_snp_4 -t SNP \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --min_prodlen 150 --opt_prodlen 180 --max_prodlen 280 \
         --search_span 140 --primer_min_size 24 \
         --primer_opt_size 24 --primer_max_size 24

#INDEL
mkprimer -r test_ref.fasta \
         -V test_mkvcf_4/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test_mkprimer_indel_4 -t INDEL \
         --mindep 5 --maxdep 120 --mismatch_allowed 5 --cpu 4 \
         --search_span 250 --primer_min_size 18 \
         --primer_opt_size 20 --primer_max_size 26