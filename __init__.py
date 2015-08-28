# Animatable movable pivot
import maya.cmds as cmds

def Setup():
    selection = cmds.ls(sl=True)
    if selection:
        for obj in selection:
            objPos = cmds.xform(obj, q=True, t=True, ws=True)
            joint = cmds.joint(n="%s_pivot" % obj, p=objPos)
            cmds.parent(obj, joint)
            cmds.connectAttr("%s.translate" % joint, "%s.rotatePivot" % obj, f=True)
    else:
        cmds.confirmDialog(t="Uh..", m="You need to select something.")

Setup()
