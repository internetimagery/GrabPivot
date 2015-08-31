# Begin
# Find joints tool

import maya.mel as mel
import maya.cmds as cmds
from re import findall
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui

class Selector(object):
    """
    Set it all up
    """
    def __init__(s, objects):
        s.meshes = objects # Allowed meshes
        s.mesh = ""
        s.sjob = cmds.scriptJob(e=["SelectionChanged", s.selectionChanged], ro=True)
        s.tool = "TempSelectionTool"
        s.selectionFree = True

    """
    Monitor selection changes
    """
    def selectionChanged(s):
        print "selection Changed"
        if s.selectionFree:
            selection = cmds.ls(sl=True)
            if selection and selection[0] in s.meshes:
                s.switchTool()
                s.mesh = selection[0]

    """
    Switch to our custom picker tool
    """
    def switchTool(s):
        s.lastTool = cmds.currentCtx()
        if cmds.draggerContext(s.tool, ex=True):
            cmds.deleteUI(s.tool)
        cmds.draggerContext(
            s.tool,
            name=s.tool,
            pressCommand=s.makeSelection,
            cursor="hand")
        cmds.setToolTo(s.tool)
        s.selectionFree = False

    """
    Switch back to the last tool used
    """
    def revertTool(s):
        cmds.setToolTo(s.lastTool)
        s.selectionFree = True
        cmds.refresh()

    """
    Pick a point in space on the mesh
    """
    def makeSelection(s):
        if s.mesh:
            try:
                # Grab screen co-ords
                viewX, viewY, viewZ = cmds.draggerContext(s.tool, q=True, ap=True)
                # Set up empty vectors
                position = om.MPoint()
                direction = om.MVector()
                # Convert 2D positions into 3D positions
                omui.M3dView().active3dView().viewToWorld(int(viewX), int(viewY), position, direction)
                selection = om.MSelectionList()
                selection.add(s.mesh)
                dagPath = selection.getDagPath(0)
                fnMesh = om.MFnMesh(dagPath)
                # Shoot a ray and check for intersection
                intersection = fnMesh.closestIntersection(om.MFloatPoint(position), om.MFloatVector(direction), om.MSpace.kWorld, 99999, False)
                if intersection:
                    # Pick nearest bone with influence
                    s.pickSkeleton(intersection)
            except IOError:
                print "Could not make selection. Were you selecting the right object?"
        s.revertTool()

    """
    Pick a bone from a point in space
    """
    def pickSkeleton(s, intersection):
        hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = intersection
        if hitTriangle != -1:
            # Grab skin Cluster
            skin = mel.eval("findRelatedSkinCluster %s" % s.mesh)
            if skin:
                # Get Face selected
                cmds.select("%s.f[%s]" % (s.mesh, hitFace), r=True)
                face = cmds.polyInfo(fv=True)
                # Get Vertexes
                verts = ["%s.vtx[%s]" % (s.mesh, v) for v in findall(r"\s(\d+)\s", face[0])]
                # Get Joints
                cmds.select(verts, r=True)
                joints = cmds.skinPercent(skin, q=True, t=None)
                # Get weights
                weights = sorted(
                    [(j, cmds.skinPercent(skin, t=j, q=True)) for j in joints],
                    key=lambda x: x[1],
                    reverse=True)
                cmds.select(weights[0][0], r=True)
            else:
                print "No skin found."
        else:
            print "Nothing to select."

sel = cmds.ls(type="transform")
sel = ["pCylinder1"]
go = Selector(sel)
