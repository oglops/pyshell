import os
import re
import sys
import code
import pickle
import inspect

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import logging

logging.basicConfig(filename='/tmp/pyshell.log', level=logging.INFO)
logging.disable(logging.INFO)
_logger = logging.getLogger(__name__)

__VERSION__='0.13'

# this is for maya
try:
    import sip

    import maya.cmds as cmds
    import maya.OpenMayaUI as mui
except:
    pass

# http://stackoverflow.com/questions/12431555/enabling-code-completion-in-an-embedded-python-interpreter


class MyInterpreter(QtGui.QWidget):

    def __init__(self, parent, global_vars=None):

        super(MyInterpreter, self).__init__(parent)
        hBox = QtGui.QHBoxLayout()

        self.setLayout(hBox)
        self.textEdit = PyInterp(self, global_vars)

        # this is how you pass in locals to the interpreter
        # self.textEdit.initInterpreter(locals())

        self.resize(850, 400)
        # self.centerOnScreen()

        hBox.addWidget(self.textEdit)
        hBox.setMargin(0)
        hBox.setSpacing(0)

        self.setWindowTitle('python shell v%s by Uncle Han' % __VERSION__)

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

    def __init__(self,  parent, global_vars=None):
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

        # self.last_cursor=None

        # setting the color for bg and text
        palette = QtGui.QPalette()
        text_color = QtGui.QColor(179, 179, 179)
        # highlight_color=self.palette().highlight().color()
        bg_color=QtGui.QColor(46, 46, 46)
        palette.setColor(QtGui.QPalette.Base, bg_color)
        palette.setColor(QtGui.QPalette.Text,text_color )

        # palette.setColor(QtGui.QPalette.Highlight, highlight_color)
        # palette.setColor(QtGui.QPalette.HighlightedText, bg_color)
        # set highlight color

        self.setPalette(palette)
        self.setFont(QtGui.QFont('DejaVu Sans Mono', 10))

        # save default format
        self.default_char_format = self.textCursor().charFormat()

        # save selected \
        self.selected_range=None

        # last cursor position
        self.last_cursor_pos=self.textCursor().position()

        # initilize interpreter with self locals
        
        if global_vars is None:
            global_vars = inspect.getouterframes(inspect.currentframe())[-1][0].f_globals
        self.initInterpreter(global_vars)

        from rlcompleter2 import Completer

        self.completer = Completer()

        # extend default menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self.textChanged.connect(self.check_multiline)

        # set cursor shape
        # self.viewport().setCursor(Qt.PointingHandCursor)
        # self.setCursorWidth(10)
        self.cursorPositionChanged.connect(self.update_readonly)

        # disable rich text pasting
        self.setAcceptRichText(False)

        # clear undo
        self.document().clearUndoRedoStacks()

        # self.setAcceptDrops(False)

    def showContextMenu(self,pos):
        menu=self.createStandardContextMenu()
        menu.addSeparator()
        
        resetAction=menu.addAction('Reset')
        testAction=menu.addAction('Debug')
        action=menu.exec_(self.mapToGlobal(pos))
        # delete menu
        if action== testAction:
            # print len(locals()),len(globals()),len(vars(self.interpreter)),len(self.interpreter.locals)
            # print len(self.interpreter.locals)

            # print self.interpreter.locals
            self.textCursor().setPosition(self.last_cursor_pos)
        if action== resetAction:
            self.clear()
            self.marker()
            # update last_cursor_pos
            self.last_cursor_pos=self.textCursor().position()


    def check_multiline(self):
        self.blockSignals(True)
        # print 'check'
        with open('/tmp/test','a') as f:
            f.write('changed')
        self.blockSignals(False)

    def printBanner(self):
        self.write(sys.version)
        self.write(' on ' + sys.platform + '\n')
        self.write('PyQt4 ' + QtCore.PYQT_VERSION_STR + '\n')
        # msg = 'Type !hist for a history view and !hist(n) history index recall'
        # self.write(msg + '\n')
    # def get_last_line(self):
    #     for l in reversed(range(self.document().blockCount())):
    #         if str(self.document().findBlockByNumber(l).text()).startswith('>>>'):
    #             return l

    def update_readonly(self):
        # print 'save cursor\n'
        # self.last_cursor = self.textCursor()
        cursor = self.textCursor()

        if cursor.block().blockNumber()<self.get_last_block_num():
            pass
            self.setReadOnly(True)
            # self.blockSignals(True)
            # cursor.setPosition(22)
            # self.blockSignals(False)

        else:
            self.setReadOnly(False)

        



    def get_last_block_num(self):
        block_count = self.document().blockCount()
        for i in xrange(block_count,-1,-1):
            if str(self.document().findBlockByNumber(i).text()).startswith('>>>'):
                return i

        # if nothing found, return last line, but this is not possible
        return block_count


    def is_editing_allowed(self,cursor=None):
        allowed= False
        if cursor is None:
            cursor = self.textCursor()
        cur_blk_num = cursor.block().blockNumber()
        last_blk_num = self.get_last_block_num()
        _logger.info('is_editing_allowed %s %s %s %s' %(cur_blk_num,last_blk_num,self.textCursor().position(),self.textCursor().block().position()))
        if cur_blk_num >=last_blk_num:
            allowed=True
            # consider >>>
            if cur_blk_num == last_blk_num:
                if cursor.position() - cursor.block().position() <= 3:
                    allowed=False
                pass
        return allowed


    def mouseMoveEvent(self,event):
        # _logger.info('event: %s' %event.__class__)
        # _logger.info('release mouse button %s' %event.buttons())




        if event.button()== Qt.LeftButton:

            # cursor = self.textCursor()
            # # _logger.info('release mouse')
            # if cursor.hasSelection():
            #     start = cursor.selectionStart()
            #     end = cursor.selectionEnd()



            # set selected text color before releasing mouse button
            tmp = self.textCursor().charFormat()
            # tmp.setBackground(QtGui.QBrush(self.palette().highlight().color()))
            # tmp.setForeground(QtGui.QBrush(self.palette().background().color()))
            tmp.setBackground(QtGui.QBrush(self.palette().text().color()))
            tmp.setForeground(QtGui.QBrush(self.palette().base().color()))

            self.textCursor().setCharFormat(tmp)
            # print 'cursor changed'
            # self.textCursor().setPosition(3)

        super(PyInterp,self).mouseMoveEvent(event)    

    def mouseReleaseEvent(self,event):
        # _logger.info('event: %s' %event.__class__)
        # _logger.info('release mouse button %s' %event.buttons())
        cursor = self.textCursor()
        if event.button()== Qt.LeftButton:
            # check if editing is allowed
            # if not self.is_editing_allowed():
                # print 'left'
                # return
            # self.setTextCursor(self.last_cursorself.last_cursor)

            # store selected range if highlight selection
            
            # _logger.info('release mouse')
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                self.selected_range=(start,end)
                # _logger.info('save last selection: %s %s' %(start,end))



            else:
                self.selected_range=None

        elif event.button()== Qt.MiddleButton:
            cursor = self.cursorForPosition(event.pos())
            if self.is_editing_allowed(cursor):
                self.setReadOnly(False)
            else:
                # self.setReadOnly(True)
                return
        else:
            # print 'other'
            pass

        super(PyInterp,self).mouseReleaseEvent(event) 
        # _logger.info('restore last pos: %s' %self.last_cursor_pos)
        cursor.setPosition(self.last_cursor_pos) 
        # if event.button()== Qt.MiddleButton:
        #     self.setReadOnly(True)  

    def mousePressEvent(self,event):
        if event.buttons()== Qt.LeftButton:
            # check if editing is allowed
            # if not self.is_editing_allowed():
                # print 'left'
                # return
            # self.textCursor().setCharFormat(self.default_char_format)
            # block_count = self.document().blockCount()
            # for i in xrange(block_count,-1,-1):
            #     self.document().findBlockByNumber(i).textCursor().setCharFormat(self.default_char_format)

            # select all
            cursor=self.textCursor()
            if self.selected_range:
                start,end = self.selected_range
                cursor.setPosition(start)
                cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)

                self.textCursor().setCharFormat(self.default_char_format)
                # cursor.setCharFormat(self.default_char_format)

            pass
            # self.last_cursor = self.textCursor()
        elif event.buttons()== Qt.MiddleButton:
            # _logger.info('press mouse button %s' %event.buttons())
            # if middle click location is allowed to edit
            cursor = self.cursorForPosition(event.pos())
            if self.is_editing_allowed(cursor):
                _logger.info('editing_allowed' )
                self.setReadOnly(False)   
            else:
                _logger.info('not allowed' )
            #     event.ignore()
                return 

        else:
            # print 'other'
            pass

        super(PyInterp,self).mousePressEvent(event)
        self.textCursor().setCharFormat(self.default_char_format)
        # if event.buttons()== Qt.MiddleButton:
        #     self.setReadOnly(True)
        #     pass

    def dropEvent(self,event):
        # if drop from self
        if event.source():
            # print 'self drag'
            event.accept()
            # self.viewport().update()
            return

        # insert file path instead uri when dragging files from system
        cursor = self.cursorForPosition(event.pos())
        if self.is_editing_allowed(cursor):
            if event.mimeData().hasUrls:
                for url in event.mimeData().urls():
                    self.insertPlainText(str(url.toLocalFile()))
                return
        else:
            return

        super(PyInterp,self).dropEvent(event)

    # def dragEvent(self,event):
    #     # print event.source()
    #     if event.source():
    #         # print 'self drag'
    #         event.accept()
    #         # self.viewport().update()
    #         return

    #     super(PyInterp,self).dragEvent(event)

    def dragMoveEvent(self,event):
        # if drag from self
        if event.source():
            # print 'self drag'
            event.accept()
            self.viewport().update()
            return
        super(PyInterp,self).dragMoveEvent(event)

    def insertFromMimeData(self,source):
        # super(PyInterp,self).insertPlainText(source.text())
        # self.insertPlainText(source.text())
        lines = source.text().split('\n')
        if len(lines)>1:
            self.multiLine=True
            i=1
            for line in lines:

                if i>1:
                    self.marker()
                self.insertPlainText(line)
                self.insertPlainText('\n')
                i+=1

                self.command += str(line) + '\n' 
                

        else:
            # if source.hasUrls():
            #     print 'has url'
            #     # self.insertPlainText(source.urls()[0].path())
            # else:
                # text = source.text()
                # if text.startswith('file://'):
                #     text=text.lstrip('file://')
            self.insertPlainText(source.text())
            # self.insertPlainText('xxx')

    def marker(self):
        if self.multiLine:
            self.insertPlainText('... ')
        else:
            self.insertPlainText('>>> ')

        # update last_cursor_pos
        self.last_cursor_pos=self.textCursor().position()

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

        self.document().lastBlock().setUserState(666)

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

    def is_bracket_matching(self,line):
        multiline=False

        c = self.command or line
        # print 'command:',c
        if c.count('(')!=c.count(')') or c.count('[')!=c.count(']') or c.count('{')!=c.count('}'):
            multiline=True

        # print 'multiline:',multiline
        return multiline



    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Tab:
            line = str(self.document().lastBlock().text())[4:]
            # set width based on window width
            # window_width=self.frameGeometry().width()
            # self.completer.config.terminalwidth=160


            self.completer.construct(line)

            if len(self.completer.rl_matches) == 1:
                self.clearCurrentBlock()
                self.insertPlainText(self.completer.rl_matches[0])
            else:
                # print 'repeat:', self.completer.repeated

                mod = self.completer.repeated % len(self.completer.completions)
                if mod == 0:
                    # print self.completer.rl_matches
                    print ' '
                    col_print(self.completer.rl_matches)
                else:

                    print ' '
                    print '\n'.join(self.completer.rl_matches)
                    # print self.completer.rl_matches
                self.marker()
                self.insertPlainText(line)

            # scroll to bottom
            self.ensureCursorVisible()
            return

        # if event.key() == Qt.Key_Escape:
        #     # proper exit
        #     self.interpreter.runIt('exit()')

        # ctrl-c to reset current line 
        if event.key()== Qt.Key_C and event.modifiers()==Qt.ControlModifier:
            # self.interpreter.runIt('exit()')
            self.append('')
            self.command = ''
            self.marker()
            return

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
            # if self.textCursor().positionInBlock() == 4:
            if self.textCursor().position() - self.textCursor().block().position() == 4:
                return None

            if not self.is_editing_allowed():
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
                    if line.strip()[-1] == ':' or self.is_bracket_matching(line):
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


def main(global_vars=None):

    if str(QtGui.qApp.applicationName()).lower().startswith('maya'):
        global win
        try:
            win.close()
        except:
            pass
        win = MyInterpreter(None, global_vars)
        win.show()

    else:
        # _logger.info('start ...')
        app = QtGui.QApplication(sys.argv)
        win = MyInterpreter(None, global_vars)
        win.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()


# print 'xxx'
