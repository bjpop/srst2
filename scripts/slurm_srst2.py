#!/usr/bin/env python
import string, re, collections
import os, sys, subprocess		
from subprocess import call, check_output, CalledProcessError, STDOUT
from argparse import (ArgumentParser, FileType)
from srst2.utils import (run_command, check_bowtie_version, check_samtools_version, CommandError)

def parse_args():
	"Parse the input arguments, use '-h' for help"

	parser = ArgumentParser(description='Submit SRST2 jobs through SLURM')

	# Job details
	parser.add_argument(
		'--walltime', type=str, required=False, help='wall time (default 0-1:0 = 1 h)', default="0-1:0")
	parser.add_argument(
		'--memory', type=str, required=False, help='mem (default 4096 = 4gb)', default="4096")
	parser.add_argument(
		'--rundir', type=str, required=False, help='directory to run in (default current dir)')
	
	# SRST2 inputs
	parser.add_argument(
		'--script', type=str, required=True, help='path to srst2 (default srst2)', default="srst")
	parser.add_argument(
		'--output', type=str, required=True, help='identifier for outputs (will be combined with read set identifiers)')
	parser.add_argument(
		'--input_se', nargs='+', type=str, required=False, help='Single end read file(s) for analysing (may be gzipped)')
	parser.add_argument(
		'--input_pe', nargs='+', type=str, required=False, help='Paired end read files for analysing (may be gzipped)')
	parser.add_argument(
		'--forward', type=str, required=False, default="_1", 
			help='Designator for forward reads (only used if NOT in MiSeq format sample_S1_L001_R1_001.fastq.gz; otherwise default is _1, i.e. expect forward reads as sample_1.fastq.gz)')
	parser.add_argument(
		'--reverse', type=str, required=False, default="_2", 
			help='Designator for reverse reads (only used if NOT in MiSeq format sample_S1_L001_R2_001.fastq.gz; otherwise default is _2, i.e. expect forward reads as sample_2.fastq.gz)')
	parser.add_argument(
		'--other_args', type=str, required=False, help='string containing all other arguments to pass to srst2')
		
	return parser.parse_args() 

def get_readFile_components(full_file_path):
	(file_path,file_name) = os.path.split(full_file_path)
	m1 = re.match("(.*).gz",file_name)
	ext = ""
	if m1 != None:
		# gzipped
		ext = ".gz"
		file_name = m1.groups()[0]
	(file_name_before_ext,ext2) = os.path.splitext(file_name)
	full_ext = ext2+ext
	return(file_path,file_name_before_ext,full_ext)

def read_file_sets(args):	

	fileSets = {} # key = id, value = list of files for that sample
	num_single_readsets = 0
	num_paired_readsets = 0
	
	if args.input_se:
		# single end
		for fastq in args.input_se:
			(file_path,file_name_before_ext,full_ext) = get_readFile_components(fastq)
			m=re.match("(.*)(_S.*)(_L.*)(_R.*)(_.*)", file_name_before_ext)
			if m==None:
				fileSets[file_name_before_ext] = [fastq]
			else:
				fileSets[m.groups()[0]] = [fastq] # Illumina names
			num_single_readsets += 1
			
	elif args.input_pe:
		# paired end
		forward_reads = {} # key = sample, value = full path to file
		reverse_reads = {} # key = sample, value = full path to file
		num_paired_readsets = 0
		num_single_readsets = 0
		for fastq in args.input_pe:
			(file_path,file_name_before_ext,full_ext) = get_readFile_components(fastq)
			# try to match to MiSeq format:
			m=re.match("(.*)(_S.*)(_L.*)(_R.*)(_.*)", file_name_before_ext)
			if m==None:
				# not default Illumina file naming format, expect simple/ENA format
				m=re.match("(.*)("+args.forward+")$",file_name_before_ext)
				if m!=None:
					# store as forward read
					(baseName,read) = m.groups()
					forward_reads[baseName] = fastq
				else:
					m=re.match("(.*)("+args.reverse+")$",file_name_before_ext)
					if m!=None:
					# store as reverse read
						(baseName,read) = m.groups()
						reverse_reads[baseName] = fastq
					else:
						print "Could not determine forward/reverse read status for input file " + fastq
			else:
				# matches default Illumina file naming format, e.g. m.groups() = ('samplename', '_S1', '_L001', '_R1', '_001')
				baseName, read  = m.groups()[0], m.groups()[3]
				if read == "_R1":
					forward_reads[baseName] = fastq
				elif read == "_R2":
					reverse_reads[baseName] = fastq
				else:
					print "Could not determine forward/reverse read status for input file " + fastq
					print "  this file appears to match the MiSeq file naming convention (samplename_S1_L001_[R1]_001), but we were expecting [R1] or [R2] to designate read as forward or reverse?"
					fileSets[file_name_before_ext] = fastq
					num_single_readsets += 1
		# store in pairs
		for sample in forward_reads:
			if sample in reverse_reads:
				fileSets[sample] = [forward_reads[sample],reverse_reads[sample]] # store pair
				num_paired_readsets += 1
			else:
				fileSets[sample] = [forward_reads[sample]] # no reverse found
				num_single_readsets += 1
				print 'Warning, could not find pair for read:' + forward_reads[sample]
		for sample in reverse_reads:
			if sample not in fileSets:
				fileSets[sample] = reverse_reads[sample] # no forward found
				num_single_readsets += 1
				print 'Warning, could not find pair for read:' + reverse_reads[sample]
				
	if num_paired_readsets > 0:
		print 'Total paired readsets found:' + str(num_paired_readsets)
	if num_single_readsets > 0:
		print 'Total single reads found:' + str(num_single_readsets)

	return fileSets

def bowtie_index(fasta_files):
	'Build a bowtie2 index from the given input fasta(s)'

	check_bowtie_version()

	for fasta in fasta_files:
		built_index = fasta + '.1.bt2'
		if os.path.exists(built_index):
			print 'Bowtie 2 index for {} is already built...'.format(fasta)
		else:
			print 'Building bowtie2 index for {}...'.format(fasta)
			run_command(['bowtie2-build', fasta, fasta])
			
def samtools_index(fasta_files):
	'Build a samtools faidx index from the given input fasta(s)'

	# check that both samtools has the right version
	check_samtools_version()

	for fasta in fasta_files:
		built_index = fasta + '.fai'
		if os.path.exists(built_index):
			print 'Samtools index for {} is already built...'.format(fasta)
		else:
			print 'Building samtools faidx index for {}...'.format(fasta)
			run_command(['samtools', 'faidx', fasta])

def main():

	args = parse_args()

	if not args.rundir:
		args.rundir = os.getcwd()

	# parse list of file sets to analyse
	fileSets = read_file_sets(args) # get list of files to process
	
	# make sure the databases are formated for bowtie2 and samtools before running the jobs
	db = []
	m = re.search( r'(--mlst_db) (.*?) .*', args.other_args)
	if m != None:
		db.append(m.group(2))
	g = re.search( r'(--gene_db) (.*?) --', args.other_args)
	if g != None:
		db += g.group(2).split()
	else:
		g = re.search( r'(--gene_db) (.*?)$', args.other_args)
		if g != None:
			db += g.group(2).split()
	bowtie_index(db)
	samtools_index(db)
	
	# build and submit commands
	for sample in fileSets:		
		cmd = "#!/bin/bash"
		cmd += "\n#SBATCH -p main"
		cmd += "\n#SBATCH --job-name=srst2" + sample + args.output
		cmd += "\n#SBATCH --ntasks=1"
		cmd += "\n#SBATCH --mem-per-cpu=" + args.memory
		cmd += "\n#SBATCH --time=" + args.walltime
		cmd += "\ncd " + args.rundir
		cmd += "\nmodule load bowtie2-intel/2.1.0"
		cmd += "\nmodule load samtools-intel/0.1.18"
		cmd += "\nmodule load python-gcc"
		cmd += "\n" + args.script
		fastq = fileSets[sample]
		if len(fastq) > 1:
			cmd += " --input_pe " + fastq[0] + " " + fastq[1]
			cmd += " --forward " + args.forward
			cmd += " --reverse " + args.reverse
		else:
			cmd += " --input_se " + fastq[0]
		cmd += " --output " + sample + "_" + args.output
		cmd += " --log"
		cmd += " " + args.other_args
		
		# print and run command
		print cmd
		os.system('echo "' + cmd + '" | sbatch')

if __name__ == '__main__':
	main()
