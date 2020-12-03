#Fusion360API Python BodiesGroupFactry ver0.0.1
#Author-kantoku
#Description-Support the creation of BodiessGroups.

import adsk.core
import adsk.fusion
import json
import neu_server
import neu_modeling

_app = adsk.core.Application.cast(None)

# component extension methods
def isRoot(self :adsk.fusion.Component) -> bool:
    return self == self.parentDesign.rootComponent

# occurrence extension methods
def isRootOcc(self: adsk.fusion.Occurrence):
    return False

# bRepBody extension methods
def getParent(self :adsk.fusion.BRepBody) -> adsk.core.Base:
    comp = adsk.fusion.Component.cast(self.parentComponent)
    root :adsk.fusion.Component = comp.parentDesign.rootComponent

    if comp.isRoot():
        return root
    
    occs :adsk.fusion.OccurrenceList = root.occurrencesByComponent(comp)
    if occs.count < 1:
        return None

    return occs[0]



class bodiesGroupFactry():

    app = adsk.core.Application.cast(None)
    ui = adsk.core.UserInterface.cast(None)

    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface

        adsk.fusion.Component.isRoot = isRoot
        adsk.fusion.Occurrence.isRoot = isRootOcc
        adsk.fusion.BRepBody.getParent = getParent
    
    def __del__(self):
        del adsk.fusion.Component.isRoot
        del adsk.fusion.Occurrence.isRoot
        del adsk.fusion.BRepBody.getParent

    # 
    # param:bodiesList-list(BRepBody)_The body in the same component only!!
    # param:groupName(Optional)-str
    # return-bool
    def createBodiesGroup(
        self,
        bodiesList :list,
        groupName :str = ''
        ) -> bool:

        # ----- Support Functions -----
        # 選択された要素のPaths取得
        def getSelectPathsId(
            ent
            ) -> str:
            
            sels :adsk.core.Selections = self.ui.activeSelections
            sels.clear()

            try:
                sels.add(ent)
                ids = self.app.executeTextCommand(u'Selections.List').rstrip('\n\r')
                sels.clear()
            except:
                ids = ''

            return ids

        # 指定IDのtergetKeyのentityId取得
        def getEntityId(
            id: int,
            tergetKey :str
            ) -> int:

            try:
                # get prop
                txt = neu_server.get_entity_properties(id)
                if len(txt) < 1: return -1

                # to json
                prop =  json.loads(json.dumps(txt))

                # terget Id
                tergetId = prop[tergetKey]["entityId"]
                if tergetId < 1 :
                    tergetId = -1

                return int(tergetId)

            except:
                return -1

        # root or Occ からcompId取得
        def getTargetComponentId(
            root_occ :adsk.core.Base
            ) -> int:

            # root_occ paths
            root_occPathStr = getSelectPathsId(root_occ)
            if len(root_occPathStr) < 1: return -1

            # root_occ id
            root_occId = root_occPathStr.split(':')[-1]

            # comp id
            compId :int = getEntityId(int(root_occId), 'rTargetComponent')
            if compId < 0: return -1

            return compId

        # Childrenの最後の要素のentityId取得
        def getLastChildId(
                parentId :int
            ) -> int:

            try:
                count :int = neu_modeling.get_child_count(parentId) 
                if count < 1: return -1

                child = neu_modeling.get_child(parentId, count -1)
                return child['entityId']
            except :
                return -1

        # BodeisGroup作成 - 事前にBodeisが選択されている必要あり
        # return SurfaceGroup Id
        def createSurfaceGroup(
            root_occ :adsk.core.Base
            ) -> int:

            # exec FusionCreateSurfaceGroupCommand
            self.app.executeTextCommand(u'Commands.Start FusionCreateSurfaceGroupCommand')

            # comp id
            compId :int = getTargetComponentId(root_occ)
            if compId < 0: return -1

            # SurfaceGroups id
            surfGroupsId :int = getEntityId(compId, 'rSurfaceGroups')
            if surfGroupsId < 0: return -1

            # SurfaceGroups count
            targetGroupId = getLastChildId(surfGroupsId)

            return targetGroupId

        def getPaths(
            root_occ :adsk.core.Base,
            tergetKey :str,
            childId :int = -1
            ) -> str:

            # root_occ paths
            root_occPathStr = getSelectPathsId(root_occ)
            if len(root_occPathStr) < 1: return ""

            # root_occ id
            root_occId = root_occPathStr.split(':')[-1]

            # comp id
            compId :int = getEntityId(int(root_occId), 'rTargetComponent')

            # root check
            if root_occ.isRoot():
                if compId < 0: return ""
                root_occPathStr += ':{}'.format(compId)

            # tergetKey id
            tergetId :int = getEntityId(compId, tergetKey)

            # <paths>
            if childId < 0:
                tergetPath = root_occPathStr + ':{}'.format(tergetId)
            else:
                tergetPath = root_occPathStr + ':{}:{}'.format(tergetId, childId)
            
            return tergetPath

        # SurfaceGroupを作成するbodiesを選択
        def selectKey(
            root_occ :adsk.core.Base,
            tergetKey :str,
            childId :int = -1
            ) -> bool:

            # get <paths>
            tergetPaths = getPaths(root_occ, tergetKey, childId)

            # select root_occ bodies
            self.app.executeTextCommand(u'Selections.Add {}'.format(tergetPaths))

            # sels count check
            if self.ui.activeSelections.count < 1:
                return False
            
            return True

        # リスト内のボディから一つの親取得
        def getSingleParent(
            bodiesList
            ) -> adsk.core.Base:

            # ddd = hasattr(bodiesList, 'count')##############
            # if hasattr(bodiesList, 'count'):
            #     if bodiesList.count < 1:
            #         return None
            # elif len(bodiesList) < 1:
            #     return None
            if len(bodiesList) < 1:
                return None

            tokens = []
            parent :adsk.core.Base.cast(None)
            for body in bodiesList:
                occ = body.assemblyContext

                if occ:
                    parent = occ
                    token = occ.entityToken
                else:
                    parent = body.getParent()
                    token = parent.entityToken

                tokens.append(token)
            
            if len(set(tokens)) < 1:
                return None
            
            return parent

        # pathsで選択
        def selectPaths(
            paths :list
            ):

            for path in paths:
                self.app.executeTextCommand(u'Selections.Add {}'.format(path))

        # ------------------

        # get root or occ
        parent = getSingleParent(bodiesList)
        if not parent:
            return False

        # select target bodies
        res = selectKey(parent, 'rBodies')
        if not res:
            return False

        # Create SurfaceGroup
        surfGroupId = createSurfaceGroup(parent)
        if surfGroupId < 0:
            return False

        # Rename SurfaceGroup
        if len(groupName) > 0:
            cmd = u'PInterfaces.Rename {} {}'.format(surfGroupId, groupName)
            self.app.executeTextCommand(cmd)

        # select SurfaceGroup bodylist
        ids = [getPaths(parent, 'rSurfaceGroups', surfGroupId)]
        ids.extend([getSelectPathsId(body) for body in bodiesList])
        selectPaths(ids)

        # exec FusionMoveToSurfaceGroupCommand
        self.app.executeTextCommand(u'Commands.Start FusionMoveToSurfaceGroupCommand')
        self.app.executeTextCommand(u'NuCommands.CommitCmd')

        return True