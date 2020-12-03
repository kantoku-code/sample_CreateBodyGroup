# Fusion360API Python script-sample_CreateBodyGroup
# Fusion360 ver2.0.9313
import adsk.core, adsk.fusion, traceback
from .BodiesGroupFactry import bodiesGroupFactry

_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)

def createBoxes(
    comp :adsk.fusion.Component,
    count :int
    ):

    def createBox(
        comp :adsk.fusion.Component,
        pnt :adsk.core.Point3D
        ) -> adsk.fusion.BRepBody:

        vec3D = adsk.core.Vector3D
        lVec = vec3D.create(1.0, 0.0, 0.0)
        wVec= vec3D.create(0.0, 1.0, 0.0)

        bouBox3D = adsk.core.OrientedBoundingBox3D
        box = bouBox3D.create(pnt, lVec, wVec, 10, 10, 10)

        tmpBrMgr = adsk.fusion.TemporaryBRepManager.get()

        baseFeats = comp.features.baseFeatures
        baseFeat = baseFeats.add()
        baseFeat.startEdit()
        cube :adsk.fusion.BRepBody = comp.bRepBodies.add(tmpBrMgr.createBox(box),baseFeat)
        baseFeat.finishEdit()

        return cube

    # return boxis
    bodies = []
    for idx in range(count):
        bodies.append(createBox(
            comp,
            adsk.core.Point3D.create(0.0 + float(20.0 * idx), 0.0, 0.0)))

    return bodies

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        _app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)

        des  :adsk.fusion.Design = _app.activeProduct
        root :adsk.fusion.Component = des.rootComponent

        # createBoxes
        vec3D = adsk.core.Vector3D
        mat3D = adsk.core.Matrix3D

        # Root Component
        bodies = createBoxes(root, 10)

        # Occurrence
        comp = root
        step = 25
        for idx in range(1,3):
            print(idx)
            vec = vec3D.create(step+idx, step+idx, step+idx)
            mat = mat3D.create()
            mat.translation = vec
            occ = comp.occurrences.addNewComponent(mat)
            comp = occ.component

            bodies = createBoxes(comp, 10)

        # message
        vp :adsk.core.Viewport = _app.activeViewport
        vp.fit()
        _ui.messageBox('Group the bodies.')

        bodiesList = [root.bRepBodies]
        bodiesList.extend([occ.bRepBodies for occ in root.allOccurrences])

        groupFact = bodiesGroupFactry()
        for bodies in bodiesList:

            # Grouping
            groupOdd = [box for idx,box in enumerate(bodies) if idx % 2 == 0]
            groupEven = [box for idx,box in enumerate(bodies) if idx % 2 != 0]

            # createBodiesGroup
            groupFact.createBodiesGroup(groupOdd,'Odd')
            groupFact.createBodiesGroup(groupEven, 'Even')

        _ui.messageBox('done')

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))