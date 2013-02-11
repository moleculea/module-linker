# -*- coding: utf-8  -*-
import sys
import collections
import utilities

# constants
MACHINE_MEMOERY_SIZE = 600

class RawModule(object):
    """
    RawModule: a single module which contains the raw-parsed Def list, Use list and Code
    """
    def __init__(self, number):
        """
        Initializing RawModule
        
        @param number : the number representing the appearing location of a module, starting from 1

        """
        self.__number = number
        self.__def_list = []  # Raw Def list; initial type being List
        self.__use_list = []  # Raw Use list; initial type being List
        self.__code = []      # Raw Code; initial type being List
    
    @property
    def number(self):
        return self.__number
    
    """
    Properties getters and setters from raw_list
    """

    @property
    def def_list(self):
        return self.__def_list
    
    @def_list.setter
    def def_list(self, value):
        self.__def_list = value

    @property
    def use_list(self):
        return self.__use_list
    
    @use_list.setter
    def use_list(self, value):
        self.__use_list = value
        
    @property
    def code(self):
        return self.__code
    
    @code.setter
    def code(self, value):
        self.__code = value

    def __str__(self):
        return "Module %d\n%s\n%s\n%s\n" % (self.number, " ".join(self.def_list), " ".join(self.use_list), " ".join(self.code))
 
 
class Module(RawModule):
    """
    Module: a single module for parsing and calculating base address
        * All values and addresses are stored as strings and
          converted to integer while in calculation
    """
    def __init__(self, number, base):
        super(Module, self).__init__(number)
        self.__base_address = base
        self.__next_address = 0 
    
    @property
    def base_address(self):
        return self.__base_address
    
    @base_address.setter
    def base_address(self, value):
        """
        For manually setting base address
        """
        if not isinstance(value, int):
            raise TypeError("Base address for module must be an integer")
        self.__base_address = value
    
    @property
    def next_address(self):
        return self._getNextAddress()
    
    @property
    def size(self):
        return int(self.code[0])
        
    def getDefVars(self):
        """
        Return an ordered dictionary mapping variables to values in the Def list
        """
        return utilities.list2dict(self.def_list[1:])
        
    def getUseVars(self):
        """
        Return a list of variables in the Use list
        """
        return self.use_list[1:]
    
    def getCodeMap(self):
        """
        Return a list of tuples mapping codes to addresses in Code
        """
        return utilities.list2tuplelist(self.code[1:])

    def _getNextAddress(self):
        """
        Get the next base address from Code section
        """
        return int(self.code[0]) + self.base_address
    
    def __str__(self):
        return "Module %d\nBase Address: %d\n%s\n%s\n%s\n" % (self.number, self.base_address,  " ".join(self.def_list), " ".join(self.use_list), " ".join(self.code))

    
class LinkedModule(object):
    """
    LinkedModule: a to-be-linked (processed) module object instantiated in Modules class
    """
    def __init__(self, number, base, def_vars=collections.OrderedDict(), use_vars=[], code_map=[], use_vals=collections.OrderedDict()):
        self.__number = number      # integer
        self.__base_address = base  # integer
        self.__defVars = def_vars
        self.__useVars = use_vars
        self.__codeMap = code_map
        self.__useVals = use_vals   # dictionary mapping variables to values (from symbol table) in Use list
                                    # elements in the same order to those of use_vars
        self.__rlcFlag = False
        self.__rsvFlag = False

    @property
    def number(self):
        return self.__number
    
    @property
    def base_address(self):
        return self.__base_address
    
    @property
    def def_vars(self):
        return self.__defVars
    
    @property
    def use_vars(self):
        return self.__useVars
    
    @property
    def code_map(self):
        return self.__codeMap
    
    @property
    def use_vals(self):
        return self.__useVals
    
    @property
    def def_vars_num(self):
        return len(self.def_vars)
    
    @property
    def use_vars_num(self):
        return len(self.use_vars)
    
    @property
    def code_map_num(self):
        return len(self.code_map)
    
    def process(self):
        """
        Process this module 
            * Relocate
            * Resolve
        """
        self.__relocate()
        self.__resolve()
        
    def __relocate(self):
        """
        Relocating Relative Addresses in this module
        """
        code_map = self.code_map
        rlc_map = []               # relocated code_map
        for t in code_map:
            if t[0] == "R":
                abs_addr = int(t[1]) + self.base_address
                addr = str(abs_addr)
                if int(addr[1:]) >= MACHINE_MEMOERY_SIZE:
                    LinkerErrors.absAddExceedRlc(addr, t[1], self.number) # call absAddExceedRlc with relocated address and original address of R
                    sys.exit(1)
                rlc_map.append((t[0], addr))
            else:
                rlc_map.append((t[0], t[1]))
                    
        self.__codeMap = rlc_map   # update code map
        self.__rlcFlag = True      # update relocation flag
    
    def __resolve(self):
        """
        Resolving Absolute Address (modifying External Address) in this module
        """
        code_map = self.code_map
        rsv_map = []
        use_vals = self.use_vals.items()
        
        for t in code_map:
            if t[0] == "E":
                ind = int(t[1][1:])             # index represented in the rightmost 3-digit of External Address
                value = use_vals[ind][1]        # value used to override the rightmost 3-digit of External Address
                addr = t[1][0] + value.zfill(3) # override External Address, e.g. "3" + "007" --> "3007"
                rsv_map.append((t[0], addr))
            else:
                rsv_map.append((t[0], t[1]))
                
        self.__codeMap = rsv_map   # update code map
        self.__rsvFlag = True      # update resolving flag
        
        
    def __str__(self):
        return "Module %d\nBase Address: %d\n%d %s\n%d %s\n%d %s\n" % (self.number, self.base_address, self.def_vars_num, " ".join(utilities.tuplelist2list(self.def_vars.items())), self.use_vars_num, " ".join(self.use_vars), self.code_map_num, " ".join(utilities.tuplelist2list(self.code_map)))

class Modules(object):
    """
    Modules: a collection of Module objects
        * Generating Symbol Table
        * Relocating Relative Addresses
        * Resolving Absolute Addresses
        * Generating final output
        * Handling exceptions
    """
    def __init__(self, modules, verbose):
        """
        Initializing with "modules", which is a list of Module objects 
        with correct base addresses, thus its elements order is relevant
        
        @param modules: a list of module objects
        """
        self.__modules = modules    # raw modules
        self.__linked_modules = []  # list of modules that are processed (after relocation and resolving)
        self.__symbol_table = collections.OrderedDict()
        self.__number = 0
        # configurations (boolean)
        self.verbose = verbose

        # actions upon initialization
        self._syntaxCheck()  # preliminary syntax check upon initialization
        
        self.__linker_errors = LinkerErrors(modules)  # initialize linker errors
        self.__linker_warnings = None  # initialize linker warnings in self.__catch_warnings()
        self._catch()  # catch errors and warnings
        self._generateSymbolTable() # generate symbol table
        
    def _syntaxCheck(self):
        """
        Preliminary syntax checking for validity of values and addresses, 
        i.e. whether addresses are 4-digit words and whether values
        are within the very module size 
            Called in self.__init__()
        """
        if self.verbose:
            utilities.output.debug("Checking module syntax and validity of values and addresses...")
            
        for mod in self.__modules:
            # checking values
            values = mod.getDefVars().items()
            num = mod.number
            for v in values:
                # v[0]: variable name
                # v[1]: value
                try:
                    #if int(v[1]) > mod.size:
                        #print  "Invalid value for variable %s: %d in Def list of Module %d. Must be within its module size." %(v[0], v[1], num)
                        #sys.exit(1)
                    int(v[1])
                        
                except ValueError:
                    print "Invalid value for variable %s: %d in Def list of Module %d. Must be an integer." %(v[0], v[1], num)
                    sys.exit(1)
                    
            # checking addresses
            addrs = mod.getCodeMap()
            for a in addrs:
                # a[0]: code (I/A/R/E)
                # a[1]: address
                try:
                    int(a[1])
                    if len(a[1]) != 4:
                        print "Invalid address for %s: %d in Code of Module %d. Must be a 4-digit word." %(a[0], a[1], num)
                        sys.exit(1)
                        
                except ValueError:
                    print "Invalid address for %s: %d in Code of Module %d. Must be an integer." %(a[0], a[1], num)
                    sys.exit(1)
    
    
    def _catch(self):
        """
        Catching errors and warnings
        """
        if self.verbose:
            utilities.output.debug("Checking errors and warnings...")
        self.__catchErrors()
        self.__catchWarnings()
        
        if self.verbose:
            utilities.output.debug("No static errors caught, continue...")
    
    def __catchErrors(self):
        self.__linker_errors.process()

    def __catchWarnings(self):
        dvl = self.__linker_errors.def_var_list
        uvl = self.__linker_errors.use_var_list
        self.__linker_warnings = LinkerWarnings(self.__modules, dvl, uvl)  # initialize LinkerWarnings with modules, def_var_list and use_var_list
        self.__linker_warnings.process()
         
    @property
    def symbol_table(self):
        """
        Return a dictionary mapping variables to their calculated values
        """
        return self.__symbol_table
    
    def _generateSymbolTable(self):
        """
        Generate Symbol Table and save in self.__symbol_table
            Called in self.__init__()
        """
        if self.verbose:
            utilities.output.debug("Generating Symbol Table...")
        for mod in self.__modules:
            def_vars = mod.getDefVars()
            base = mod.base_address
            if def_vars:
                for v in def_vars.items():
                    self.__symbol_table.update([(v[0], str(int(v[1]) + base))])
    
    def formatSymbolTable(self):
        """
        Return formatted Symbol Table with "=" for each variable
        """
        pst = []

        for t in self.symbol_table.items():
            pst.append(t[0] + "=" + t[1])
        return "\n".join(pst)
        
    def processModules(self):
        """
        Main process
            * Relocate RAs in all modules
            * Resolve EAs all modules
        """
        if self.verbose:
            utilities.output.debug("Starting to process modules (relocating and resolving)...")
        for mod in self.__modules:
            def_vars = mod.getDefVars()
            use_vars = mod.getUseVars()
            code_map = mod.getCodeMap()
            use_vals = collections.OrderedDict()

            for var in use_vars:
                use_vals.update([(var, self.symbol_table[var])])
            lmod = LinkedModule(mod.number, mod.base_address, def_vars, use_vars, code_map, use_vals)
            lmod.process()
            self.__linked_modules.append(lmod)
            
        self.__number = len(self.__linked_modules)  # update number of modules linked
    
    @property
    def number(self):
        """
        Return number of modules linked after linking process
        """
        return self.__number
    
    def getModule(self, number):
        """
        Return a module specified by number
        """
        return self.__module[number]
    
    def formatLinkedModules(self):
        r = []
        for m in self.__linked_modules:
            r.append(str(m))
            
        return "\n".join(r)
    
    def output(self):
        """
        Return formatted output of processed modules (to be dumped in a text file)
        """
        ind = 0  # starting index
        next = 0 # base index for next module in the following loop
        add_index = [] # list of tuples of indexes and addresses, e.g. [(0, 7002), (1, 1004), (2, 4033), ...]
        
        for m in self.__linked_modules:
            nums = [next + i for i in range(m.code_map_num)]
            addrs = [t[1] for t in m.code_map]  # retrieve address in every tuple in code_map
            next += m.code_map_num
            add_index += zip(nums, addrs)
            
        vars = [t[0] for t in self.symbol_table.items()]  # retrieve variable in symbol table
        var_max_len = len(max(vars, key=len))  # length of longest string
        tj = []  # temporary list to be joined

        for t in add_index:
            fmt = "{:<%s}" % var_max_len  # left-align format width
            tj.append(fmt.format(str(t[0]) + ':') + ' ' + t[1])

        return self.formatSymbolTable() + "\n\n" + "\n".join(tj) + "\n"
    
    def outputWarnings(self):
        return self.__linker_warnings.output()
    
    def outputHuman(self):
        """
        Return human readable output of processed modules
        """
        return "Symbol Table\n" + self.formatSymbolTable() + "\n" + self.formatLinkedModules()         
      
    def __str__(self):
        return self.outputHuman()

  
        
class LinkerErrors(object):
    """
    LinkerErrors
    """
    
    def __init__(self, modules):
        """
        Initialize with modules list
        """
        self.__modules = modules
        self.__def_vars_list = []
        self.__use_vars_list = []
        
    def process(self):
        """
        Main process function
        """
        self._multiDef()
        self._useVarUndef()
        self._defVarExceed()
        self._extAddExceed()
        self._absAddExceed()
        self._relAddExceed()
        self._netModExceed()
        
    def __locateError(self, module, kind_number):

        number = module.number  # module number
        # 1 => Def list
        # 2 => Use list
        # 3 => Code
        kind = [None, "Def list", "Use list", "Code"]
        return " (Module %d: %s)" % (number, kind[kind_number])

    def _multiDef(self):
        """
        If a symbol is multiply defined, print an error message specifying the variable and exit.
        """
        # check multidef => check duplicate appearances of variables in Def lists
        all_def_vars = []
        for mod in self.__modules:
            def_vars = mod.getDefVars()
            if def_vars:
                vars = list(zip(*def_vars.items())[0])  # unzip def_vars items to retrieve only variables
                all_def_vars += vars
        
        dp = utilities.getduplicate(all_def_vars)  # find all duplicate variables
        if dp:
            for d in dp:
                utilities.output.error("%s multiply defined" % d)
                sys.exit(1)
        else:
            self.__def_vars_list = all_def_vars
            return
        
    
    def _useVarUndef(self):
        """
        If a symbol is used but not defined, print an error message specifying the value and exit.
        """
        
        all_use_vars = []
        for mod in self.__modules:
            use_vars = mod.getUseVars()
            all_use_vars += use_vars
        
        all_use_vars = list(set(all_use_vars))  # remove duplicate elements
        
        for v in all_use_vars:
            if v not in self.__def_vars_list:
                utilities.output.error("%s used but not defined" % v)
                sys.exit(1)
                
        self.__use_vars_list = all_use_vars
        return
            
    def _defVarExceed(self):
        """
        If an address appearing in a definition exceeds the size of the module, 
        print an error message specifying the given address and the module size and exit.
        """
        
        for mod in self.__modules:
            def_vars = mod.getDefVars()
            size = mod.size
            for t in def_vars.items():
                if int(t[1]) >= size:
                    utilities.output.error("address %s exceeds the module size of %d" % (t[1], size) + self.__locateError(mod, 1))
                    sys.exit(1)
        return 
                    
        
    def _extAddExceed(self):
        """
        If an external address is too large to reference an entry in the use list, 
        print an error message specifying the variable and exit.
        """
        
        for mod in self.__modules:
            use_vars = mod.getUseVars()
            use_vars_num = len(use_vars)
            code_map = mod.getCodeMap()
            for t in code_map:
                if t[0] == "E":
                    ind = int(t[1][1:])  # index represented in the rightmost 3-digit of External Address
                    if use_vars_num:
                        if ind >= use_vars_num:
                            utilities.output.error("external address %s is too large to reference an entry in the use list" % t[1] + self.__locateError(mod, 3))
                            sys.exit(1)
                    else:
                        utilities.output.error("external address %s is unable to reference any entry because the use list is empty" % t[1] + self.__locateError(mod, 3))
                        sys.exit(1)
                        
        return
    
    def _absAddExceed(self):
        """
        If an absolute address exceeds the size of the machine, 
        print an error message specifying that address and exit.
            Check before relocation
        """
        for mod in self.__modules:
            code_map = mod.getCodeMap()
            for t in code_map:
                if t[0] == "A":
                    ind = int(t[1][1:])  # index represented in the rightmost 3-digit of Absolute Address
                    if ind >= MACHINE_MEMOERY_SIZE:
                        utilities.output.error("absolute address %s exceeds the size of the machine" % t[1] + self.__locateError(mod, 3))
                        sys.exit(1)
        return
    
    @staticmethod
    def absAddExceedRlc(abs_addr, ori_addr, number):
        """
            Called if relocated R address is larger than machine memory size
        """
        return utilities.output.error("relocated absolute address %s (original R address: %s) exceeds the size of machine" % (abs_addr, ori_addr) + " (Module %d: Code)" % number)
        
    def _relAddExceed(self):
        """
        If a relative address exceeds the size of the module,
        print an error specifying that address and exit.
        """
        for mod in self.__modules:
            code_map = mod.getCodeMap()
            size = mod.size
            for t in code_map:
                if t[0] == "R":
                    ind = int(t[1][1:])  # index represented in the rightmost 3-digit of Absolute Address
                    if ind >= size:
                        utilities.output.error("relative address %s exceeds the size of the module" % t[1] + self.__locateError(mod, 3))
                        sys.exit(1)
        return
    
    def _netModExceed(self):
        """
        If the sum of all modules size exceeds the machine size,
        print an error
        """
        sum_size = 0
        for mod in self.__modules:
            sum_size += mod.size
        if sum_size > MACHINE_MEMOERY_SIZE:
            utilities.output.error("The summed size of all modules, which is %d, exceeds the size of machine" % sum_size)
            sys.exit(1)
            
    @property
    def def_var_list(self):
        return self.__def_vars_list
    
    @property
    def use_var_list(self):
        return self.__use_vars_list
       
    
class LinkerWarnings(object):
    """
    LinkerWarnings
    """
    def __init__(self, modules, def_vars_list, use_vars_list):
        """
        Initialize with modules list, and def_vars_list and use_vars_list from LinkerError object
        """
        self.__modules = modules
        self.__def_warnings = None
        self.__use_warnings = None
        self.__def_vars = def_vars_list
        self.__use_vars = use_vars_list
    
    def process(self):
        """
        Main process function
        """
        self._defVarUnuse()
        self._useVarUnuse()
        
    def _defVarUnuse(self):
        """
        If a symbol is defined but not used, print a warning message specifying the value and continue.
        """
        def_vars_list = self.__def_vars  # list of defined variables
        use_vars_list = self.__use_vars  # list of used variables
        def_warnings = [] # list of tuples (variable, module_number)
        
        if set(def_vars_list) != set(use_vars_list):
            for mod in self.__modules:
                def_vars = mod.getDefVars().items()
                number = mod.number
                for v in def_vars:
                    if v[0] not in use_vars_list:
                        def_warnings.append((v[0], number))
                        utilities.output.warning("%s was defined in Module %d but was never used" % (v[0], number))
        
            self.__def_warnings = def_warnings
            
        else:
            return

    def _useVarUnuse(self):
        """
        If a symbol appears in a use list but it not actually used in the module 
        (i.e., not referred to in an E-type address), 
        print a warning message and continue.
        """
        use_warnings = []  # list of tuples (variable, module_number)
        for mod in self.__modules:
            use_vars = mod.getUseVars()
            code_map = mod.getCodeMap()
            number = mod.number
            all_ind = range(len(use_vars)) # list of entry indexes to be referred to in E address 
            used_ind = []
            for t in code_map:
                if t[0] == "E":
                    ind = int(t[1][1:])  # index represented in the rightmost 3-digit of External Address
                    used_ind.append(ind)  # collect used indexes
            unused_ind = list(set(all_ind) - set(used_ind))
            unused_vars = [use_vars[ind] for ind in unused_ind]  # list of unused variables in the current module
            if unused_vars:
                use_warnings.append((unused_vars, number))
                for v in unused_vars:
                    utilities.output.warning("%s appeared in the use list in Module %d but not used" % (v, number))
        
        self.__use_warnings = use_warnings
        
    def output(self):
        """
        Return formatted output of all warnings caught
        """
        output_str = ""
        if self.__def_warnings:
            def_vars_str = ""
            for t in self.__def_warnings:
                def_vars_str += "Warning: %s was defined in Module %d but was never used.\n" % (t[0], t[1])
            output_str += def_vars_str
        if self.__use_warnings:
            use_vars_str = ""
            for t in self.__use_warnings:
                for tt in t[0]:
                    use_vars_str += "Warning: %s appeared in the use list in Module %d but not used.\n" % (tt, t[1])
            output_str += use_vars_str
        return output_str
            
    
if __name__ == '__main__':
    utilities.output.warning("Please run main.py script from project's directory.")