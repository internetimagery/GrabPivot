# Selection callback. Dies with GUI
import maya.cmds as cmds

class Selection(object):
    def __init__(s, win):
        s.ignore = False
        s.call = []
        cmds.scriptJob(e=["SelectionChanged", s.run], p=win)
    def run(s):
        if not s.ignore:
            sel = cmds.ls(sl=True)
            if s.call:
                for c in s.call:
                    c(sel)
    def __enter__(s):
        s.ignore = True
        return s
    def __exit__(s, *err):
        s.ignore = False

if __name__ == '__main__':
    def test(sel):
        print "Selection Changed", sel
    win = cmds.window()
    cmds.columnLayout()
    cmds.text(l="Close window to stop selection callbacks")
    cmds.showWindow(win)
    s = Selection(win)
    s.call.append(test)
