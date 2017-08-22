python command shell for maya
===================

This is a python command shell for maya with auto complete

Usage
------------------
    import pyshell
    pyshell.main()

其实只需要pyshell.py这一个文件就行，rlcompleter2你可以从pip装，lz没有在windows下测试，windows下你可以参考[python tips : rlcompleter & rlcompleter2 tab自动完成](https://ilmvfx.wordpress.com/2014/04/08/python-tips-rlcompleter-rlcompleter2-tab-auto-complete/)

另外,如果想加到maya菜单里，必须把globals()当参数传进去,utils.py 和 userSetup.py 里面有举例
```python
global_vars = inspect.getouterframes(inspect.currentframe())[-1][0].f_globals
add_menu(label="Python Command Shell",command= lambda *x: __import__("pyshell").main(global_vars))
```

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

