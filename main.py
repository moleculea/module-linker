#! /usr/bin/env python
# -*- coding: utf-8  -*-
import argparse
import sys
import os
import re
import collections
from scripts import utilities
from scripts.linker import *

def checkVersion():
    version = sys.version_info
    if version[0] == 2:
        if version[1] < 7:
            utilities.output.error("Python 2.%d installed. This app requires Python 2.7."%(version[1]))
            sys.exit(1)
    if version[0] == 3:
            utilities.output.error("Python 3.%d installed. This app requires Python 2.7."%(version[1]))
            sys.exit(1)

def getArgs():
    """Parse command-line arguments with optional functionalities"""
    
    parser = argparse.ArgumentParser(
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Link multiple modules into a single module", 
                                     usage='%(prog)s [-prv] input_file [output_file]',
                                     epilog="usage examples: \n\
  %(prog)s input.txt output.txt       (save output without printing)\n\
  %(prog)s -p input.txt output.txt    (print formatted output)\n\
  %(prog)s -pr input.txt output.txt   (print human readable output)\n\
  %(prog)s -v input.txt output.txt    (print verbose debug information)\n\
  %(prog)s input.txt                  (simply print output without saving)\n"
                                     )
    parser.add_argument('input_file', help="/path/to/input-file.txt")
    parser.add_argument('output_file', nargs='?', help="/path/to/output-file.txt; if not given, print to standard output")
    parser.add_argument('-p','--print', action="store_true", dest="to_print", help="print output file content to standard output")
    parser.add_argument('-r','--human', action="store_true", dest="to_human", help="print human readable output to standard output")
    parser.add_argument('-v','--verbose', action="store_true", dest="to_verbose", help="print verbose information")
    
    # if no argument is given, print help message
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    
    input_file, output_file, to_print, to_human, to_verbose = \
    args.input_file, args.output_file, args.to_print, args.to_human, args.to_verbose

    return input_file, output_file, to_print, to_human, to_verbose

def checkPaths(input_file, output_file, verbose=False):
    """Check validity of paths of input file and output file """
    abs_path = os.path.abspath(input_file)  # absolute path of input file
    out_path = None  # absolute path of output file
    if verbose:
        utilities.output.debug("Input file name: %s." %abs_path)
    if os.path.isfile(abs_path):
        pass
    else:
        if os.path.exists(abs_path):
            if os.path.isdir:
                utilities.output.error("Input file \"%s\" is a directory, not a file." % abs_path)
                sys.exit(1)
        else:
            utilities.output.error("Input file \"%s\" does not exist." % abs_path)
            sys.exit(1)

    if output_file:
        if output_file in ['/', '.', '..', './', '../'] or output_file.endswith('/'):
            utilities.output.error("Output file must be a file not a directory")
            sys.exit(1)
        out_path = os.path.abspath(output_file)
        dir_name = os.path.dirname(out_path)
        if os.path.exists(dir_name):
            if os.path.isfile(out_path):
                utilities.output.warning("Output file \"%s\" already exists." % out_path)
                s = raw_input("Overwrite (1), keep both (2) or cancel (3)? ")
                flag, out_path = _promptOutput(s, out_path)
                
                while flag == False:
                    ns = raw_input("Please input 1, 2, or 3: ")
                    flag, out_path = _promptOutput(ns, out_path)   
            else:
                pass
        else:
            utilities.output.error("Base directory for output file \"%s\" dose not exist." % out_path)
            sys.exit(1)
                
    return abs_path, out_path
            
def _promptOutput(s, out_path):
    flag = True
    if s == '1':
        pass
    elif s == '2':
        fn, ext = os.path.splitext(out_path)
        out_path = _keepBoth(out_path)
    elif s == '3':
        sys.exit(1)
    else:
        flag = False
    return (flag, out_path)

def _keepBoth(out_path):
    """
    Increment the tag (n) of the duplicate filename
        e.g.: output_file_name(1).txt --> output_file_name(2).txt 
    """
    fn, ext = os.path.splitext(out_path)
    
    dir_fn = os.path.splitext(os.path.split(out_path)[1])[0]
    
    dir_file_list = os.listdir(os.path.dirname(out_path))
    max_dup_num = 1

    for df in dir_file_list:
        m = re.search("%s\((\d+)\)%s" % (dir_fn, ext), df)
        if m:
            num = int(m.group(1)) + 1
            if num > max_dup_num:
                max_dup_num = num
                
    out_path = fn + "(%d)" % max_dup_num + ext 
    return out_path

def readInput(input_file, verbose=False):
    f = None
    text = ""
    try:
        if verbose:
            utilities.output.debug("Opening input file \"%s\"..." %input_file)
        f = open(input_file, "r")
        text = f.read()
        f.close()
        
    except:
        utilities.output.error("Cannot open the file \"%s\"" % input_file)
        sys.exit(1)
    
    finally:
        f.close()
        
    #print text
    return text

def splitInput(text, verbose=False):
    if verbose:
        utilities.output.debug("Reading input file...")
    s = text.split()
    return s

def parseList(raw_list, verbose=False):
    """
    Parse raw_list into a list of module objects
    """
    count = 0
    modules = []
    mod = None  # declare a local variable for module objects
    base = 0    # base address for modules
    try:
        if verbose:
            utilities.output.debug("Parsing module structure of input file...")        
        while raw_list:
            ind = count % 3
            num = count / 3 + 1
            if ind == 0:
                mod = Module(num, base)   # instantiate a module object at the first stage
                mod.def_list = _parseDeflist(raw_list, num)
            if ind == 1:
                mod.use_list = _parseUselist(raw_list, num)
            if ind == 2:
                mod.code = _parseCode(raw_list, num)
                modules.append(mod)        # append module into modules list at the last parse stage
                base = mod.next_address    # next base address
            count += 1
    except:
        # all exception should be owing to syntax errors
        utilities.output.error("There seems to be syntax errors in the input file. Please check the module structures.")
        sys.exit(1)

    if verbose:
        utilities.output.debug("%d modules detected in the input file..." % len(modules))
    return modules

def _parseDeflist(raw_list, mod_num):
    """
    Parse and return a raw sublist for Def list
    """
    msg = "Def list in Module %d" % mod_num
    _checkFirstIndex(raw_list, msg)
    f_num = int(raw_list[0])
    num = f_num*2 + 1
    def_list = raw_list[:num]
    _delRange(num, raw_list)
    return def_list

def _parseUselist(raw_list, mod_num):
    """
    Parse and return a raw sublist for Use list
    """
    msg = "Use list in Module %d" % mod_num
    _checkFirstIndex(raw_list, msg)
    f_num = int(raw_list[0])
    num = f_num + 1
    use_list = raw_list[:num]
    _delRange(num, raw_list)
    return use_list
    
def _parseCode(raw_list, mod_num):
    """
    Parse and return a raw sublist for Code
    """
    msg = "Code in Module %d" % mod_num
    _checkFirstIndex(raw_list, msg)
    f_num = int(raw_list[0])
    num = f_num*2 + 1
    code = raw_list[:num]
    _delRange(num, raw_list)
    return code

def _checkFirstIndex(l, msg):
    """
    Check whether the first element in the given list is an integer
    """
    first = 1
    try:
        first = int(l[0])
        return True
    except:
        utilities.output.error("Invalid starting index for %s. Must be an integer." % msg)
        sys.exit(1)
    
def _delRange(num, raw_list):
    """
    Delete the first "num" elements in the raw_list
    """
    for i in range(num):
        del raw_list[0]  # remove saved elements from the beginning of raw_list    
    return

class Config(object):
    def __init__(self, input_file, output_file, to_print, to_human, to_verbose):
        self.input_file = input_file
        self.output_file = output_file
        self.to_print = to_print
        self.human = to_human
        self.verbose = to_verbose
        
    def __str__(self):
        return "input_file: %s\noutput_file: %s\nto_print: %s\nhuman: %s\nverbose: %s\n" % (self.input_file, self.output_file, self.output_file, self.human, self.human)
    
def preprocess():
    """
    Pre-processing of file paths and configurations
        * input_file 
        * output_file
        * to_print
        * to_human
        * to_verbose 
    """
    input_file, output_file, to_print, to_human, to_verbose = getArgs()
    input_file, output_file = checkPaths(input_file, output_file, to_verbose)
    return Config(input_file, output_file, to_print, to_human, to_verbose)

def postprocess(format_output, warnings, output_file, verbose=False):
    """
    Post-processing of output
        * Print output
        * Dump output into specific output file
    """
    f = None
    try:
        if verbose:
            utilities.output.debug("Opening output file \"%s\" to write." %output_file)

        f = open(output_file, "w")
        f.write(format_output + '\n\n' + warnings)
        
    except:
        utilities.output.error("Cannot write output to file \"%s\"." %output_file)
        sys.exit(1)
        
    finally:
        f.close()
    
def main():
    """
    Main control of objects and actions
    """
    conf = preprocess()
    t = readInput(conf.input_file, conf.verbose)
    r_list = splitInput(t, conf.verbose)
    mods = parseList(r_list, conf.verbose)
    modules = Modules(mods, conf.verbose)
    modules.processModules()

    # assign to local variables
    format_output = modules.output()
    human_output = modules
    warnings = modules.outputWarnings()
    number = modules.number  # number of modules processed (linked)
    
    if conf.to_print or not conf.output_file: # if to_print is enabled or output_file is not given
        if conf.human:
            if conf.verbose:
                utilities.output.debug("Print human readable output...")
            print human_output
            if warnings:
                print warnings
        else:
            if conf.verbose:
                utilities.output.debug("Printing output...")
            print format_output
            if warnings:
                print warnings

    if conf.output_file:
        postprocess(format_output, warnings, conf.output_file, conf.verbose)
    
    if conf.verbose:
        utilities.output.debug("Linking process is complete. %d modules linked." % number)
       
if __name__ == '__main__':
    main()
    
    