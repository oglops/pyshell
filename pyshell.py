import os
import re
import sys
import code
import pickle

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

# this is for maya
try:
    import sip

    import maya.cmds as cmds
    import maya.OpenMayaUI as mui
except:
    pass

# http://stackoverflow.com/questions/12431555/enabling-code-completion-in-an-embedded-python-interpreter


class MyInterpreter(QtGui.QWidget):

    def __init__(self, parent, local_vars):

        super(MyInterpreter, self).__init__(parent)
        hBox = QtGui.QHBoxLayout()

        self.setLayout(hBox)
        self.textEdit = PyInterp(self, local_vars)

        # this is how you pass in locals to the interpreter
        # self.textEdit.initInterpreter(locals())

        self.resize(850, 400)
        # self.centerOnScreen()

        hBox.addWidget(self.textEdit)
        hBox.setMargin(0)
        hBox.setSpacing(0)

        self.setWindowTitle('python shell v0.1 by oglop')

    def centerOnScreen(self):
        # center the widget on the screen
        resolution = QtGui.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))


class PyInterp(QtGui.QTextEdit):

    class InteractiveInterpreter(code.InteractiveInterpreter):

        def __init__(self, locals):
            code.InteractiveInterpreter.__init__(self, locals)

        def runIt(self, command):
            code.InteractiveInterpreter.runsource(self, command)

    def __init__(self,  parent, local_vars):
        super(PyInterp,  self).__init__(parent)

        sys.stdout = self
        sys.stderr = self
        self.refreshMarker = False  # to change back to >>> from ...
        self.multiLine = False  # code spans more than one line
        self.command = ''    # command to be ran
        self.printBanner()              # print sys info
        self.marker()                   # make the >>> or ... marker
        self.history = []    # list of commands entered
        self.historyIndex = -1
        self.interpreterLocals = {}

        # setting the color for bg and text
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(46, 46, 46))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(179, 179, 179))
        self.setPalette(palette)
        self.setFont(QtGui.QFont('DejaVu Sans Mono', 10))

        # initilize interpreter with self locals
        self.initInterpreter(local_vars)

        from rlcompleter2 import Completer

        self.completer = Completer()

        # extend default menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self,pos):
        menu=self.createStandardContextMenu()
        menu.addSeparator()
        testAction=menu.addAction('test')
        action=menu.exec_(self.mapToGlobal(pos))
        # delete menu
        if action== testAction:
            # print len(locals()),len(globals()),len(vars(self.interpreter)),len(self.interpreter.locals)
            print len(self.interpreter.locals)

            print self.interpreter.locals


    def printBanner(self):
        self.write(sys.version)
        self.write(' on ' + sys.platform + '\n')
        self.write('PyQt4 ' + QtCore.PYQT_VERSION_STR + '\n')
        # msg = 'Type !hist for a history view and !hist(n) history index recall'
        # self.write(msg + '\n')

    def marker(self):
        if self.multiLine:
            self.insertPlainText('... ')
        else:
            self.insertPlainText('>>> ')

    def initInterpreter(self, interpreterLocals=None):
        if interpreterLocals:
            # when we pass in locals, we don't want it to be named "self"
            # so we rename it with the name of the class that did the passing
            # and reinsert the locals back into the interpreter dictionary

            # maybe this still works when run outside maya
            try:
                selfName = interpreterLocals['self'].__class__.__name__
                interpreterLocalVars = interpreterLocals.pop('self')
                self.interpreterLocals[selfName] = interpreterLocalVars
            except:
                pass
                self.interpreterLocals = interpreterLocals
        else:
            self.interpreterLocals = interpreterLocals
        self.interpreter = self.InteractiveInterpreter(self.interpreterLocals)

    def updateInterpreterLocals(self, newLocals):
        className = newLocals.__class__.__name__
        self.interpreterLocals[className] = newLocals

    def write(self, line):
        self.insertPlainText(line)
        self.ensureCursorVisible()

    def clearCurrentBlock(self):
        # block being current row
        length = len(self.document().lastBlock().text()[4:])
        if length == 0:
            return None
        else:
            # should have a better way of doing this but I can't find it
            [self.textCursor().deletePreviousChar() for x in xrange(length)]
        return True

    def recallHistory(self):
        # used when using the arrow keys to scroll through history
        self.clearCurrentBlock()
        if self.historyIndex <> -1:
            self.insertPlainText(self.history[self.historyIndex])
        return True

    def customCommands(self, command):

        if command == '!hist':  # display history
            self.append('')  # move down one line
            # vars that are in the command are prefixed with ____CC and deleted
            # once the command is done so they don't show up in dir()
            backup = self.interpreterLocals.copy()
            history = self.history[:]
            history.reverse()
            for i, x in enumerate(history):
                iSize = len(str(i))
                delta = len(str(len(history))) - iSize
                line = line = ' ' * delta + '%i: %s' % (i, x) + '\n'
                self.write(line)
            self.updateInterpreterLocals(backup)
            self.marker()
            return True

        if re.match('!hist\(\d+\)', command):  # recall command from history
            backup = self.interpreterLocals.copy()
            history = self.history[:]
            history.reverse()
            index = int(command[6:-1])
            self.clearCurrentBlock()
            command = history[index]
            if command[-1] == ':':
                self.multiLine = True
            self.write(command)
            self.updateInterpreterLocals(backup)
            return True

        return False

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Tab:
            line = str(self.document().lastBlock().text())[4:]
            self.completer.construct(line)

            if len(self.completer.rl_matches) == 1:
                self.clearCurrentBlock()
                self.insertPlainText(self.completer.rl_matches[0])
            else:
                print 'repeat:', self.completer.repeated

                mod = self.completer.repeated % len(self.completer.completions)
                if mod == 0:
                    # print self.completer.rl_matches
                    col_print(self.completer.rl_matches)
                else:

                    print ' '
                    print '\n'.join(self.completer.rl_matches)
                    # print self.completer.rl_matches
                self.marker()
                self.insertPlainText(line)

            return

        if event.key() == Qt.Key_Escape:
            # proper exit
            self.interpreter.runIt('exit()')

        if event.key() == Qt.Key_Down:
            if self.historyIndex == len(self.history):
                self.historyIndex -= 1
            try:
                if self.historyIndex > -1:
                    self.historyIndex -= 1
                    self.recallHistory()
                else:
                    self.clearCurrentBlock()
            except:
                pass
            return None

        if event.key() == Qt.Key_Up:
            try:
                if len(self.history) - 1 > self.historyIndex:
                    self.historyIndex += 1
                    self.recallHistory()
                else:
                    self.historyIndex = len(self.history)
            except:
                pass
            return None

        if event.key() == Qt.Key_Home:
            # set cursor to position 4 in current block. 4 because that's where
            # the marker stops
            blockLength = len(self.document().lastBlock().text()[4:])
            lineLength = len(self.document().toPlainText())
            position = lineLength - blockLength
            textCursor = self.textCursor()
            textCursor.setPosition(position)
            self.setTextCursor(textCursor)
            return None

        if event.key() in [Qt.Key_Left, Qt.Key_Backspace]:
            # don't allow deletion of marker
            # if qt version < 4.7, have to use position() - block().position()
            if self.textCursor().positionInBlock() == 4:
                return None

        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            # set cursor to end of line to avoid line splitting
            textCursor = self.textCursor()
            position = len(self.document().toPlainText())
            textCursor.setPosition(position)
            self.setTextCursor(textCursor)

            line = str(self.document().lastBlock().text())[4:]  # remove marker
            line.rstrip()
            self.historyIndex = -1

            if self.customCommands(line):
                return None
            else:
                try:
                    line[-1]
                    self.haveLine = True
                    if line[-1] == ':':
                        self.multiLine = True
                    self.history.insert(0, line)
                except:
                    self.haveLine = False

                if self.haveLine and self.multiLine:  # multi line command
                    self.command += line + '\n'  # + command and line
                    self.append('')  # move down one line
                    self.marker()  # handle marker style
                    return None

                if self.haveLine and not self.multiLine:  # one line command
                    self.command = line  # line is the command
                    self.append('')  # move down one line
                    self.interpreter.runIt(self.command)
                    self.command = ''  # clear command
                    self.marker()  # handle marker style
                    return None

                if self.multiLine and not self.haveLine:  # multi line done
                    self.append('')  # move down one line
                    self.interpreter.runIt(self.command)
                    self.command = ''  # clear command
                    self.multiLine = False  # back to single line
                    self.marker()  # handle marker style
                    return None

                if not self.haveLine and not self.multiLine:  # just enter
                    self.append('')
                    self.marker()
                    return None
                return None

        # allow all other key events
        super(PyInterp, self).keyPressEvent(event)
# http://stackoverflow.com/a/30861871/2052889


def col_print(lines, term_width=90, indent=0, pad=2):
    n_lines = len(lines)
    if n_lines == 0:
        return

    col_width = max(len(line) for line in lines)
    n_cols = int((term_width + pad - indent)/(col_width + pad))
    n_cols = min(n_lines, max(1, n_cols))

    col_len = int(n_lines/n_cols) + (0 if n_lines % n_cols == 0 else 1)
    if (n_cols - 1) * col_len >= n_lines:
        n_cols -= 1

    cols = [lines[i*col_len: i*col_len + col_len] for i in range(n_cols)]

    rows = list(zip(*cols))
    rows_missed = zip(*[col[len(rows):] for col in cols[:-1]])
    rows.extend(rows_missed)

    for row in rows:
        print(" "*indent + (" "*pad).join(line.ljust(col_width)
                                          for line in row))


def getMayaWindow():
    'Get the maya main window as a QMainWindow instance'
    ptr = mui.MQtUtil.mainWindow()
    return sip.wrapinstance(long(ptr), QtCore.QObject)


def main(local_vars=locals()):

    if str(QtGui.qApp.applicationName()).lower().startswith('maya'):
        global win
        try:
            win.close()
        except:
            pass
        win = MyInterpreter(None, local_vars)
        win.show()

    else:
        # print 'in else'
        app = QtGui.QApplication(sys.argv)
        win = MyInterpreter(None, local_vars)
        win.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()


# print 'xxx'
