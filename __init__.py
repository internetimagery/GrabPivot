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
            else:
                for mesh in s.meshes:
                    s.setColour(mesh)
        # print cmds.ls(selection, st=True)

    """
    Set vertex colour on selection
    """
    def setColour(s, mesh, colour=None):
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
        cmds.select(s.mesh, r=True)
        s.setColour(s.mesh, (0.5,0.5,0.5))

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
                    cmds.select(verts, r=True)
                    s.setColour(s.mesh, (0.3, 0.8, 0.1))
                    # cmds.select(bone, r=True)
        s.revertTool()

    """
    Update display
    """
    def updateSelectionPreview(s):
        print "dragging"

    """
    Get Mouse in 3D
    """
    def getPointer(s, mesh, tool):
        try:
            # Grab screen co-ords
            viewX, viewY, viewZ = cmds.draggerContext(tool, q=True, ap=True)
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
            # Grab original selection
            selection = cmds.ls(sl=True)
            # Grab skin Cluster
            skin = mel.eval("findRelatedSkinCluster %s" % s.mesh)
            if skin:
                # Get Face selected
                cmds.select("%s.f[%s]" % (s.mesh, hitFace), r=True)
                # face = cmds.polyInfo(fv=True)

                # joints = cmds.skinCluster(skin, q=True, wi=True)
                # weights = {}
                # verts = [v for v in findall(r"\s(\d+)\s", cmds.polyInfo(fv=True)[0])]
                # vertWeights = {}
                # for j in cmds.listAttr("%s.weightList" % skin, multi=True):
                #     parse = findall(r"\[(\d+)\]", j)
                #     if 1 < len(parse):
                #         joint = joints[int(parse[1])]
                #         weights[joint] = weights.get(joint, [])
                #         weights[joint].append("%s.vtx[%s]" % (s.mesh, parse[0]))
                #         if parse[0] in verts:
                #             vertWeights[joint] = vertWeights.get(joint, 0)
                #             vertWeights[joint] += cmds.getAttr("%s.%s" % (skin, j))
                # highestInfluence = max(vertWeights,key = lambda x: vertWeights.get(x))
                # return highestInfluence, weights[highestInfluence]


                face = cmds.polyInfo(fv=True)

                # Get Vertexes
                verts = ["%s.vtx[%s]" % (s.mesh, v) for v in findall(r"\s(\d+)\s", face[0])]
                # Get Joints
                cmds.select(verts, r=True)
                print cmds.skinPercent(skin, verts, v=True, q=True)
                # joints = cmds.skinPercent(skin, q=True, t=None)
                # # Get weights
                # weights = sorted(
                #     [(j, cmds.skinPercent(skin, t=j, q=True)) for j in joints],
                #     key=lambda x: x[1])
                # # Get other weights of the bone
                # cmds.select(selection)
                # return weights[-1][0]
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
