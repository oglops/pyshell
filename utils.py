import maya.mel as mm
import maya.cmds as mc
import inspect


def add_menu(location='Window->General Editors', label='xxx', command='print "xxx"'):
    '''
    Add menu to specified location in main menu.

    Args:
        location: Window->General Editors.
        label: the label on the menu.
        command: the command
    '''
    # gMainWindowMenu='mainWindowMenu'
    import maya.cmds as mc
    menu_path = location.split('->')

    def get_menu_item(label, parent_menu=None):
        'returns menu item with label in parent_menu'
        menu_item = None
        
        # if it is top level menu
        for m in mc.lsUI(type='menu'):
            if mc.objectTypeUI(m) != 'commandMenuItem' and mc.menu(m, q=1, l=1) == label:
                menu_item = m

                if parent_menu:
                    if not menu_item in mc.menu(parent_menu, q=1, ia=1) or []:
                        continue
                else:
                    break

        pmc = mc.menu(menu_item, q=1, pmc=1)
        if pmc:
            mm.eval(pmc)

        return menu_item

    parent_menu = None
    for m in menu_path:
        menu_item = get_menu_item(m, parent_menu)
        parent_menu = menu_item

    print parent_menu

    # delete existing menuItem
    if mc.menu(parent_menu, q=1, ia=1):
        for m in mc.menu(parent_menu, q=1, ia=1):
            if mc.menuItem(m, q=1, l=1) == label:
                mc.deleteUI(m)
                break

    mc.setParent(menu_item, m=1)
    mc.menuItem(l=label, c=command)


def add_pyshell_menu():
    import maya.cmds as mc
    global_vars = inspect.getouterframes(
        inspect.currentframe())[-1][0].f_globals
    add_menu(label="Python Command Shell", command=lambda *
             x: __import__("pyshell").main(global_vars))


def add_toolbox_menu():
    gridLayout = 'hj_gridLayout'
    if mc.gridLayout(gridLayout, q=1, ex=1):
        mc.deleteUI(gridLayout)

    mc.setParent('flowLayout2')
    size=36
    mc.gridLayout(gridLayout, nc=1, cwh=[size, size])
    mc.setParent(gridLayout)

    global_vars = inspect.getouterframes(
        inspect.currentframe())[-1][0].f_globals
    # global_vars = globals()
    mc.shelfButton(
        i='play.png', c=lambda *x: __import__("pyshell").main(global_vars),w=40)
