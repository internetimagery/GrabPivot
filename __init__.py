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

import maya.mel as mel
import maya.cmds as cmds
from re import findall, UNICODE
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui

class NewTool(object):
    def __init__(s):
        pass
    def load(s):
        sel = cmds.ls(sl=True)
        if sel:
            s.sel = sel[0]
            s.tool = cmds.currentCtx()
            s.myTool = "TempTool"
            if cmds.draggerContext(s.myTool, exists=True):
                cmds.deleteUI(s.myTool)
            cmds.draggerContext(s.myTool, name=s.myTool, pressCommand=s.click, cursor='crossHair')
            cmds.setToolTo(s.myTool)
        else:
            print "Nothing selected"
    def click(s):
        # MGlobal::selectFromScreen()
        # Grab mouse co-ords on screen
        viewX, viewY, viewZ = cmds.draggerContext(s.myTool, q=True, ap=True)
        position = om.MPoint()
        direction = om.MVector()
        # Convert 2D screen positions into 3D world positions
        omui.M3dView().active3dView().viewToWorld(int(viewX), int(viewY), position, direction)
        sel = om.MSelectionList()
        sel.add(s.sel)
        dagPath = sel.getDagPath(0)
        fnMesh = om.MFnMesh(dagPath)
        intersection = fnMesh.closestIntersection(om.MFloatPoint(position), om.MFloatVector(direction), om.MSpace.kWorld, 99999, False)
        # Did our ray intersect with the object?
        if intersection:
            hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = intersection
            if hitTriangle != -1:
                # Grab Skin Cluster
                skin = mel.eval("findRelatedSkinCluster %s" % s.sel)
                if skin:
                    # Get Face points
                    cmds.select("%s.f[%s]" % (s.sel, hitFace))
                    face = cmds.polyInfo(fv=True)
                    # Get vertexes
                    verts = ["%s.vtx[%s]" % (s.sel, v) for v in findall(r"\s(\d+)\s", face[0])]
                    # Get Joints
                    joints = cmds.skinPercent(skin, verts, q=True, t=None)
                    #     print cmds.skinPercent(skin, "%s.vtx[%s]" % (s.sel, vert), q=True, v=True)
                    # print "hit face id %s" % hitFace
                    #create locator
                    # loc1= cmds.spaceLocator(p=(hitPoint[0],hitPoint[1],hitPoint[2]), a=True)
                    # cmds.refresh()
                else:
                    print "No skin found"
        # Return to previous tool
        cmds.refresh()
        cmds.setToolTo(s.tool)

thing = NewTool()
thing.load()
# print cmds.scriptJob(ct=["SomethingSelected", thing.load], ro=True)
