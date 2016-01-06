r"""Python interactive completion using GNU readline 2.1.
    $Id: rlcompleter2.py,v 1.1 2003/01/29 17:20:35 hpk Exp $

    licensed under the Python Softare License 

    (c) 2003-2010 Holger Krekel, hpk at codespeak net 

   how the interactive completer works
   -------------------------------------

   The Completer works as a callback object for the readline 
   library. It doesn't just give you completions on much 
   more expressions than the stdlib-rlcompleter. It also 
   gives you incrementally more introspective information 
   the more often you hit <tab>.  

   The completer aims to be very intuitive and helpful.
   You can customize behaviour via the Config class 
   which is instantiated per Completer (to enable it 
   to be multiply embedded with e.g. IPython)

   Feel free to suggest better default behaviour or
   configuration options! 
"""

__version__='0.98'
__author__ ='holger krekel <hpk@trillke.net>'
__url__='http://codespeak.net/rlcompleter2/'

import os, sys, re, inspect, keyword
try:
    import __builtin__
except ImportError:
    import builtins as __builtin__

# debug turned off for releases
if 0:
    debugfile = open('/tmp/rlcompleter2.log','w')
    def debug(obj):
        debugfile.write(str(obj).strip()+'\n')
        debugfile.flush()
else:
    debug = lambda obj: None

class Config:
    """ run-time changeable configuration parameters and
        functions. An instance of this class can be modified
        and passed to the Completer constructor.
    """

    # number of characters for <type>-abbrevs. set 0 to omit type info.
    typesize = 3

    # num of lines of completions/documentation chunks
    # set to  0 for using terminalheight (see below),
    #        -1 for showing *all* lines in one go
    #        >0 for the number of lines to show with each chunk
    spliteach = 0

    # separator line when showing docstring + signatures
    separator_line = '-'*78

    # show source code for functions
    showfuncsource = 1

    # evaluation and completion of expressions happens in ...
    try:
        mainmodule = __import__('__main__')
    except ImportError:
        mainmodule = None

    def viewfilter(self, nameobj):
        """ return true if the given name, object combination
            should be included in the visible completion-list.
        """
        name, obj = nameobj
        if name.startswith('_'):
            return 0
        return 1

    def __init__(self, formatter=None):
        self.formatter = formatter or Formatter(self)

        try:
            import termios,fcntl,struct
            call = fcntl.ioctl(0,termios.TIOCGWINSZ,"\000"*8)
            height,width = struct.unpack( "hhhh", call ) [:2]
            self.terminalwidth = width
            self.terminalheight = height
        except:
            self.terminalwidth = 80
            self.terminalheight = 30


    string_help = r"""*regular expressions
\A start of string
\Z end of string
\b-\B empty str beg/end of word-INVERSE
\d-\D decimal digit-INVERSE
\s-\S whitespace[ \t\n\r\f\v]-INVERSE
\w-\W alphanumeric-INVERSE
\\ backslash
.  any character
^  start of string
$  end of string
*  zero or more reps
+  one or more reps
*?,+?,?? non-greedy versions
{m,n} m to n reps
{m,n}? non-greedy m to n reps
[] set of characters (^ inverses)
|  A|B matches A or B
(...) RE inside parens
(?iLmsux) set flag for RE
(?:...) non-grouping parens
(?P<name>...) named group
(?P = name) same as before named group
(?#...) comment(ignored)
(?=...) if ... next, nonconsuming
(?!...) if ... doesnt match next
""".strip().split('\n')

class Formatter:
    """ Lots of hooks for showing non-unqiue completions. 
        (unique completions are handled by the Completer itself).
    """
    import types
    
    def __init__(self, config):
        self.config = config
        # construct type abbreviation list
        self.abbdict={}
        if config.typesize:
            t=type
            tlist = filter(lambda x: type(x) is type, vars(self.types).values())
            for typ in tlist:
                self.abbdict[typ]=typ.__name__.split()[-1][:config.typesize].lower()
            debug("formatted types: %s" % self.abbdict)
        
    """ Formatting functions. 
    """
    def TypeView(self, name, obj):
        """ return a Type-specific view which is never used
            for unqiue (final) completion.
        """
        if not keyword.iskeyword(name) and self.config.typesize:
            if inspect.isclass(obj) and issubclass(obj, Exception):
                name='<exc>%s' % name
            elif type(obj) in self.abbdict:
                name='<%s>%s' % (self.abbdict[type(obj)], name)

            if callable(obj):
                name=name+format_callable_signature(obj)
        return name

    def TypeCompletion(self, name, obj):
        """ determines natural completion characters 
            for the given obj. For an appropriate 
            definition of 'natural' :-)
        """
        if callable(obj):
            if format_callable_signature(obj).endswith('()'):
                return "()"
            return "(" 
        if inspect.ismodule(obj):
            return '.'
        if keyword.iskeyword(name):
            return ' '
        return ''

    def rl_many(self, matches):
        """ return list of list of completion strings.
            [[string0a,string0b,...],[string1a,...]]
        """
        debug("rl_many:"+str(matches.keys()[:10])+'...')

        keywidth = 8+max(map(len, matches.keys()) or [0])
        subfin = [[],[]]
        for name,obj in matches.items():
            subfin[0].append(self.TypeView(name, obj))
            subfin[1].extend(self.doculines(name, obj, keywidth))
           
        lines = subfin.pop(1)
        subfin.extend(linesplit(lines,self.config))
        for i in range(1,len(subfin)):
            if subfin[i]:
                rl_fixlines(subfin[i], self.config.terminalwidth)
            else:
                del subfin[i]
        return subfin

    condense_rex = re.compile('\s*\n\s*',re.MULTILINE)

    def doculines(self, name, obj, keywidth):
        """ show documentation for one match trimmed to 
            a few lines (currently one).
        """
        if keyword.iskeyword(name):
            objdoc = '<python keyword>'
        else:
            objdoc = docstring(obj)
            if not objdoc:
                objdoc = ': %s, type: %s' % (obj,type(obj))
        objdoc = self.condense_rex.sub('. ',objdoc.strip())

        # cut out part of c-signature in doctring 
        try:
            inspect.getargspec(obj)
        except TypeError:
            i = objdoc.find('->')
            if i!=-1:
                objdoc = objdoc[i:]

        namedoc = self.TypeView(name,obj)
        namedoc = namedoc.ljust(keywidth)+' '

        line = namedoc + objdoc
        width = self.config.terminalwidth-4
        return [line[:width-1].ljust(width-1)]

    def fulldoc(self, obj):
        """ return list of list of documentation strings.
        """
        debug("fulldoc for %s" % repr(obj))
        lines = [self.config.separator_line]
        if callable(obj):
            header = get_callable_name(obj)
            sig  = format_callable_signature(obj, justnum=0) 
            if sig:
                lines.append(header + sig)
        else:
            lines.append(repr(obj) + ' ' + repr(type(obj)))
            lines.append(self.config.separator_line)

        doc = docstring(obj) or '*'
        lines.extend(doc.strip().split('\n'))
        if isfunc(obj) and self.config.showfuncsource:
            try:
                source = inspect.getsource(obj)
                lines.append(self.config.separator_line)
                lines.extend(source.split('\n'))
            except IOError: pass
        rl_fixlines(lines, self.config.terminalwidth-4)
        rl_fixorder(lines)
        l = linesplit(lines, self.config)
        return l

###########################################
# support functions                       #
###########################################

def isfunc(obj):
    if callable(obj):
        if hasattr(obj, 'func_code') or hasattr(obj, 'im_func'):
            return 1

def get_callable_name(obj):
    assert callable(obj)
    if inspect.isclass(obj):
        return obj.__name__
    try:    
        return obj.im_class.__name__ + '.' + obj.im_func.func_name
    except AttributeError:
        try:
            return obj.func_name
        except AttributeError:
            return ''

def format_callable_signature(obj, justnum=1):
    """return signature for any callable (including classes)"""
    assert callable(obj)
    if inspect.isclass(obj):
        obj = getattr(obj, '__init__', lambda: None)
    try: 
        func = obj.im_func
        delta=1
    except AttributeError:
        func = obj
        delta=0
    try:
        args, vargs, kargs, defs = inspect.getargspec(func)
        if not justnum:
            return inspect.formatargspec(args, vargs, kargs, defs)
            
        arglen = (args and len(args)-delta) or 0
        if defs:
            sig='(%d-%d' % (arglen-len(defs), arglen)
        elif arglen:
            sig='(%d' % arglen
        else:
            sig='('
        if vargs:
            sig+= sig[-1]!='(' and ',*' or '*'
        if kargs:
            sig+= sig[-1]!='(' and ',**' or '**'
        sig+=')'
        return sig

    except TypeError:
        if justnum: 
            return format_callable_c_signature(obj)
        return ''

funcrex = re.compile('\w+\(([^\[\)]*)(\[.*?\])?\).*(-|=>)?\s*(\S*)')
wordrex = re.compile('\w+')

def format_callable_c_signature(obj, long = 0):
    """ heuristically get a C-function's signature """
    assert callable(obj)
    doc = docstring(obj)
    if not doc:
        return '(?)' 
    else:
        # look for typical doc c-signature 
        m = funcrex.search(doc[:200])
        if not m:
            return '*(?)'
        else:
            args = m.group(1) or ''
            dargs = m.group(2) or ''
            args = len(wordrex.findall(args))
            dargs = len(wordrex.findall(dargs))
            if dargs:
                return '*(%d-%d)' % (args,args+dargs)
            if not args:
                return '*()'
            return '*(%d)' % args

def allbindings(obj):
    """ return dict with all attrname/obj bindings for a given obj.

        note that using the builtin vars() would not give the attributes 
        of base classes whereas calling 'dir()' gives the names 
        of inherited attributes. 
    """
    d = {}
    for name in dir(obj):
        try: d[name]=getattr(obj, name)
        except: pass
    return d

def globalscope(module):
    """return (interactive) global scope for a module."""
    scope = vars(__builtin__)
    scope.update(vars(module))
    for kw in keyword.kwlist:
        scope[kw] = 1
    return scope

def docstring(obj):
    """ return un-inherited doc-attribute of obj.

        (i.e. we detect inheritance from its type).
        XXX: this should eventually go into the inspect module!
    """
    if getattr(type(obj),'__doc__','')!=getattr(obj,'__doc__',''):
        return inspect.getdoc(obj)

def commonprefix(names, base = ''):
    """ return the common prefix of all 'names' starting with 'base'
    """
    def commonfunc(s1,s2):
        while not s2.startswith(s1): 
            s1=s1[:-1]
        return s1

    if base:
        names = filter(lambda x, base=base: x.startswith(base), names)
        if not names:
            return ''
    return reduce(commonfunc,names)

def linesplit(lines, config):
    """ return a list of sublists where each sublist
        is not longer than maxi lists.
    """
    maxi = config.spliteach
    if maxi == -1:
        return [lines]
    elif maxi == 0:
        maxi = config.terminalheight-3
    splitlist = []
    for i in range(1+(len(lines)/maxi)):
        if i!=0:
            stilltogo = len(lines)-i*maxi
            splitlist[i-1].append('~<tab> for remaining %d lines' % stilltogo)
        splitlist.append(lines[i*maxi:(i+1)*maxi])
    debug("returning splitlist, size = %s" % len(splitlist))
    #debug("first item in splitlist: %s" % splitlist[0])
    return splitlist

###########################################
# Fixing some bad readline behaviour      #
###########################################

def rl_fixorder(strings):
    """ fix implicit sorting of readline.
   
        if the strings are not accidentally sorted 
        then fix the current 'strings' order.
    """
    num = len(strings)
    for s1,s2 in zip(strings, strings[1:]):
        if s1 >= s2:
            digits = num<=10 and '%d ' or '%02d '
            for i in range(num):
                strings[i]=digits % i + strings[i]
            break

def rl_fixprefix(strings):
    """ avoid completion on a common prefix.
    """
    if len(strings)==0:
        strings[:] = list('*?')
    else:
        if commonprefix(strings):
            strings.append('*') # destroys common prefix

def rl_fixlines(strings, width):
    """ avoids multicolumns so that effectively each
        string in strings will be shown on its own line.
    """
    l = reduce(max,map(len, strings or []))
    if l<width/2:
        strings[0]=strings[0][:width-2].ljust(width-1)

###########################################
# classes for meta control flow 
#     they are usually raised and catched
#     to avoid ugly recursive "returns"
###########################################

class Finish:
    """ Finish Event 
        gets thrown from different completion-methods. 
    """
    def __init__(self, completions):
        for list in completions:
            rl_fixprefix(list)
        self.completions = completions

class UniqueFinish(Finish):
    """ UniqueFinish event
        gets thrown from different completion-methods. 
    """
    def __init__(self, completions):
        self.completions = completions

class Error(Finish):
    """ Error Event, thrown if there was an not to be 
        ignored error in the command line. 
    """
    def __init__(self, obj):
        Finish.__init__(self, [['*error',str(obj)]])

#####################################################################
# classes performing introspection into the parser to eventually 
# obtain a code object                       
#####################################################################

class TryParser:
    """ Repeatedly parse substrings to find 
        an AST-Expression where we can deliver
        a Code object on the interesting part.
    """
    __magicmarker__ = '__NO_MORE_WARS__'
    wordmatch = re.compile('([\w_]*).*')
    import compiler,parser

    def _raise_codegenerator(self, node):
        """ recurse into AST-node to raise a codegenerator
            for the * in the substructure 'ast.Getattr(*,MAGICATTR)'
        """
        if getattr(node,'attrname',None)==self.__magicmarker__:
            node = self.compiler.ast.Expression(node.expr)
            node.filename = "<subtree %s>" % repr(node)
            raise self.compiler.pycodegen.InteractiveCodeGenerator(node)
        filter(self._raise_codegenerator,node.getChildNodes())

    def find_code(self, text):
        """ return code object for last valid expression OR if 
            not determinable, then return a 'parsability' flag.
            this flag indicates if we were able to parse
            a subexpression at all.
        """
        debug("trying to get code for %s" % repr(text))
        parseable = not text 
        while text:
            try:
                if text[-1]=='.':
                    parsable = self.parser.expr(text[:-1])
                    expr = text+self.__magicmarker__
                else:
                    parsable = self.parser.expr(text)
                    expr = text+' .'+self.__magicmarker__
                tree = self.compiler.pycodegen.parse(expr, 'eval') # ) # , 'eval')
                debug("parsing succeeded: "+ repr(expr))
                self._raise_codegenerator(tree)
                raise AssertionError('for %s unexpected AST: %s' %(repr(expr), tree))

            except (SyntaxError, self.parser.ParserError):
                m = self.wordmatch.match(text)
                text = text[m and m.span(1)[1] or 1:]
            except self.compiler.pycodegen.InteractiveCodeGenerator:
                ic = sys.exc_info()[1]
                return ic.getCode()
            except:
                import traceback
                traceback.print_exc()
                print ("internal failure on %s" % expr)
                print ("send mail to hpk at codespeak net")
            #    m = self.wordmatch.match(text)
            #    text = text[m and m.span(1)[1] or 1:]
        return parseable

# simple singleton
TryParser = TryParser()

class EvalItem:
    """ Evaluating a line
    """
    def __init__(self, config, text = '', attr = None):
        """ evaluate last possible expression part in text.

            attr can be a string or a filter-function
            which accepts/rejects (name,obj)-bindings.
        """
        self.config = config
        debug("got text %s, attr %s" % (repr(text),repr(attr)))
        self.text = text

        if attr and type(attr) is str:
            self.attrname = attr
            self.func = lambda x: x[0].startswith(attr)
        else:
            self.attrname = ''
            self.func = attr or config.viewfilter

        # try finding code and evaluting it...
        self.code = TryParser.find_code(text)
        if inspect.iscode(self.code):
            try: 
                self.obj = eval(self.code, vars(config.mainmodule))
            except: 
                raise Error(sys.exc_info()[1])
        else:
            self.text = ''

    def has_undotted_object(self):
        """ see if evaluated an object does not end in '.'"""
        if hasattr(self, 'obj') and self.text[-1]!='.':
            return 1
    
    def completions(self):
        """ return name-object bindings matching self.attr/name.
        """
        debug("completions called")
        if hasattr(self,'obj') and self.text[-1]=='.': 
            scope = allbindings(self.obj)
            prefix = commonprefix(scope.keys(), self.attrname)
            if prefix and prefix!=self.attrname:
                return {prefix:''}  # unique-complete prefix 
            #else:
            #    return scope
        elif self.attrname:
            scope = globalscope(self.config.mainmodule)
        else:
            scope = vars(self.config.mainmodule)
        debug("scopes: %s" % scope.keys()[:10])
        debug("func: %s" % repr(self.func))
        d = {}
        for k,v in filter(self.func, scope.items()):
            d[k]=v
        return d

    def __str__(self):
        return '%s hasobj %d' %(repr(self), hasattr(self, 'obj'))

class LineEval:
    """ Encapusulates Recognition of line parts and 
        parsing/evaluation of the relevant last part 
        where completions are requested on.
    """
    breakchars = ',;{[%+-*/=:`'
    splitrex = re.compile(r'\A(?P<base>.*?\.?\s*)?(?P<attrname>[_a-zA-Z][\w_]*)?\Z')

    def __init__(self, text, config):
        self.text = text
        self.config = config
        for k,v in self.splitrex.match(text).groupdict('').items():
            setattr(self,k,v)
            debug("    %s = %s" % (k,v))

        lastchar = self.base[-1:]
        debug('lastchar: %s' % lastchar)
        if lastchar == '(':
            evalitems = [
                         EvalItem(config, self.base[:-1]),
                         EvalItem(config, '', self.attrname),
                        ]

        elif not lastchar or lastchar in self.breakchars:
            evalitems = [EvalItem(config, '', self.attrname)]
        elif lastchar == '.':
            evalitems = [
                         EvalItem(config, self.base, self.attrname),
                         EvalItem(config, self.base[:-1]),
                        ]
            #if inspect.ismodule(getattr(evalitems[0], 'obj')):
            #    evalitems.reverse()
        else:
            evalitems = [EvalItem(config, self.base, self.attrname)]

        #if len(evalitems[0].completions())==1:
        #    self.evalitems = [evalitems.pop(0)]
        #else:
        self.evalitems = evalitems

    def __str__(self):
        """ for debuggging purposes"""
        return 'matches: %s' % map(str, self.evalitems)

class Completer:
    """ Class providing completions for readline's requests
    """
    def __init__(self, config = None):
        """ Return a completer object whose 'rl_complete' method
            is suitable for use by the readline library via 
            readline.set_completer(<instance>.rl_complete).
        """
        self.config = config or Config()

    def rl_complete(self, text, state):
        """handle readline's complete requests
           readline calls consecutively with state == 0, 1, 2, ... 
           until we return None.
        """
        if state == 0:
            try:
                self.construct(text)
            except:
                import traceback
                traceback.print_exc()
                self.rl_matches=['!!', 'INTERNAL ERROR']

            if len(self.rl_matches)==1:
                match = self.rl_matches[0]
                if match and not match.startswith(text):
                    debug ("ERROR: catching wrong completion %s" % repr(match))
                    self.rl_matches.append('<INTERNAL ERROR')
                elif match == text:
                    return None
                else:
                    debug("dispatching unique completion: %s" % repr(match))
        if state<len(self.rl_matches):
            #debug("returning match: %s" % repr(self.rl_matches[state]))
            return self.rl_matches[state]
        return None

    def construct(self, text):
        """ constructs completions for the given text. 

            this method is called once per-completion request
            from readline. Based on the input text and the 
            config-object it computes the list of completions 
            'self.rl_strings' which 'rl_complete' dipatches one 
            by one to readline. 
        """
        # count repitions, starting from -1 
        # (because first <tab> is usually swallowed by readline) 
        if text == getattr(self, 'text_last', None):
            debug("self.repeat = %d"%self.repeated)
            self.repeated+=1
        else:
            self.repeated = 0 # -1
            self.text_last = text
            self.completions = [[]]
            #print "constructing completions, repeat=%d" % self.repeated

            try:
                self.method_tokenize(text)
                self.method_eval(text)
                raise Error('nothing found, empty namespace?')
            except Finish:
                fin = sys.exc_info()[1]
                self.completions = fin.completions
                if fin.__class__ == Error:
                    self.text_last = None

        #debug("completions[:10]: %s" % str(self.completions[:10]))
        mod = self.repeated % len(self.completions)
        self.rl_matches = self.completions[mod]
        #debug("finish: %s" % str(self.rl_matches))

    def method_tokenize(self, text):
        """ return true if tokenization information 
            lets us shortcut completions such
            as returning error/string-information.

            this method basically checks if we are inside
            a raw/string definition.

            XXX: Could we incorporate trying filename-completions
                 here?
        """
        import token, tokenize

        class TokenEater:
            """ Token Receiver function (as class-instance) 
            """
            def __init__(self,text,config):
                self.text = text
                self.config = config

            def __call__(self, ttype, ttoken, srowscol, erowecol, line):
                srow, scol = srowscol
                erow, ecol = erowecol 
                #debug("got token: %s" % repr(ttoken))
                self.context = '%s' % (line[max(0,scol-1):scol+4])
                if ttype == token.ERRORTOKEN:
                    #debug("found error token: %s" % repr(ttoken))
                    if ttoken.strip():
                        if ttoken in '"\'':
                            self.handle_open_string(line[:scol].rstrip()[-1:])
                        else:
                            raise Error('error at %s' % self.context)

            def handle_open_string(self, previous):
                """ raise help completion for open strings """
                #debug("previousstrip: "+repr(previous))
                if previous == 'r':
                    fin = [['in rawstring, <tab> for regexinfo'],
                           self.config.string_help[:]]
                elif previous == 'u':
                    fin = [['<open unicode string>']]
                else:
                    fin = [['<open string>']]
                raise Finish(fin)

        try:
            eater = TokenEater(text, self.config)
            tokenize.tokenize(['',text].pop, eater)

        except tokenize.TokenError:
            ex = sys.exc_info()[1]
            debug("ex:%s" % ex)
            msg = ex.args[0]
            if msg[:3]=='EOF'and msg[-6:]=='string':
                eater.handle_open_string(text[ex.args[1][1]])

    def method_eval(self, text):
        """ Partially parse and evaluate a single cmdline-text."""
        debug("method eval %s"% repr(text))

        line = LineEval(text, self.config)
        debug(line)

        fin = []
        for evalitem in line.evalitems:
            if evalitem.has_undotted_object():
                fin.extend(self.config.formatter.fulldoc(evalitem.obj))
                continue

            matches = evalitem.completions()
            attrname = evalitem.attrname
            #debug("matches: %s " % matches.keys())

            if len(matches)==0:
                if attrname:
                    raise Error('no match found for name: %s' % repr(attrname))
                else:
                    continue
                    raise Error('sorry. dunno, quite empty here, eh ...')
            elif len(matches)==1:
                name, obj = matches.popitem()
                if fin:
                    fin.extend(self.config.formatter.fulldoc(obj))
                else:
                    debug("exact match, name %s, attrname %s" % (name,attrname))
                    if attrname == name:
                        debug("getting typecompletion for %s"% repr(obj))
                        x = self.config.formatter.TypeCompletion(name,obj)
                        if x:
                            fin.append([text+x])
                            raise UniqueFinish(fin)
                        else:
                            fin.extend(self.config.formatter.fulldoc(obj))
                    else:
                        fin.append([text+name[len(attrname):]])
                        raise UniqueFinish(fin)
                break
            else:
                fin.extend(self.config.formatter.rl_many(matches))
        if fin:
            raise Finish(fin)

def setup_readline_history(histfn):
    import readline 
    try:
        readline.read_history_file(histfn)
    except IOError:
        # guess it doesn't exist 
        pass

    def save():
        try:
            readline.write_history_file(histfn)
        except IOError:
            print ("bad luck, couldn't save readline history to %s" % histfn)
       
    import atexit
    atexit.register(save)

def setup(histfn=None, button='tab',verbose=1):
    if histfn is None: 
        base = os.getenv('HOME')
        if not base: 
            import tempfile
            base = tempfile.gettempdir()
        histfn = os.path.join(base, '.pythonhist')
    import readline 
    completer = Completer()
    readline.set_completer_delims('')
    readline.set_completer(completer.rl_complete)
    readline.parse_and_bind(button+': complete')
    if histfn:
        setup_readline_history(histfn)
    if verbose:
        print ("Welcome to rlcompleter2 %s" % __version__)
        print ("for nice experiences hit <%s> multiple times"%(button))

if __name__ == '__main__':
    setup()
