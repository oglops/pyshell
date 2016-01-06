=============================================================
rlcompleter2 0.97, interactive python command line completion 
=============================================================

Impatient?  download: `rlcompleter2-0.97.tar.gz`_,  ``(c) 2003-2005 Holger Krekel, hpk@trillke.net, license: MIT-License``

.. _`rlcompleter2-0.97.tar.gz`: http://codespeak.net/download/rlcompleter2/rlcompleter2-0.97.tar.gz 

Python command line completion - Holger Krekel 
============================================== 

One of the best features of Python_ is that you can use and
learn it interactively.  *rlcompleter2* enhances this
interactive experience.  It is a major improvement over the
'rlcompleter' in the standard library.

I recommend that you simply install it and see if you 
like it.  The user interface is simple: hit ``<tab>`` one
or more times.  If you sometimes use python interactively you 
will certainly enjoy it.  If you don't work interactively, 
well, then you should :-)

Please feel free to submit/look at current `issues (bugs,
features, wishes)`_.  You may also send private mail to "hpk
at trillke net" though that might get lost more easily. 

.. _Python: http://www.python.org 
.. _`issues (bugs, features, wishes)`: http://codespeak.net/issues/rlcompleter2/

Features
-------- 

- completion on any valid Python statement/expression

- many convenient completions, for example: 

  func(<tab>   presents function signatures and docs
  module.<tab> presents module docstring
  func<tab>    completes '(' or '()' 
  obj<tab>     completes '.' if obj is module or instance
  r'<tab>      (in raw string) shows regular expression help 

- when you hit <tab> multiple times you will get 
  increasingly more details about multiple completions

- the completer tries to autodetect your terminal height
  and width.

- shows type information for multiple matches. types
  are abbreviated by three characters.
  
- customaizable via the config class which you can inherit
  Look at the source at the bottom to get a clue.

Notes and the future
====================

how the interactive completer works
----------------------------------- 

rlcompleter2 works as a callback object for the readline 
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

We can't escape the Heisenberg problem
--------------------------------------

Anytime you hit <TAB> you may *change* objects
in your environment. This is because the completer 
not only parses the input but also partially compiles 
and evaluates it.  Python is dynamically typed so
we can't infer type/class information with only
parsing.  But evaluation of code can have 
side effects, if it involves e.g. a ``file.read()`` method.  
In interactive command line practice this is seldomly a 
big problem, though. 

Future and More Information 
--------------------------- 

For most up to date information please look at 
http://codespeak.net/rlcompleter2/

It is likely that rlcompleter2's functionality 
will be subsumed into  `the py lib`_ which aims
to offer a set of useful development utilities, 
among them `py.test`_, a unique python testing 
facility. 

.. _`py.test`: http://codespeak.net/py/current/doc/test.html 
.. _`the py lib`: http://codespeak.net/py 

