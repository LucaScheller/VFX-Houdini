import json
from PySide2 import QtWidgets, QtCore, QtGui

import hou
import layout.assetlayoutinterface as ALI
from layout import panel
from vfxHoudini.api.constants import EnvVar, MimeData

class AssetLibraryDropField(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super(AssetLibraryDropField, self).__init__(*args, **kwargs)
        # UI
        self.setAcceptDrops(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setFlat(True)
        self.setStyleSheet('''
            QPushButton {
                border: %spx dashed rgba(255,255,255,200);
                border-radius: %spx;
                background: rgba(0,0,0,0);
            }
            ''' % (int(hou.ui.scaledSize(3)),
                   int(hou.ui.scaledSize(7))))
        # Data source
        self.panel = None

    def parseMimeData(self, mime_data):
        """Retrieve asset libray data from the given mime_data."""
        # Parse from text
        text_data = []
        if mime_data.hasText():
            try:
                text_data = json.loads(mime_data.text())
                text_data = text_data.get('vfxHoudini', {}).get({"assetLibrary", []})
            except:
                text_data = []
        # Parse from URLs
        url_data = []
        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.startswith(MimeData.url_scheme_vfxHoudini):
                    data = url.replace(MimeData.url_scheme_vfxHoudini + ":", "")
                    try:
                        data = json.loads(data.text())
                        data = data.get({"assetLibrary", []})
                    except:
                        data = []
                    url_data.extend(data)

        # TODO Remove in production
        url_data = [
            {
                "id": "id_9",
                "label": "Item Label 9",
            }, 
            {
                "id": "id_10",
                "label": "Item Label 10",
                "file_path": "/some/path/10.usd",
                "thumbnail_file_path": "/some/path/10.png",
                "creation_date": 0,
                "modification_date": 0,
                "meta_data": {"keyA": "valueA", "keyB": "valueB"},
                "tags": ["Tag 0", f"Item Tag 10"],
                "color": "yellow",
                "star": 0
            }
        ]

        return text_data + url_data

    def dragEnterEvent(self, event):
        """The drop event enter handler.
        Args:
            event(QEvent): The event.
        """
        mime_data = event.mimeData()
        data = self.parseMimeData(mime_data)
        if data:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """The drop event handler.
        Args:
            event(QEvent): The event.
        """
        mime_data = event.mimeData()
        data = self.parseMimeData(mime_data)
        if data:
            data_source = hou.ui.sharedAssetGalleryDataSource('layout')
            # Update data source
            item_ids = data_source.itemIds()
            for item_data in data:
                if item_data["id"] not in item_ids:
                    data_source.addItem("", blind_data=json.dumps(item_data).encode('ascii'))
            # Update working set
            node = ALI.instance()._current_node
            user_info_parm = node.parm("userinfo")
            user_info = user_info_parm.unexpandedString()
            user_info = json.loads(user_info)
            working_set = json.loads(user_info.get("working_set", '{"items": []}'))
            working_set_items = {i["id"]: i for i in working_set["items"]}
            for item_data in data:
                # Hard overwrite dict
                working_set_items[item_data["id"]] = {"id": item_data["id"],
                                                      "isChecked": True}
            working_set_items = [v for k, v in working_set_items.items()]
            working_set["items"] = working_set_items
            user_info["working_set"] = json.dumps(working_set)
            user_info_parm.set(json.dumps(user_info))
            
            # UI Refresh
            # This only works for pre-existing items.
            hou.ui.reloadSharedAssetGalleryDataSource('layout')
            self.panel.onActivate({})

            event.accept()
        else:
            event.ignore()


class LopLayoutPanel(panel.LopLayoutPanel):
    def __init__(self, parent=None):
        super(LopLayoutPanel, self).__init__(parent)

        brush_panel_layout = self._brush_panel.layout()
        drop_button = AssetLibraryDropField("Drop Assets Here!", self)
        drop_button.setMinimumHeight(hou.ui.scaledSize(100))
        drop_button.panel = self._brush_panel._working_set_panel
        brush_panel_layout.addWidget(drop_button)

        # Activate library
        asset_library_identifier = "{}.env".format(EnvVar.asset_library_datasource)
        asset_library_data_source = hou.AssetGalleryDataSource(asset_library_identifier, "")
        hou.ui.setSharedAssetGalleryDataSource(asset_library_data_source, gallery_name='layout')

        