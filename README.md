# 'MKDesigner' User Guide
#### version 0.1.1

## Table of contents
- [Outline](#Outline)
- [Install](#Install)
  + [Dependencies](#Dependencies)
  + [Install via bioconda](#Installation-using-bioconda)
- [Usage](#Usage)
  + [Tutorial](#Tutorial)
  + [Commands](#Commands)
- [References](#References)

## Outline

'MKDesigner' is a tool to design DNA markers for PCR-based genotyping using whole genome resequence data. 
PCR-based genotyping is the most basic genotyping method, and is still an indispensable method for fine mapping and the like.
When performing PCR-based genotyping, it is necessary to identify DNA markers (SSR, InDel, SNP) that are mutated between parental cultivars and design primers to amplify their surroundings.
Primer3 is a convenient tool for designing primers against target sequences, available both on the web and on the local command line[1,2]. Primer-BLAST, which is a combination of Primer3 and BLAST, further searches for specificity within the reference genome and provides primers amplifying only the target sequence[3]. However, it can only be used on the web, and manual input is needed one by one. Therefore, it is very laborious when tens to hundreds of DNA markers are required. 

'MKDesigner' can solve such troubles of marker design. MKDesigner also uses Primer3 and BLAST but It can deal NGS data to design all possible markers and its primers at once.As long as you have the  whole genome resequence data of the parent cultivars, MKDesigner generates a list of primers that amplify your desired DNA marker in just 2 steps.

#### Citation
- Comming soon.

## Install

### Install via bioconda
We recommend that you install the MKDesigner in a dedicated environment.
```
conda create -n mkdesigner python=3.8 mkdesigner
```

#### Dependencies
 - python >=3.8,<4.0
 - pandas >=2.0.2,<3.0.0
 - samtools >=1.6,<2.0
 - bcftools >=1.5,<2.0
 - blast >=2.14.0,<3.0.0
 - gatk4 >=4.4.0.0,<5.0.0.0
 - picard >=2.18.29,<3.0.0
 - r-base >=4.2.3, <5.0.0

Tools above are installed automatically.
 - Primer3 >=2.6.1

Primer3 software must be installed manually.
```
cd ~
sudo apt-get install -y build-essential g++ cmake git-all
git clone https://github.com/primer3-org/primer3.git primer3
cd primer3/src
make
make test
```
If you have already installed primer3 at other directory, you have to set the path when you run the program.

#### Check about packages in dependency
Dependent packages often get errors about shared libraries.
Please check errors of packages below.
```
bcftools --version
samtools --version
```
If you got error like below... 
```
bcftools: error while loading shared libraries: libcrypto.so.1.0.0: cannot open shared object file: No such file or directory
```
you can try a solution like below.
```
cd /home/[USER NAME]/(ex.)miniconda3/envs/(ex.)mkdesigner/lib
ls -l libcrypto.so*
```
For example,
`lrwxrwxrwx ... libcrypto.so -> libcrypto.so.3`
`-rwxrwxr-x ... libcrypto.so.3`
Then, you can make symbolic link to the new version of the shared library.
```
ln -s libcrypto.so.3 libcrypto.so.1.0.0
```

## Usage
#### Tutorial
We have a dataset for test.
```terminal:get_test_dataset
git clone https://github.com/KChigira/mkdesigner.git
cd mkdesigner/test
ls
├── lineA_sorted_reads.bam 
├── lineB_sorted_reads.bam
├── test_ref.fasta
└── ...
```

(1) Haplotype calling 
```
mkvcf -r test_ref.fasta \
      -b lineA_sorted_reads.bam \
      -b lineB_sorted_reads.bam \
      -n lineA -n lineB \
      -p test --cpu 4(appropriately)
```

(2) Get DNA markers and design PCR primers 
```
mkprimer -r test_ref.fasta \
         -V test/vcf_2nd/Merged_filtered_variants.vcf \
         -n1 lineA -n2 lineB \
         -p test -t SNP \
         --mindep 5 --maxdep 120 --cpu 4 \
         --min_prodlen 150 --max_prodlen 280 \
         --search_span 140
```

(3) Choose an appropriate number of markers and draw their physical locations
```
mkselect -i test08/ref/test_ref.fasta.fai \
         -V test08/vcf/Merged_filtered_variants_selected_primer_added.vcf \
         -n 30
```

#### Commands

comming soon.

## References
[1] Untergasser A, Cutcutache I, Koressaar T, Ye J, Faircloth BC, Remm M and Rozen SG.
Primer3--new capabilities and interfaces.
Nucleic Acids Res. 2012 Aug 1;40(15):e115.
[2] Koressaar T and Remm M.
Enhancements and modifications of primer design program Primer3.
Bioinformatics 2007;23(10):1289-1291.
[3] Ye, J., Coulouris, G., Zaretskaya, I. et al. Primer-BLAST: A tool to design target-specific primers for polymerase chain reaction. BMC Bioinformatics 13, 134 (2012). 

