python command shell for maya
===================

This is a python command shell for maya with auto complete

Usage
------------------
    import pyshell
    pyshell.main()
    
如果想加到maya菜单里，必须把globals()当参数传进去,utils.py 和 userSetup.py是如何加菜单的举例

    global_vars = inspect.getouterframes(inspect.currentframe())[-1][0].f_globals
	add_menu(label="Python Command Shell",command= lambda *x: __import__("pyshell").main(global_vars))


Current Status
------------------

desired effect:
http://gfycat.com/WindyLeanDog
![gfycat](https://fat.gfycat.com/WindyLeanDog.gif)


Changelog
------------------
01/22/2016
* multiline pasting now working

01/05/2016
* auto complete not fully working yet

