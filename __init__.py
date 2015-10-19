# Begin
# Find joints tool

import maya.mel as mel
import maya.cmds as cmds
from re import findall
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
from pprint import pprint
from time import time
import traceback


class Selection(object):
    def __init__(s, win):
        s.ignore = False
        s.call = []
        s.selection = []
        cmds.scriptJob(e=["SelectionChanged", s.run], p=win)
    def run(s):
        if s.ignore:
            s.ignore = False
        else:
            s.selection = cmds.ls(sl=True)
            try:
                if s.call:
                    for c in s.call:
                        c(s.selection)
            except:
                print traceback.format_exc()

class Window(object):
    def __init__(s):
        winName = "BETAWIN"
        if cmds.window(winName, ex=True):
            cmds.deleteUI(winName)
        win = cmds.window(winName, s=False, rtf=True, t="(BETA TEST) Controllerless Rigging")
        cmds.columnLayout(adj=True)
        cmds.text(h=30, l="Controllerless Rig active on the following objects:")
        s.wrapper = cmds.scrollLayout(cr=True, bgc=[0.2,0.2,0.2], h=100)
        cmds.text(l="Nothing here...")
        cmds.setParent("..")
        cmds.button(h=40, l="Click to use selected objects (skinned meshes).", c=lambda x: s.addMesh())
        cmds.separator()
        cmds.text(al="left", l="""
Some notes:
-  If you add a TEXT attribute to the joint named "control" and give it the name
of another object in the scene (ie a controller/IK handle etc) it will be selected
instead of the bone itself.
-  If you add a NUMERAL (float/int) attribute to the controller / bone named "selected",
it will be set to "1" when selected and set to "0" when not.
""")
        cmds.showWindow(win)
        s.select = Selection(win)
        s.select.call.append(s.selectUpdate)
        s.picker = Picker(s.select)
        s.selection = []

    def addMesh(s):
        s.selection = cmds.ls(sl=True, type="transform")
        cmds.deleteUI(cmds.layout(s.wrapper, q=True, ca=True))
        if s.selection:
            s.picker.cache(s.selection)
            for o in s.selection:
                cmds.text(l=o, p=s.wrapper)
        else:
            s.picker.cache()
            cmds.text(l="Nothing here...", p=s.wrapper)

    def selectUpdate(s, sel):
        if s.selection:
            if cmds.currentCtx() != s.picker.tool:
                if sel and len(sel) == 1:
                    if sel[0] in s.selection:
                        # Turn on our picker!!
                        print "Turning on Picker"
                        s.select.ignore = True
                        # Make the mesh look different to make it obvious
                        # That we're doing something with it.
                        s.picker.switchTool(sel[0])
                        cmds.select(clear=True)
                        cmds.refresh()

class Picker(object):
    """
    Controllerless Picker
    """
    def __init__(s, select):
        s.meshes = {} # Meshes to look for
        s.joints = {} # Joints associated with em
        s.select = select # Selection interface
        s.tool = "ControllerlessSelection" # Tool name
        s.lastTool = "" # Previous tool
        s.lastJoint = "" # Previous joint, only display joint during drag on changes
        s.lastControl = "" # Previous control selected
        s.select.call.append(s.closeTool)
        s.active = False # Tool state

    def cache(s, meshes=None):
        """
        Store joints influence on objects for quick checking later
        """
        if meshes:
            # Cache Joints and Meshes
            for mesh in meshes:
                skin = mel.eval("findRelatedSkinCluster %s" % mesh)
                if skin:
                    joints = cmds.skinPercent(skin, "%s.vtx[0]" % mesh, q=True, t=None)
                    for vert in range(cmds.getAttr("%s.weightList" % skin, size=True)):
                        for i, v in enumerate(cmds.skinPercent(skin, "%s.vtx[%s]" % (mesh, vert), q=True, v=True)):
                            joint = joints[i]
                            if 0.2 < v:
                                # Sort by joints
                                s.joints[joint] = s.joints.get(joint, [])
                                s.joints[joint].append("%s.vtx[%s]" % (mesh, vert))
                                # Sort by meshes
                                s.meshes[mesh] = s.meshes.get(mesh, {})
                                s.meshes[mesh][joint] = s.meshes[mesh].get(joint, {})
                                s.meshes[mesh][joint][vert] = v
            # Speed up Cache
            if s.joints:
                s.select.ignore = True
                for j in s.joints:
                    cmds.select(s.joints[j], r=True)
                    s.joints[j] = cmds.filterExpand(ex=False, sm=31)
                cmds.select(clear=True)
        else:
            s.meshes = {}
            s.joints = {}
        pass

    def switchTool(s, mesh=None):
        """
        Switch to our selection tool
        """
        s.lastTool = cmds.currentCtx()
        ### For testing, refresh the tool each time this is run!
        if cmds.draggerContext(s.tool, ex=True):
            cmds.deleteUI(s.tool)
        ###
        if mesh and mesh in s.meshes:
            s.setColour("%s.vtx[0:]" % mesh, (0.4,0.4,0.4)) # Highlight mesh if provided.
        cmds.draggerContext(
            s.tool,
            name=s.tool,
            releaseCommand=s.makeSelection,
            dragCommand=s.updateSelectionPreview, # Preview selection while dragging
            cursor="hand",
            image1="hands.png")
        cmds.setToolTo(s.tool)
        s.active = True

    def revertTool(s):
        """
        Drop back to the previous tool once selection is made.
        """
        cmds.setToolTo(s.lastTool)
        cmds.refresh()

    def closeTool(s, sel):
        """
        Remove mesh highlighting etc when tool officially stops.
        """
        if cmds.currentCtx() != s.tool and s.active:
            s.active = False
            s.setColour()
            if s.lastControl:
                cmds.setAttr(s.lastControl, 0)

    def setColour(s, selection=None, colour=None):
        """
        Colour the mesh for visual feedback.
        This step slows down the process a bit.
        """
        for mesh in s.meshes:
            cmds.polyColorPerVertex("%s.vtx[0:]" % mesh, rgb=(0.5,0.5,0.5))
            if colour:
                cmds.setAttr("%s.displayColors" % mesh, 1)
            else:
                cmds.setAttr("%s.displayColors" % mesh, 0)
        if selection and colour:
            cmds.polyColorPerVertex(selection, rgb=colour)
            s.turnOffColours = True # There is colour to be turned off

    def boneSetColour(s, bone, colour):
        """
        Colour our meshes based on a Joint.
        """
        if s.joints and bone in s.joints:
            s.setColour(s.joints[bone], colour)

    def getPointer(s):
        """
        Get intersection point on the mesh from the mouse click.
        """
        if s.meshes:
            try:
                # Grab screen co-ords
                viewX, viewY, viewZ = cmds.draggerContext(s.tool, q=True, dp=True)
                # Set up empty vectors
                position = om.MPoint()
                direction = om.MVector()
                # Convert 2D positions into 3D positions
                omui.M3dView().active3dView().viewToWorld(int(viewX), int(viewY), position, direction)
                # Check our meshes
                for mesh in s.meshes:
                    selection = om.MSelectionList()
                    selection.add(mesh)
                    dagPath = selection.getDagPath(0)
                    fnMesh = om.MFnMesh(dagPath)
                    # Shoot a ray and check for intersection
                    intersection = fnMesh.closestIntersection(om.MFloatPoint(position), om.MFloatVector(direction), om.MSpace.kWorld, 99999, False)
                    # hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = intersection
                    if intersection and intersection[3] != -1:
                        return (mesh, intersection[2]) # hit mesh and face ID
            except RuntimeError:
                pass
        # print "Could not find a point."

    def pickSkeleton(s, mesh, faceID):
        """
        Pick a bone, given a skinned mesh and a face ID
        """
        # Get verts from Face
        meshes = s.meshes
        verts = [int(v) for v in findall(r"\s(\d+)\s", cmds.polyInfo("%s.f[%s]" % (mesh, faceID), fv=True)[0])]

        weights = {}
        for joint in meshes[mesh]:
            weights[joint] = weights.get(joint, 0) # Initialize
            weights[joint] = sum([meshes[mesh][joint][v] for v in verts if v in meshes[mesh][joint]])

        if weights:
            maxWeight = max(weights, key=lambda x: weights.get(x))
            return maxWeight

    def updateSelectionPreview(s):
        """
        Preview selection if mouse is dragging the mesh.
        """
        intersection = s.getPointer()
        if intersection:
            # Pick nearest bone with influence
            mesh, faceID = intersection
            bone = s.pickSkeleton(mesh, faceID)
            if bone:
                if bone == s.lastJoint:
                    pass # No need to do anything
                else:
                    t = time()
                    s.lastJoint = bone
                    s.boneSetColour(bone, (9, 0.7, 0.3))
                    cmds.refresh()

    def makeSelection(s):
        """
        Finalize Selection
        """
        intersection = s.getPointer()
        if intersection:
            # Pick nearest bone with influence
            mesh, faceID = intersection
            bone = s.pickSkeleton(mesh, faceID)
            if bone:
                # If the bone has an attribute "control"
                # Follow that attribute to the source.
                if cmds.attributeQuery("control", n=bone, ex=True):
                    controller = cmds.getAttr("%s.control" % bone)
                else:
                    controller = bone
                s.expectedChange = True
                s.select.ignore = True
                cmds.select(controller, r=True)
                s.boneSetColour(bone, (0.3, 0.8, 0.1))
                # If we have previously selected a joint. Turn off selected flag
                if s.lastControl:
                    cmds.setAttr(s.lastControl, 0)
                if cmds.attributeQuery("selected", n=controller, ex=True):
                    s.lastControl = "%s.selected" % controller
                    cmds.setAttr(s.lastControl, 1)
        else:
            print "Nothing to select."
        s.revertTool()


Window()
