# Animatable movable pivot
import maya.cmds as cmds
#
# def Setup():
#     selection = cmds.ls(sl=True)
#     if selection:
#         for obj in selection:
#             objPos = cmds.xform(obj, q=True, t=True, ws=True)
#             joint = cmds.joint(n="%s_pivot" % obj, p=objPos)
#             cmds.parent(obj, joint)
#             cmds.connectAttr("%s.translate" % joint, "%s.rotatePivot" % obj, f=True)
#     else:
#         cmds.confirmDialog(t="Uh..", m="You need to select something.")
#
# Setup()


# Other stuff
class Tool(object):
    def __enter__(s):
        s.ctx = cmds.currentCtx() # Get current tool
    def __exit__(s, err, type, trace):
        cmds.setToolTo(s.ctx) # reset tool


##############################
import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui


class SamsClass():
    def __init__(self):    # __init__ is a special function that "initialises" classes.
        pass


    def events(self, *args):
        self.meshSelection=cmds.ls(type='mesh')

        Context='Context'

        #onPress is called when the user clicks on the surface of the mesh
        def onPress():
            vpX, vpY, _ = cmds.draggerContext('Context', query=True, anchorPoint=True)
            pos = om.MPoint()
            dir = om.MVector()
            omui.M3dView().active3dView().viewToWorld(int(vpX)  , int(vpY), pos, dir)
            for mesh in self.meshSelection:
                selectionList = om.MSelectionList()
                selectionList.add(mesh)
                dagPath = selectionList.getDagPath(0)
                fnMesh = om.MFnMesh(dagPath)
                self.intersection = fnMesh.closestIntersection(om.MFloatPoint(pos), om.MFloatVector(dir), om.MSpace.kWorld, 99999, False)
                print "pressing now 1"
                if self.intersection:
                    hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = self.intersection
                    if hitTriangle != -1:
                        #create locator
                        self.loc1= cmds.spaceLocator(p=(hitPoint[0],hitPoint[1],hitPoint[2]), a=True)
                        cmds.refresh()


        if cmds.draggerContext(Context, exists=True):
            cmds.deleteUI(Context)
        cmds.draggerContext(Context, pressCommand=onPress, name=Context, cursor='crossHair')
        cmds.setToolTo(Context)

# a = SamsClass()
# a.events()
import maya.cmds as cmds
import maya.api.OpenMaya as om

class NewTool(object):
    def __init__(s):
        s.tool = cmds.currentCtx()
        s.myTool = "TempTool"
        if cmds.draggerContext(s.myTool, exists=True):
            cmds.deleteUI(s.myTool)
        cmds.draggerContext(s.myTool, name=s.myTool, pressCommand=s.click, cursor='crossHair', space="world")
        cmds.setToolTo(s.myTool)
    def click(s):
        print "clicked"
        print cmds.draggerContext(s.myTool, q=True, ap=True)
        cmds.setToolTo(s.tool)


cmds.scriptJob(ct=["SomethingSelected", NewTool], ro=True)
