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
        s.sjob = cmds.scriptJob(e=["SelectionChanged", s.selectionChanged], kws=True)#, ro=True)
        s.tool = "TempSelectionTool"
        s.clearMeshes = False # Do we need to clear the meshes?

    """
    Monitor selection changes
    """
    def selectionChanged(s):
        print "selection Changed"
        selection = cmds.ls(sl=True)
        if cmds.currentCtx() != s.tool:
            if selection and len(selection) == 1 and selection[0] in s.meshes:
                s.switchTool()
                s.mesh = selection[0]
                s.setColour(s.mesh, (0.5,0.5,0.5))
                s.clearMeshes = True
            elif selection and cmds.ls(sl=True, st=True)[1] == "joint":
                print "No need to clear"
            else:
                if s.clearMeshes:
                    for mesh in s.meshes:
                        s.setColour(mesh)
                    s.clearMeshes = False

    """
    Set vertex colour on selection
    """
    def setColour(s, mesh, colour=None):
        selection = cmds.ls(sl=True)
        cmds.select(mesh, r=True)
        cmds.polyColorPerVertex(rgb=(0.5,0.5,0.5))
        cmds.select(selection, r=True)
        if colour:
            cmds.setAttr("%s.displayColors" % mesh, 1)
            cmds.polyColorPerVertex(rgb=colour)
        else:
            cmds.setAttr("%s.displayColors" % mesh, 0)

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
            releaseCommand=s.makeSelection,
            dragCommand=s.updateSelectionPreview,
            cursor="hand")
        cmds.setToolTo(s.tool)


    """
    Switch back to the last tool used
    """
    def revertTool(s):
        cmds.setToolTo(s.lastTool)
        cmds.refresh()

    """
    Pick a point in space on the mesh
    """
    def makeSelection(s):
        if s.mesh:
            intersection = s.getPointer(s.mesh, s.tool)
            if intersection:
                # Pick nearest bone with influence
                bone, verts = s.pickSkeleton(intersection)
                if bone:
                    cmds.select(["%s.vtx[%s]" % (s.mesh, v) for v in verts.keys()], r=True)
                    s.setColour(s.mesh, (0.3, 0.8, 0.1))
                    cmds.select(bone, r=True)
                    s.clearMeshes = True
        s.revertTool()

    """
    Update display
    """
    def updateSelectionPreview(s):
        if s.mesh:
            intersection = s.getPointer(s.mesh, s.tool)
            if intersection:
                # Pick nearest bone with influence
                bone, verts = s.pickSkeleton(intersection)
                if bone:
                    cmds.select(["%s.vtx[%s]" % (s.mesh, v) for v in verts.keys()], r=True)
                    s.setColour(s.mesh, (0.3, 0.8, 0.1))
                    cmds.select(s.mesh, r=True)
                    s.clearMeshes = True
            cmds.refresh()

    """
    Get Mouse in 3D
    """
    def getPointer(s, mesh, tool):
        try:
            # Grab screen co-ords
            viewX, viewY, viewZ = cmds.draggerContext(tool, q=True, dp=True)
            # Set up empty vectors
            position = om.MPoint()
            direction = om.MVector()
            # Convert 2D positions into 3D positions
            omui.M3dView().active3dView().viewToWorld(int(viewX), int(viewY), position, direction)
            selection = om.MSelectionList()
            selection.add(mesh)
            dagPath = selection.getDagPath(0)
            fnMesh = om.MFnMesh(dagPath)
            # Shoot a ray and check for intersection
            intersection = fnMesh.closestIntersection(om.MFloatPoint(position), om.MFloatVector(direction), om.MSpace.kWorld, 99999, False)
            return intersection
        except RuntimeError:
            print "Could not find point."


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
                verts = [int(v) for v in findall(r"\s(\d+)\s", cmds.polyInfo(fv=True)[0])]
                joints = cmds.skinPercent(skin, "%s.vtx[0]" % s.mesh, q=True, t=None)
                weights = {}
                selWeights = {}
                for vert in range(cmds.getAttr("%s.weightList" % skin, size=True)):
                    for i, v in enumerate(cmds.skinPercent(skin, "%s.vtx[%s]" % (s.mesh, vert), q=True, v=True)):
                        joint = joints[i]
                        if 0.2 < v:
                            weights[joint] = weights.get(joint, {})
                            weights[joint][vert] = v
                        if vert in verts:
                            selWeights[joint] = selWeights.get(joint, 0)
                            selWeights[joint] += v
                maxWeight = max(selWeights, key=lambda x: selWeights.get(x))
                return maxWeight, weights[maxWeight]
            else:
                print "No skin found."
        else:
            print "Nothing to select."
        return None, None

sel = cmds.ls(type="transform")
sel = ["pCylinder1"]
go = Selector(sel)

# result = {}
# for i in cmds.listAttr("skinCluster1.weightList", multi=True):
#     match = findall(r"\[(\d+)\]", i)
#     if len(match) == 1:
#         result[match[0]] = []
#     else:
#         result[match[0]].append(match[1])
