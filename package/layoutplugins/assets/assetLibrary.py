import hou
import layout.assetlayoutinterface as ali
import layout.utils as lu
import loputils
import json
import toolutils
from typing import *
from husd import assetutils

from vfxHoudini.api.constants import EnvVar, DataSourceTypes

def ALI():
    return ali.instance()


def _notImplementedFn(fn_name: str):
    def fn(*args, **kwargs):
        raise NotImplementedError(f"'{fn_name}' is not properly defined for this asset.")
    return fn


class AssetLibrayUSDAsset(object):
    generator = _notImplementedFn("generator")
    update_handler = _notImplementedFn("update_handler")
    reload_handler = _notImplementedFn("reload_handler")
    bb_handler = _notImplementedFn("bb_handler")

    def __init__(self, ident : str, datasource : hou.AssetGalleryDataSource):
        self._node = None
        self._container = None
        self._ident = ident
        if datasource is None:
            raise Exception("Datasource cannot be None")
        self._datasource = datasource

    def onGenerate(self, kwargs: Dict[Any, Any]) -> None:
        """
        Callback that is triggered when the layout state might need to generate a new asset.
        The generate functions should take care of not generating duplicate nodes in the same container
        as there is no convention for what the ID is for all asset types.
        """
        self._node = kwargs['prototype_node']
        self._container = kwargs['container']
        ident = kwargs['id']
        self._file_path, self._asset_name, self._primpath = ali.getFileNamePath(ident)
        end_node = self._container.node("./END_ASSETS")
        assert(end_node is not None)
        prev_item = None
        connectors = end_node.inputConnectors()
        if connectors:
            connections = connectors[0]
            if connections:
                prev_item = connections[0]
        asset_info = assetutils.getInfoFromAssetDataSource(self._ident, self._datasource)
        self.generator(
            self._container,
            asset_info,
            self._primpath,
            prev_item,
            end_node)

    def validate(self, ident:str) -> None:
        file_path = self._datasource.filePath(ident)
        file_path = hou.text.collapseCommonVars(file_path, ali.COMMON_VARS)
        asset_name = self._datasource.label(ident)
        old_file_path = self._file_path
        old_asset_name = self._asset_name
        old_primpath = self._primpath

        needs_update = file_path != self._file_path or asset_name != self._asset_name

        if asset_name != self._asset_name:
            self._primpath = hou.lop.makeValidPrimPath('/' + asset_name)
            self._asset_name = asset_name

        if self._file_path != file_path:
            self._file_path = file_path

        if needs_update:
            self.update_handler(self._container, ident, self._file_path, self._primpath)
            update_dict = {
                'old_file_path': old_file_path,
                'file_path': self._file_path,
                'old_asset_name': old_asset_name,
                'asset_name': self._asset_name,
                'old_primpath': old_primpath,
                'primpath': self._primpath
            }
            ALI().emitCustomEvent(ALI().eventType.AssetUpdated, update_dict)

    def getBoundingBox(self) -> hou.BoundingBox:
        return self.bb_handler(self._node, self._primpath)

    def getPrototypeDescriptor(self) -> str:
        return self._primpath

    def reload(self, ident: str) -> None:
        self.reload_handler(self._container, ident)


def _createNode(container: hou.Node, node_name: str, node_type: str) -> hou.Node:
    """
    Returns the node with name node_name.
    """
    return container.createNode(node_type, node_name=node_name, force_valid_node_name=True)


def basicBBHandler(prototype_node: hou.Node, primpath: str) -> hou.BoundingBox:
    prims = loputils.globPrims(prototype_node, primpath)
    if len(prims) == 0:
        return hou.BoundingBox()
    prim = prims[0]
    bbox = loputils.computePrimLocalBounds([prim])
    if bbox is None:
        return hou.BoundingBox()
    xform = loputils.getPrimXform(prototype_node, primpath)
    range3d = bbox.GetRange()
    min_pt = hou.Vector3(*range3d.GetMin())
    max_pt = hou.Vector3(*range3d.GetMax())
    return hou.BoundingBox(min_pt.x(), min_pt.y(), min_pt.z(), max_pt.x(), max_pt.y(), max_pt.z()) * xform


def placementAssetLibraryHandler(
        container: hou.Node,
        asset_info : dict[str, Any],
        primpath : str,
        prev_item: Optional[hou.NetworkMovableItem],
        next_node: Optional[hou.Node],
        force_gen: bool = False) -> Optional[hou.Node]:
    """ Generate a set of nodes that import an asset from a file.

    file_path : str describing the file path to the asset.
    name: str name for the node, might be modified to be a valid variable name.
    primpath: str describing the primitive path for the referenced asset.
    data: bytestring encoding a dictionary holding the primpath for the specific
          primitive being referenced from the file.
    """
    name = asset_info['label']
    data = asset_info['data']
    data_dict = json.loads(data.decode()) if data else {}
    node_name = hou.text.variableName(name)

    # Load item blind data
    item_data_blind_data = data_dict
    item_prim_path = item_data_blind_data["prim_path"]
    item_layer_identifier = item_data_blind_data["layer_identifier"]

    # Create an asset reference node
    new_node = container.node(node_name)
    if not force_gen and new_node is not None:
        # If the node already exists just return that node.
        return new_node

    # Otherwise generate the node.
    new_node = _createNode(container, node_name, "assetreference")
    new_node.parm("filepath").set(item_layer_identifier)
    new_node.parm("instanceable").set(1)
    # Warn on missing files instead of error.
    new_node.parm("handlemissingfiles").set("warn")
    new_node.parm("primpath").set(primpath) # Has to derive from the label

    # Set variant selections.
    variants_dict = data_dict.get('variants', {})
    new_node.parm("num_variants").set(len(variants_dict))
    for (i, (variant_set_name, variant_name)) in enumerate(variants_dict.items()):
        new_node.parm("variantset{}".format(i+1)).set(variant_set_name)
        new_node.parm("variantname{}".format(i+1)).set(variant_name)

    # Update node position
    if prev_item is not None and next_node is None:
        new_node.setInput(0, prev_item)
    if next_node is not None:
        toolutils.insertNodeAbove(next_node, new_node)
    new_node.moveToGoodPosition()

    return new_node


def updateAssetLibraryAssetHandler(container: hou.Node,
        ident: str,
        file_path: str,
        primpath: str) -> None:
    node = container.node(hou.text.variableName(ident))
    if node is None:
        raise ValueError("No node found for identifier: " + ident)
    # Notes: SideFX maps ident to be the item label here.
    # This method is not tested, not sure where this actually gets called.
    data_source = hou.ui.sharedAssetGalleryDataSource('layout')
    blind_data = None
    for item_id in data_source.itemIds():
        if item_id == data_source.label(item_id):
            blind_data = json.loads(data_source.blindData(item_id))
            break
    if not blind_data:
        return
    data_source = hou.ui.sharedAssetGalleryDataSource('layout')
    node.parm("filepath").set(blind_data["layer_identifier"])
    node.parm("reload").pressButton()


def reloadAssetLibraryHandler(container: hou.Node, ident: str) -> None:
    # Notes: SideFX maps ident to be the item id here.
    data_source = hou.ui.sharedAssetGalleryDataSource('layout')
    item_label = data_source.label(ident)
    ref_node = container.node(hou.text.variableName(item_label))
    if ref_node is None:
        raise ValueError("No node found for identifier: {} in {}".format(ident, container))
    ref_node.parm("reload").pressButton()


def _buildAssetClass(
    gen : lu.AssetGeneratorSig,
    updater : Callable[[hou.Node, str, str, str], None],
    bbox : Callable[[hou.Node, str], hou.BoundingBox],
    reloader : Callable[[hou.Node, str], None]):
    class C(AssetLibrayUSDAsset):
        generator = staticmethod(gen)
        update_handler = staticmethod(updater)
        bb_handler = staticmethod(bbox)
        reload_handler = staticmethod(reloader)
    return C


def registerAssets():
    # Generate classes with handlers as class members
    AssetLibraryAsset = _buildAssetClass(placementAssetLibraryHandler, updateAssetLibraryAssetHandler, basicBBHandler, reloadAssetLibraryHandler)

    ali.registerAsset(DataSourceTypes.asset_library_source, AssetLibraryAsset)

