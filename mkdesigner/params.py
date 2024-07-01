import argparse
import sys
import os
from mkdesigner.__init__ import __version__

class Params(object):

    def __init__(self, program_name):
        self.program_name = program_name

    def set_options(self):
        if self.program_name == 'mkvcf':
            parser = self.mkvcf_options()
        elif self.program_name == 'mkprimer':
            parser = self.mkprimer_options()
        elif self.program_name == 'mkselect':
            parser = self.mkselect_options()

        if len(sys.argv) == 1:
            args = parser.parse_args(['-h'])
        else:
            args = parser.parse_args()
        return args
    
    def mkvcf_options(self):
        parser = argparse.ArgumentParser(description='MKDesigner version {}'.format(__version__),
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.usage = ('mkvcf -r <FASTA> -b <BAM_1> -b <BAM_2>... -n <name_1> -n <name_2>... -O <STRING>\n')

        # set options
        parser.add_argument('-r', '--ref',
                            action='store',
                            required=True,
                            type=str,
                            help='Reference fasta.',
                            metavar='')

        parser.add_argument('-b', '--bam',
                            action='append',
                            required=True,
                            type=str,
                            help=('Bam files for variant calling.\n'
                                  'e.g. -b bam1 -b bam2 ... \n'
                                  'You must use this option 2 times or more\n'
                                  'to get markers in following analysis.'),
                            metavar='')
        
        parser.add_argument('-n', '--name',
                            action='append',
                            required=True,
                            type=str,
                            help=('Variety name of each bam file.\n'
                                  'e.g. -n name_bam1 -n name_bam2 ... \n'
                                  'You must use this option same times\n'
                                  'as -b.'),
                            metavar='')
        
        parser.add_argument('-O', '--output',
                            action='store',
                            required=True,
                            type=str,
                            help=('Identical name (must be unique).\n'
                                  'This will be stem of output directory name.'),
                            metavar='')
                            
        parser.add_argument('--cpu',
                            action='store',
                            default=2,
                            type=int,
                            help=('Number of CPUs to use.\n'),
                            metavar='')
        
        # set version
        parser.add_argument('-v', '--version',
                            action='version',
                            version='%(prog)s {}'.format(__version__))
        return parser
        
    def mkprimer_options(self):
        parser = argparse.ArgumentParser(description='MKDesigner version {}'.format(__version__),
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.usage = ('mkprimer -r <FASTA> -V <VCF> -n1 <name1> -n2 <name2>\n'
                        '         -O <output name> --type <SNP or INDEL>\n'
                        '         [--target <Target position>]\n'
                        '         [--mindep <INT>] [--maxdep <INT>]\n'
                        '         [--min_prodlen <INT>] [--max_prodlen <INT>]\n'
                        '         [--margin <INT>] [--max_distance <INT>]')

        # set options
        parser.add_argument('-r', '--ref',
                            action='store',
                            required=True,
                            type=str,
                            help='Reference fasta.',
                            metavar='')

        parser.add_argument('-V', '--vcf',
                            action='store',
                            required=True,
                            type=str,
                            help=('VCF file without filtering.\n'
                                  'Recommended to use VCF made by "mkvcf" command.\n'
                                  'VCF must contain GT and DP field.'),
                            metavar='')
        
        parser.add_argument('-n1', '--name1',
                            action='append',
                            required=True,
                            type=str,
                            help=('Variety name 1.\n'
                                  'Must match VCF column names.\n'
                                  'This parameter can be specified multiple times to design common markers for multiple varieties.\n'),
                            metavar='')
        
        parser.add_argument('-n2', '--name2',
                            action='append',
                            required=True,
                            type=str,
                            help=('Variety name 2.\n'
                                  'Must match VCF column names.\n'
                                  'This parameter can be specified multiple times to design common markers for multiple varieties.\n'),
                            metavar='')
        
        parser.add_argument('-O', '--output',
                            action='store',
                            required=True,
                            type=str,
                            help=('Identical name (must be unique).\n'
                                  'This will be stem of output directory name.'),
                            metavar='')
        
        parser.add_argument('-T', '--type',
                            action='store',
                            required=True,
                            choices=['SNP',  'INDEL'],
                            help=('Type of variants.\n'
                                  'SNP or INDEL are supported.'),
                            metavar='')
        
        parser.add_argument('-t', '--target',
                            action='append',
                            default=None,
                            type=str,
                            help=('Target position where primers designed/\n'
                                  'e.g. "chr01:1000000-3500000"\n'
                                  'If not specified, the program process whole genome.\n'
                                  'This parameter can be specified multiple times.'),
                            metavar='')
        
        parser.add_argument('--mindep',
                            action='store',
                            default=2,
                            type=int,
                            help=('Variants with more depth than this\n'
                                  'are judged as valid mutations\ndefault: 2'),
                            metavar='')
        
        parser.add_argument('--maxdep',
                            action='store',
                            default=200,
                            type=int,
                            help=('Variants with less depth than this\n'
                                  'are judged as valid mutations\ndefault: 200'),
                            metavar='')
        
        parser.add_argument('--mismatch_allowed',
                            action='store',
                            default=5,
                            type=int,
                            help=('Primers with more mismatch than this\n'
                                  'are ignored in specificity check.\ndefault: 5'),
                            metavar='')  
        
        parser.add_argument('--mismatch_allowed_3_terminal',
                            action='store',
                            default=1,
                            type=int,
                            help=('Primers with more mismatch than this\n'
                                  'in 5 bases of 3\' terminal end\n'
                                  'are ignored in specificity check.\ndefault: 1'),
                            metavar='')  
        
        parser.add_argument('--unintended_prod_size_allowed',
                            action='store',
                            default=4000,
                            type=int,
                            help=('Primer pairs producing unintended PCR product which is shorter than this\n'
                                  'are ignored in specificity check.\ndefault: 4000'),
                            metavar='')  
        
        parser.add_argument('--min_prodlen',
                            action='store',
                            default=150,
                            type=int,
                            help=('Minimum PCR product length.default: 150'),
                            metavar='')
        
        parser.add_argument('--max_prodlen',
                            action='store',
                            default=280,
                            type=int,
                            help=('Maximam PCR product length.\ndefault: 280'),
                            metavar='')
        
        parser.add_argument('--opt_prodlen',
                            action='store',
                            default=180,
                            type=int,
                            help=('Optical PCR product length.\ndefault: 180'),
                            metavar='')

        parser.add_argument('--margin',
                            action='store',
                            default=5,
                            type=int,
                            help=('Minimum distance from 3\' terminal of primer to variant.\ndefault: 5'),
                            metavar='')
        
        parser.add_argument('--search_span',
                            action='store',
                            default=140,
                            type=int,
                            help=('Intervals to search for primers upstream and downstream variants.\ndefault: 140'),
                            metavar='')
        
        parser.add_argument('--primer_num_consider',
                            action='store',
                            default=3,
                            type=int,
                            help=('Primer number considering in primer3 software.\ndefault: 3'),
                            metavar='')

        parser.add_argument('--primer_min_size',
                            action='store',
                            default=18,
                            type=int,
                            help=('Minimum primer size\ndefault: 18'),
                            metavar='')

        parser.add_argument('--primer_max_size',
                            action='store',
                            default=26,
                            type=int,
                            help=('Maximum primer size\ndefault: 26'),
                            metavar='')

        parser.add_argument('--primer_opt_size',
                            action='store',
                            default=20,
                            type=int,
                            help=('Optical primer size\ndefault: 20'),
                            metavar='')
        
        parser.add_argument('--cpu',
                            action='store',
                            default=2,
                            type=int,
                            help=('Number of CPUs to use.\n'),
                            metavar='')
        # set version
        parser.add_argument('-v', '--version',
                            action='version',
                            version='%(prog)s {}'.format(__version__))
        return parser
        
    def mkselect_options(self):
        parser = argparse.ArgumentParser(description='MKDesigner version {}'.format(__version__),
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.usage = ('mkselect -i <FASTA Index file>\n'
                        '         -V <VCF with Primer> -n <INT>\n'
                        '         -O <STRING>\n'
                        '         [-t <Target position>]\n'
                        '         [-d <TSV with marker density infomation>]\n'
                        '         [--avoid_lowercase]\n')
        
        # set options
        parser.add_argument('-i', '--fai',
                            action='store',
                            required=True,
                            type=str,
                            help='Index file (.fai) of reference fasta.',
                            metavar='')

        parser.add_argument('-V', '--vcf',
                            action='store',
                            required=True,
                            type=str,
                            help=('VCF file with primers.\n'
                                  'This file must be made by "mkprimer" command.'),
                            metavar='')
        
        parser.add_argument('-n', '--num_marker',
                            action='store',
                            required=True,
                            type=int,
                            help=('Number of markers selected.'),
                            metavar='')
        
        parser.add_argument('-O', '--output',
                            action='store',
                            required=True,
                            type=str,
                            help=('Identical name (must be unique).\n'
                                  'This will be stem of output directory name.'),
                            metavar='')
        
        parser.add_argument('-t', '--target',
                            action='append',
                            default=None,
                            type=str,
                            help=('Target position where primers designed\n'
                                  'e.g. "chr01:1000000-3500000"\n'
                                  'This parameter can be specified multiple times.'),
                            metavar='')
        
        parser.add_argument('-d', '--density',
                            action='store',
                            default=None,
                            type=str,
                            help=('TSV file with marker density infomation..\n'
                                  'This file must be formatted as "test/density.tsv".'),
                            metavar='')
        
        parser.add_argument('--mindif',
                            action='store',
                            default=0,
                            type=int,
                            help=('Set minimum differences\n'
                                  'of PCR product length between alleles.\n'
                                  'For SNP marker, this must be 0.'),
                            metavar='')
        
        parser.add_argument('--maxdif',
                            action='store',
                            default=50,
                            type=int,
                            help=('For indel marker, set maximum differences\n'
                                  'of PCR product length between alleles.'),
                            metavar='')
        
        parser.add_argument('--avoid_lowercase',
                            action='store_true',
                            help=('Select only primers written by uppercase.\n'
                                  'Lowercase may mean repeat sequence.'))

        # set version
        parser.add_argument('-v', '--version',
                            action='version',
                            version='%(prog)s {}'.format(__version__))
        return parser
    
    def mkvcf_check_args(self, args):
        #Does a project file with the same name exist?
        if os.path.isdir('{}_mkvcf'.format(args.output)):
            sys.stderr.write(('  Output directory already exist.\n'
                              '  Please rename the --output.\n'))
            sys.exit(1)

        if not os.path.isfile('{}'.format(args.ref)):
            sys.stderr.write('  Input reference FASTA does not exist.\n')
            sys.exit(1)

        #Do BAM files exist?
        #Is the extentions of files designeated as BAM really '.bam' ?
        for input_name in args.bam:
                if not os.path.isfile('{}'.format(input_name)):
                    sys.stderr.write('  At least one of input BAM does not exist.\n')
                    sys.exit(1)
                ext = os.path.splitext(input_name)
                if ext[-1] != '.bam':
                    sys.stderr.write(('  Please check input BAM file "{}".\n'
                                      '  The extension of this file is not "bam".\n').format(input_name))
                    sys.exit(1)

        #Do the number of BAM and the number of names match?
        if len(args.bam) != len(args.name) :
            sys.stderr.write(('  Number of input BAM files is not'
                              '  matched the number of names.\n\n'))
            sys.exit(1)

        #Names must be unique.
        name_unique = set(args.name)
        if len(args.name) != len(name_unique) :
            sys.stderr.write(('  Variety names must not be duplicated.\n\n'))
            sys.exit(1)

    def mkprimer_check_args(self, args):
        #Does a project file with the same name exist?
        if os.path.isdir('{}_mkprimer'.format(args.output)):
            sys.stderr.write(('  Output directory already exist.\n'
                              '  Please rename the --output.\n'))
            sys.exit(1)
        if not os.path.isfile('{}'.format(args.vcf)):
            sys.stderr.write('  Input VCF does not exist.\n')
            sys.exit(1)
        if not os.path.isfile('{}'.format(args.ref)):
            sys.stderr.write('  Input reference FASTA does not exist.\n')
            sys.exit(1)

    def mkselect_check_args(self, args):
        #Does a directory with the same name exist?
        if os.path.isdir('{}_mkselect'.format(args.output)):
            sys.stderr.write(('  Output directory already exist.\n'
                              '  Please rename the --output.\n'))
            sys.exit(1)
        if not os.path.isfile('{}'.format(args.vcf)):
            sys.stderr.write('  Input VCF does not exist.\n')
            sys.exit(1)
        if not os.path.isfile('{}'.format(args.fai)):
            sys.stderr.write('  Input FASTA index does not exist.\n')
            sys.exit(1)
        if args.density != None:
            if not os.path.isfile('{}'.format(args.density)):
                sys.stderr.write(' Input file for adjusting marker density does not exist.\n')
                sys.exit(1)

