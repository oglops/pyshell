import maya.mel as mm
import maya.cmds as mc

import utils
reload(utils)

mc.evalDeferred('utils.add_pyshell_menu()',lp=1)
