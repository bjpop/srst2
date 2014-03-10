#!/usr/bin/env python

'''
Graphical User Interface for SRST2, the Short Read Sequence Typer

Authors:
    Michael Inouye (minouye@unimelb.edu.au)
    Harriet Dashnow (h.dashnow@gmail.com)
    Kathryn Holt (kholt@unimelb.edu.au)
    Bernie Pope (bjpope@unimelb.edu.au)

See LICENSE.txt for the license
'''

import logging
from argparse import Namespace
from srst2 import main_args
from Tkinter import (Tk, StringVar, Entry, LabelFrame, Label,
    Button, OptionMenu, IntVar, Radiobutton, Frame, DoubleVar,
    Spinbox, N, S, E, W, LEFT, RIGHT, Text, BooleanVar, DISABLED,
    NORMAL)
import tkFileDialog

try:
    from version import srst2_version
except:
    srst2_version = "version unknown"

DEFAULT_FORWARD = "_1"
DEFAULT_REVERSE = "_2"
DEFAULT_READ_TYPE = "fastq"
DEFAULT_MLST_DELIMITER = "-"
DEFAULT_MIN_DEPTH = 5.0 
DEFAULT_MIN_EDGE_DEPTH = 2.0 
DEFAULT_MAX_DIVERGENCE = 10.0
DEFAULT_MIN_COVERAGE = 90
DEFAULT_SAMTOOLS_MAPQ = 1
DEFAULT_SAMTOOLS_BASEQ = 20
SPIN_BOX_WIDTH = 4
LABEL_FRAME_PAD = 10
FILE_ENTRY_WIDTH = 40
DEFAULT_PROB_ERROR = 0.01
DEFAULT_OUTPUT = 'srst2'

def get_one_file(value):
    result = None
    if isinstance(value, str) and len(value.strip()) > 0:
        result = value.strip()
    return result

def get_filenames_tuple(value):
    result = None
    if isinstance(value, str) and len(value.strip()) > 0:
        result = tuple(value.strip())
    elif isinstance(value, tuple):
        result = value 
    return result

def get_default(value, default):
    if value:
        return value
    else:
        return default

class Gui(Tk):
    def __init__(self,parent):
        Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    # XXX should common these together

    def ask_single_end(self):
        filename = tkFileDialog.askopenfilenames()
        self.single_end_variable.set(filename)

    def ask_paired_end(self):
        filename = tkFileDialog.askopenfilenames()
        self.paired_end_variable.set(filename)

    def ask_mlst_db(self):
        filename = tkFileDialog.askopenfilename()
        self.mlst_db_variable.set(filename)

    def ask_mlst_defs(self):
        filename = tkFileDialog.askopenfilename()
        self.mlst_defs_variable.set(filename)

    def ask_gene_db(self):
        filename = tkFileDialog.askopenfilenames()
        self.gene_db_variable.set(filename)

    def ask_previous_outputs(self):
        filename = tkFileDialog.askopenfilenames()
        self.previous_outputs_variable.set(filename)

    def run(self):
        self.run_button['state'] = DISABLED
        args = Namespace()

        # XXX is it okay if both of these are set?
        args.input_se = get_filenames_tuple(self.single_end_variable.get())
        args.input_pe = get_filenames_tuple(self.paired_end_variable.get())

        args.forward = get_default(self.forward_variable.get(), DEFAULT_FORWARD) 
        args.reverse = get_default(self.reverse_variable.get(), DEFAULT_REVERSE) 

        read_type_map = {'fastq':'q', 'solexa':'qseq', 'fasta':'f'}
        args.read_type = read_type_map[self.read_type_variable.get()]

        args.mlst_db = get_one_file(self.mlst_db_variable.get())
        args.mlst_definitions = get_one_file(self.mlst_defs_variable.get())
        args.mlst_delimiter = get_default(self.mlst_delimiter_variable.get(), DEFAULT_MLST_DELIMITER)

        args.gene_db = get_filenames_tuple(self.gene_db_variable.get())
        args.no_gene_details = bool(self.no_gene_details_variable.get())

        args.min_coverage = get_default(self.min_coverage_variable.get(), DEFAULT_MIN_COVERAGE)
        args.max_divergence = get_default(self.max_divergence_variable.get(), DEFAULT_MAX_DIVERGENCE)
        args.min_depth = get_default(self.min_depth_variable.get(), DEFAULT_MIN_DEPTH)
        args.min_edge_depth = get_default(self.min_edge_depth_variable.get(), DEFAULT_MIN_EDGE_DEPTH)
        args.prob_err = get_default(self.prob_error_variable.get(), DEFAULT_PROB_ERROR)

        args.stop_after = get_default(self.bowtie_stop_after_variable.get(), None) 
        args.other = get_default(self.bowtie_other_variable.get(), None) 

        args.mapq = get_default(self.samtools_mapq_variable.get(), DEFAULT_SAMTOOLS_MAPQ)
        args.baseq = get_default(self.samtools_baseq_variable.get(), DEFAULT_SAMTOOLS_BASEQ)

        args.output = get_default(self.output_prefix_variable.get(), DEFAULT_OUTPUT)
        args.log = bool(self.log_variable.get()) 
        args.save_scores = bool(self.save_scores_variable.get())

        args.use_existing_pileup = bool(self.use_existing_pileup_variable.get()) 
        args.use_existing_scores = bool(self.use_existing_scores_variable.get())
        args.prev_output = get_filenames_tuple(self.previous_outputs_variable.get())
 
        main_args(args)
        self.run_button['state'] = NORMAL 


    def quit(self):
        self.destroy()

    def initialize(self):

        self.columnconfigure(0, weight=1, pad=20)
        self.columnconfigure(1, weight=1, pad=20)
        self.rowconfigure(0, weight=1, pad=20)
        self.rowconfigure(1, weight=1, pad=20)
        self.rowconfigure(2, weight=1, pad=20)

        title = Label(self, text="SRST2: Short Read Sequence Typer {}".format(srst2_version))
        title.grid(row=0, columnspan=2)

        left_column = Frame(self)
        left_column.grid(row=1, column=0) 
        right_column = Frame(self)
        right_column.grid(row=1, column=1) 

        inputs_frame = LabelFrame(left_column, text="Input Reads Options:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        inputs_frame.pack(side="top", fill="both", expand=True)

        row = 0

        Label(inputs_frame, text="Single End:").grid(row=row, column=0, sticky=W)
        self.single_end_variable = StringVar(self) 
        Entry(inputs_frame, textvariable=self.single_end_variable, width=FILE_ENTRY_WIDTH).grid(row=row, column=1) 
        Button(inputs_frame, text='Choose Files', command=self.ask_single_end).grid(row=row, column=2)
        row += 1

        Label(inputs_frame, text="Paried End:").grid(row=row, column=0, sticky=W)
        self.paired_end_variable = StringVar(self) 
        Entry(inputs_frame, textvariable=self.paired_end_variable, width=FILE_ENTRY_WIDTH).grid(row=row, column=1) 
        Button(inputs_frame, text='Choose Files', command=self.ask_paired_end).grid(row=row, column=2)
        row += 1

        Label(inputs_frame, text="Forward:").grid(row=row, column=0, sticky=W)
        self.forward_variable = StringVar(self)
        self.forward_variable.set(DEFAULT_FORWARD)
        Entry(inputs_frame, textvariable=self.forward_variable, width=5).grid(row=row, column=1, sticky=W)
        row += 1

        Label(inputs_frame, text="Reverse:").grid(row=row, column=0, sticky=W)
        self.reverse_variable = StringVar(self)
        self.reverse_variable.set(DEFAULT_REVERSE)
        Entry(inputs_frame, textvariable=self.reverse_variable, width=5).grid(row=row, column=1, sticky=W)
        row += 1

        Label(inputs_frame, text="Read Type:").grid(row=row, column=0, sticky=W)
        self.read_type_variable = StringVar(self)
        self.read_type_variable.set(DEFAULT_READ_TYPE)
        OptionMenu(inputs_frame, self.read_type_variable, "fastq", "solexa", "fasta").grid(row=row, column=1, sticky=W)
        row += 1

        mlst_frame = LabelFrame(left_column, text="MLST Database Options:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        mlst_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(mlst_frame, text="Database:").grid(row=row, column=0, sticky=W)
        self.mlst_db_variable = StringVar(self) 
        Entry(mlst_frame, textvariable=self.mlst_db_variable, width=FILE_ENTRY_WIDTH).grid(row=row, column=1) 
        Button(mlst_frame, text='Choose File', command=self.ask_mlst_db).grid(row=row, column=2)
        row += 1

        Label(mlst_frame, text="Definitions:").grid(row=row, column=0, sticky=W)
        self.mlst_defs_variable = StringVar(self) 
        Entry(mlst_frame, textvariable=self.mlst_defs_variable, width=FILE_ENTRY_WIDTH).grid(row=row, column=1) 
        Button(mlst_frame, text='Choose File', command=self.ask_mlst_defs).grid(row=row, column=2)
        row += 1

        Label(mlst_frame, text="Delimiter:").grid(row=row, column=0, sticky=W)
        self.mlst_delimiter_variable = StringVar(self)
        self.mlst_delimiter_variable.set(DEFAULT_MLST_DELIMITER)
        Entry(mlst_frame, textvariable=self.mlst_delimiter_variable, width=5).grid(row=row, column=1, sticky=W)
        row += 1

        gene_frame = LabelFrame(left_column, text="Gene Database Options:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        gene_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(gene_frame, text="Database:").grid(row=row, column=0, sticky=W)
        self.gene_db_variable = StringVar(self) 
        Entry(gene_frame, textvariable=self.gene_db_variable, width=FILE_ENTRY_WIDTH).grid(row=row, column=1) 
        Button(gene_frame, text='Choose Files', command=self.ask_gene_db).grid(row=row, column=2)
        row += 1

        Label(gene_frame, text="No Gene Details:").grid(row=row, column=0, sticky=W)
        self.no_gene_details_variable = IntVar(self)
        gene_radio_frame = Frame(gene_frame)
        gene_radio_frame.grid(row=row, column=1, sticky=W)
        Radiobutton(gene_radio_frame, text="Yes", variable=self.no_gene_details_variable, value=1).grid(row=0, column=0, sticky=W)
        Radiobutton(gene_radio_frame, text="No", variable=self.no_gene_details_variable, value=0).grid(row=0, column=1, sticky=W)

        previous_outputs_frame = LabelFrame(left_column, text="Previous Outputs:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        previous_outputs_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(previous_outputs_frame, text="Files:").grid(row=row, column=0, sticky=W)
        self.previous_outputs_variable = StringVar(self) 
        Entry(previous_outputs_frame, textvariable=self.previous_outputs_variable, width=FILE_ENTRY_WIDTH).grid(row=row, column=1) 
        Button(previous_outputs_frame, text='Choose Files', command=self.ask_previous_outputs).grid(row=row, column=2)
        row += 1

        cutoff_frame = LabelFrame(right_column, text="Cutoffs for scoring/heuristics:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        cutoff_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(cutoff_frame, text="Min Coverage:").grid(row=row, column=0, sticky=W)
        self.min_coverage_variable = DoubleVar(self)
        self.min_coverage_variable.set(DEFAULT_MIN_COVERAGE)
        Spinbox(cutoff_frame, textvariable=self.min_coverage_variable,
            from_=0, to=10**6, increment=1.0, width=SPIN_BOX_WIDTH).grid(row=row, column=1) 
        row += 1

        Label(cutoff_frame, text="Max Divergence:").grid(row=row, column=0, sticky=W)
        self.max_divergence_variable = DoubleVar(self)
        self.max_divergence_variable.set(DEFAULT_MAX_DIVERGENCE)
        Spinbox(cutoff_frame, textvariable=self.max_divergence_variable,
            from_=0, to=10**6, width=SPIN_BOX_WIDTH).grid(row=row, column=1) 
        row += 1

        Label(cutoff_frame, text="Min Depth:").grid(row=row, column=0, sticky=W)
        self.min_depth_variable = DoubleVar(self)
        self.min_depth_variable.set(DEFAULT_MIN_DEPTH)
        Spinbox(cutoff_frame, textvariable=self.min_depth_variable,
            from_=0, to=10**6, width=SPIN_BOX_WIDTH).grid(row=row, column=1) 
        row += 1

        Label(cutoff_frame, text="Min Edge Depth:").grid(row=row, column=0, sticky=W)
        self.min_edge_depth_variable = DoubleVar(self)
        self.min_edge_depth_variable.set(DEFAULT_MIN_EDGE_DEPTH)
        Spinbox(cutoff_frame, textvariable=self.min_edge_depth_variable,
            from_=0, to=10**6, width=SPIN_BOX_WIDTH).grid(row=row, column=1) 
        row += 1

        Label(cutoff_frame, text="Error Probability:").grid(row=row, column=0, sticky=W)
        self.prob_error_variable = DoubleVar(self)
        self.prob_error_variable.set(DEFAULT_PROB_ERROR)
        Spinbox(cutoff_frame, textvariable=self.prob_error_variable,
            from_=0, to=1.0, increment=0.01, width=SPIN_BOX_WIDTH, format='%0.2f').grid(row=row, column=1) 
        row += 1

        bowtie_frame = LabelFrame(right_column, text="Bowtie Options:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        bowtie_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(bowtie_frame, text="Stop After:").grid(row=row, column=0, sticky=W)
        self.bowtie_stop_after_variable = StringVar(self)
        Entry(bowtie_frame, textvariable=self.bowtie_stop_after_variable, width=5).grid(row=row, column=1, sticky=W) 
        row += 1

        Label(bowtie_frame, text="Other options:").grid(row=row, column=0, sticky=W)
        self.bowtie_other_variable = StringVar(self)
        Entry(bowtie_frame, textvariable=self.bowtie_other_variable).grid(row=row, column=1) 
        row += 1

        samtools_frame = LabelFrame(right_column, text="Samtools Options:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        samtools_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(samtools_frame, text="mapq:").grid(row=row, column=0, sticky=W)
        self.samtools_mapq_variable = IntVar(self)
        self.samtools_mapq_variable.set(DEFAULT_SAMTOOLS_MAPQ)
        Spinbox(samtools_frame, textvariable=self.samtools_mapq_variable,
            from_=0, to=10**6, width=SPIN_BOX_WIDTH).grid(row=row, column=1) 
        row += 1

        Label(samtools_frame, text="baseq:").grid(row=row, column=0, sticky=W)
        self.samtools_baseq_variable = IntVar(self)
        self.samtools_baseq_variable.set(DEFAULT_SAMTOOLS_BASEQ)
        Spinbox(samtools_frame, textvariable=self.samtools_baseq_variable,
            from_=0, to=10**6, width=SPIN_BOX_WIDTH).grid(row=row, column=1) 
        row += 1

        reporting_frame = LabelFrame(right_column, text="Reporting Options:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        reporting_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(reporting_frame, text="Output Prefix:").grid(row=row, column=0, sticky=W)
        self.output_prefix_variable = StringVar(self)
        self.output_prefix_variable.set(DEFAULT_OUTPUT)
        Entry(reporting_frame, textvariable=self.output_prefix_variable).grid(row=row, column=1) 
        row += 1

        Label(reporting_frame, text="Log:").grid(row=row, column=0, sticky=W)
        self.log_variable = IntVar(self)
        log_radio_frame = Frame(reporting_frame)
        log_radio_frame.grid(row=row, column=1, sticky=W)
        Radiobutton(log_radio_frame, text="Yes", variable=self.log_variable, value=1).grid(row=0, column=0, sticky=W)
        Radiobutton(log_radio_frame, text="No", variable=self.log_variable, value=0).grid(row=0, column=1, sticky=W)
        row += 1

        Label(reporting_frame, text="Save scores:").grid(row=row, column=0, sticky=W)
        self.save_scores_variable = IntVar(self)
        save_scores_radio_frame = Frame(reporting_frame)
        save_scores_radio_frame.grid(row=row, column=1, sticky=W)
        Radiobutton(save_scores_radio_frame, text="Yes", variable=self.save_scores_variable, value=1).grid(row=0, column=0, sticky=W)
        Radiobutton(save_scores_radio_frame, text="No", variable=self.save_scores_variable, value=0).grid(row=0, column=1, sticky=W)
        row += 1

        run_options_frame = LabelFrame(right_column, text="Run Options:", padx=LABEL_FRAME_PAD, pady=LABEL_FRAME_PAD)
        run_options_frame.pack(side="top", fill="both", expand=True)
        row = 0

        Label(run_options_frame, text="Use Existing Pileup:").grid(row=row, column=0, sticky=W)
        self.use_existing_pileup_variable = IntVar(self)
        use_existing_pileup_radio_frame = Frame(run_options_frame)
        use_existing_pileup_radio_frame.grid(row=row, column=1, sticky=W)
        Radiobutton(use_existing_pileup_radio_frame, text="Yes", variable=self.use_existing_pileup_variable, value=1).grid(row=0, column=0, sticky=W)
        Radiobutton(use_existing_pileup_radio_frame, text="No", variable=self.use_existing_pileup_variable, value=0).grid(row=0, column=1, sticky=W)
        row += 1

        Label(run_options_frame, text="Use Existing Scores:").grid(row=row, column=0, sticky=W)
        self.use_existing_scores_variable = IntVar(self)
        use_existing_scores_radio_frame = Frame(run_options_frame)
        use_existing_scores_radio_frame.grid(row=row, column=1, sticky=W)
        Radiobutton(use_existing_scores_radio_frame, text="Yes", variable=self.use_existing_scores_variable, value=1).grid(row=0, column=0, sticky=W)
        Radiobutton(use_existing_scores_radio_frame, text="No", variable=self.use_existing_scores_variable, value=0).grid(row=0, column=1, sticky=W)
        row += 1

        action_frame = Frame(self)
        action_frame.grid(row=2, columnspan=2)

        self.run_button = Button(action_frame, text='Run', command=self.run)
        self.run_button.grid(row=0, column=0)
        quit_button = Button(action_frame, text='Quit', command=self.quit)
        quit_button.grid(row=0, column=1)


def main():
    app = Gui(None)
    app.title('SRST2 version {}'.format(srst2_version))
    app.mainloop()


if __name__ == "__main__":
    main()
