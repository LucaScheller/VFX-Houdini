import datetime
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import hou
import husd


class ItemColor:
    blue = "blue"
    green = "green"
    purple = "purple"
    yellow = "yellow"
    teal = "teal"
    red = "red"


@dataclass
class Item:
    id: str
    # Hierarchy
    parent: str = ""
    children: dict = field(default_factory = lambda: ({}))
    # Data
    label: str = ""
    file_path: str = ""
    thumbnail_file_path: str = ""
    thumbnail_file_content: bytes = b"" 
    creation_date: int = 0
    modification_date: int = 0
    meta_data: dict = field(default_factory = lambda: ({}))
    blind_data: str = ""
    # UI
    tags: list[str] = field(default_factory = lambda: ([]))
    color: str = ""
    star: bool = False


class Model(object):
    def __init__(self, identifier: str) -> None:
        """Initialize the model.
        Args:
            identifier(str): The identifier.
        """
        # Static
        self.identifier = identifier

        # Items
        self.items = {}
        self.items_updated = set()
        self.items_deleted = {}

        # UI
        self.tags = []

    def get_tags(self) -> tuple[str]:
        """Get all tags.
        Returns
            list[str]: The tags.
        """
        return tuple(self.tags)

    def add_tag(self, tag:str) -> bool:
        """Create a tag, return True if 
        the tag did not already exist and was created.

        Args:
            tag(str): The tag name.
        Returns:
            str: The success state.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            return True
        return False

    def delete_tag(self, tag:str, delete_if_assigned: bool) -> bool:
        """Delete a tag, return True if 
        the tag did not already exist and was created.

        Args:
            tag(str): The tag name.
        Returns:
            str: The success state.
        """
        tag_assigned = False
        for item in self.items.values():
            if tag in item.tags:
                tag_assigned = True
                break
        if not delete_if_assigned and tag_assigned:
            return False
        
        if tag_assigned:
            for item in self.items.values():
                if tag in item.tags:
                    item.tags.remove(item)
            
        tag_exists = tag in self.tags
        if tag_exists:
            self.tags.remove(tag)
        return tag_assigned or tag_exists

    def get_item_ids(self) -> tuple[str]:
        """Get the ids of all items.

        Returns:
            tuple[str]: The item ids.
        """
        return tuple(self.items.keys())
    
    def get_item_updated_ids(self) -> tuple[str]:
        """Get the ids of all updated items.
        This clears the update queue.

        Returns:
            tuple[str]: The item ids.
        """
        ids = tuple(self.items_updated)
        self.items_updated.clear()
        return ids

    def set_item_mark_deleted(self, item_id: str) -> bool:
        """Marks the item to be deleted.
        Args:
            item_id(str): The item id to mark as deleted.
        Returns:
            str: The success state.
        """
        item = self.items.pop(item_id, None)
        if item:
            self.items_deleted[item_id] = item
            return True
        return False

    def set_item_mark_undeleted(self, item_id: str) -> bool:
        """Un-mark the item to be deleted.
        Args:
            item_id(str): The item id to restore.
        Returns:
            str: The success state.
        """
        item = self.items_deleted.pop(item_id, None)
        if item:
            self.items[item_id] = item
            return True
        return False

    def add_item(self, item: Item):
        """Add an item to the model.
        Args:
            item(Item): The item to add.
        """
        self.items[item.id] = item
        for tag in item.tags:
            self.add_tag(tag)

    def get_data(self, item_id: str, role: Any):
        """Get data with the given role from the item.
        Args:
            item_id(str): The item id.
            role(str): The data role.
        Returns:
            Any: The data.
        """
        item = self.items.get(item_id)
        data = getattr(item, role, None)
        if role == 'thumbnail_file_content' and not data:
            thumbnail_file_path = getattr(item, 'thumbnail_file_path', None)
            data = b''
            if thumbnail_file_path and os.path.isfile(thumbnail_file_path):
                with open(thumbnail_file_path, "r") as thumbnail_file:
                    data = thumbnail_file.read()
                setattr(item, 'thumbnail_file_content', data)

        return data

    def set_data(self, item_id: str, role: str, value: Any) -> bool:
        """Set data with the given role on the given item.
        Args:
            item_id(str): The item id.
            role(str): The data role.
            value(Any): The data.
        Returns:
            bool: The success state.
        """
        item = self.items.get(item_id)
        if not item:
            return False
        data = getattr(item, role, None)
        if data == value:
            return False
        else:
            self.items_updated.add(item_id)
            setattr(item, role, value)
            return True

    def load(self, identifier: str=None):
        """Load the model from the given identifier.
        Args:
            identifier(str): The model id.
        """
        if not identifier:
            identifier = self.identifier
        if identifier == "__mock__.env":
            populate_mock_data(self)
        else:
            env_name = identifier.replace(".env", "")
            data = hou.getenv(env_name, "")
            if not data:
                return
            data = json.loads(data).replace('|||', '"')
            self.identifier = data["identifier"]
            self.tags = data["tags"]
            for item_id, item_data in data["items"].items():
                self.items[item_id] = Item(item_id, **item_data)

    def save(self, identifier: str=None):
        """Save the model to its identifier."""
        if not identifier:
            identifier = self.identifier
        env_name = identifier.replace(".env", "")
        data = {"identifier": self.identifier, "items": {}, "tags": self.tags}
        item: Item
        for item in self.items.values():
            item_data = item.__dict__
            item_data = {k:v for k,v in item_data.items()}
            item_data.pop('thumbnail_file_content')
            data["items"][item.id] = item_data
        data = json.dumps(data).replace('"', '|||')
        hou.hscript('setenv {env_name}="{data}"'.format(env_name=env_name,
                                                        data=data))


def populate_mock_data(model: Model):
    self = model
    for idx in range(5):
        self.add_tag(f"Tag {idx}")
    item_colors = [ItemColor.red, ItemColor.green, ItemColor.blue]
    for idx in range(10):
        item_creation_date = time.mktime(datetime.datetime.now().timetuple())
        item = Item(
            f"id_{idx}",
            label=f"Item Label {idx}",
            file_path=f"/some/path/{idx}.usd",
            thumbnail_file_path=f"/some/path/{idx}.png",
            creation_date=item_creation_date,
            modification_date=item_creation_date,
            meta_data={"keyA": "valueA", "keyB": "valueB"},
            tags=["Tag 0", f"Item Tag {idx}"],
            color=item_colors[idx % 3],
            star=idx % 3 == 0
        )
        self.add_item(item)


class AssetLibrary(husd.datasource.DataSource):
    identifier = "AssetLibrary"

    def __init__(self, source_identifier, args=None):
        self.source_identifier = source_identifier
        self.source_args = args # Not implemented for now.

        # Storage
        self.model = Model(source_identifier)

        # Init
        self.model.load()

    def isValid(self) -> bool:
        """The data source state.
        Returns:
            bool: Data source is valid.
        """
        return True

    def isReadOnly(self) -> bool:
        """The read only state.
        Returns:
            bool: Data source read only state.
        """
        return False

    @staticmethod
    def canHandle(source_identifier):
        """Check if this model can handle the specified
        model identifier.
        Args:
            identifier(str): The model identifier.
        Returns:
            bool: The state.
        """
        return source_identifier.endswith(".env")
    
    def sourceIdentifier(self) -> str:
        """The source identifier string used to create this data source object.
        Returns:
            str: Data source identifier.
        """
        return self.source_identifier

    def sourceArgs(self) -> str:
        """The args string used to create this data source object.
        Returns:
            str: Data source args string.
        """
        return self.source_args

    def infoHtml(self) -> str:
        """Return a string in HTML format that will be
        displayed at the top of the asset gallery window.
        Provides custom information about the data source.

        Returns:
            str: A html parse-able string.
        """
        return ""

    def saveAs(self, source_identifier) -> bool:
        """Create a copy of the data source, if supported.
        This will also create copies of the item files, if
        the ownsFile flag is True.
        Args:
            source_identifier(str): The save source identifier.
        Returns:
            str: The success state.
        """
        return self.model.save(source_identifier)

    def startTransaction(self):
        """For writable data sources, this method is used to group
        multiple calls to edit the data source.
        """
        pass

    def endTransaction(self, commit=True):
        """This method is always called after a call to startTransaction,
        and indicates that the group of data source edits has been completed.
        Args:
            commit (bool): If True, make the changes persistent.
        """
        if commit:
            self.model.save()

    def itemIds(self) -> tuple[str]:
        """A unique identifier for each asset available in the data source.
        Returns:
            list[str]: The item identifiers.
        """
        return self.model.get_item_ids()

    def updatedItemIds(self) -> tuple[str]:
        """Return a unique identifier for any asset that has changed since
        the last call to this method. This method is polled regularly by the
        asset gallery to handle cases where the underlying data source may change,
        or where data my not have been available when it was queried, but the item’s
        data has since become available.

        Returns:
            tuple[str]: Item identifiers of items that have data changes.
        """
        return self.model.get_item_updated_ids()

    def parentId(self, item_id: str) -> str:
        """The unique identifier for this item’s parent item.
        Args:
            item_id(str): The id of the item whose parent to query.
        Returns:
            str: The parent item identifier.
        """
        return self.model.get_data(item_id, "parent")

    def setParentId(self, item_id: str, parent_item_id: str) -> bool:
        """Set the unique identifier for this item’s parent item.
        Args:
            item_id(str): The item identifier.
            parent_item_id(str): The parent item identifier.
        Returns:
            bool: The success state.
        """
        return self.model.set_data(item_id, "parent", parent_item_id)

    def childItemIds(self, item_id: str) -> tuple[str]:
        """A list of unique identifiers for all assets that
        have this item set as its parent.
        Args:
            item_id(str): The parent item id.
        Returns:
            tuple[str]: The child item ids.
        """
        return self.model.get_data(item_id, "children")

    def prepareItemForUse(self, item_id: str) -> str:
        """Make sure that the item is ready to be used.
        For data sources that point to remote databases,
        this method may involve downloading the item’s data.

        Args:
            item_id(str): The item id.
        Returns:
            str: Empty string if item is ready, otherwise error.
        """
        return ""

    def markItemsForDeletion(self, item_ids: tuple[str]) -> bool:
        """Marks one or more items to be deleted.
        Args:
            item_ids(tuple[str]): The item ids to mark as deleted.
        Returns:
            str: The success state.
        """
        states = []
        for item_id in item_ids:
            states.append(
                self.model.set_item_mark_deleted(item_id)
            )
        return all(states)

    def unmarkItemsForDeletion(self, item_ids: tuple[str]) -> bool:
        """Remove the indicator in the data source that the
        supplied items should be deleted.
        Args:
            item_ids(tuple[str]): The item ids to restore.
        Returns:
            str: The success state.
        """
        states = []
        for item_id in item_ids:
            states.append(
                self.model.set_item_mark_undeleted(item_id)
            )
        return all(states)
    
    def addItem(
        self,
        label: str,
        file_path: str = None,
        thumbnail: str = b"",
        type_name: str = "asset",
        blind_data: str = b"",
        creation_date: int = 0,
    ) -> str:
        """Add an item to the data source.
        Args:
            label(str): The label.
            file_path(str): The file path.
            thumbnail(str): The thumbnail file path.
            type_name(str): The thumbnail file path.
            blind_data(str): The blind data.
            creation_data(int): The creation date.
        Returns:
            str: The item identifier.
        """
        item = Item(
            id=file_path,
            label=label,
            file_path=file_path,
            thumbnail_file_content=thumbnail,
            blind_data=blind_data,
            creation_date=creation_date
        )
        self.model.add_item(item)

    def filePath(self, item_id: str) -> str:
        """Return a string that can be used to access
        the raw data associated with this item.

        Args:
            item_id(str): The item id.
        Returns:
            str: The file path.
        """
        return self.model.get_data(item_id, "file_path")

    def setFilePath(self, item_id: str, file_path: str) -> bool:
        """Set the value of the filePath for this item.
        Return True if this call resulted in a change to this value.

        Args:
            item_id(str): The item id.
            file_path(str): The file path.
        Returns:
            str: The success state.
        """
        return self.model.set_data(item_id, "file_path")
    
    def generateItemFilePath(self, item_id: str, file_ext: str) -> str:
        """Return a unique file path with an extension provided in file_ext.
        Args:
            item_id(str): The item id.
            file_ext(str): The file extension.
        Returns:
            str: The file path.
        """
        return ""

    def createTag(self, tag: str) -> bool:
        """Create a tag in the data source, but do not assign it to any items.
        Return True if the tag did not already exist and was created.

        Args:
            tag(str): The tag name.
        Returns:
            str: The success state.
        """
        return self.model.add_tag(tag)

    def deleteTag(self, tag: str, delete_if_assigned: bool) -> bool:
        """Delete a tag from the data source.
        Return True if the tag existed and was removed.
        If delete_if_assigned is False, and the tag is assigned
        to any item, this function will do nothing and return False.
        If delete_if_assigned is True and the tag is assigned
        to any items, the tag is first unassigned from those items,
        then the tag is deleted.

        Args:
            tag(str): The tag name.
            delete_if_assigned(bool): Delete tag, even if it is assigned.
        Returns:
            str: The success state.
        """
        return self.model.delete_tag(tag, delete_if_assigned)

    def addTag(self, item_id, tag) -> bool:
        """Adds a tag to a specific item.
        Creates the tag if it does not already exist.
        Return True if the tag was added to the item.
        Return False if the tag was already assigned to the item.

        Args:
            item_id(str): The item id.
            tag(str): The tag name.
        Returns:
            str: The success state.
        """
        tags = self.model.get_data(item_id, "tags")
        if tag not in tags:
            self.model.set_data(item_id, "tags", tags + [tag])
            return True
        else:
            return False

    def removeTag(self, item_id, tag) -> bool:
        """Removes a tag from a specific item.
        Return True if the tag was removed from the item.
        Return False if the tag was not assigned to the item.

        Args:
            item_id(str): The item id.
            tag(str): The tag name.
        Returns:
            str: The success state.
        """
        tags = self.model.get_data(item_id, "tags")
        if tag in tags:
            tags.remove(tag)
            self.model.set_data(item_id, "tags", tags) # Technically not necessary.
            return True
        else:
            return False

    def tags(self, item_id: str) -> tuple[str]:
        """Return a tuple of user defined tag
        strings that have been assigned to this item.

        Args:
            item_id(str): The item id.
        Returns:
            tuple[str]: The tags.
        """
        item_tags = []
        if item_id:
            item_tags = self.model.get_data(item_id, "tags")
        return tuple(sorted(list(item_tags) + list(self.model.get_tags())))

    def status(self, item_id) -> str:
        """Return a string describing the current status of this item.
        Args:
            item_id(str): The item id.
        Returns:
            str: The status.
        """
        return ""

    def typeName(self, item_id) -> str:
        """Return the type of asset identified by the id.
        This will either be snapshot (for a snapshot in a
        snapshot gallery) or asset (for an asset in an asset gallery).
        Args:
            item_id(str): The item id.
        Returns:
            str: The type name.
        """
        return "asset"

    def sourceTypeName(self, item_id: str | None = None) -> str:
        """Return the data source type of the asset identified by the id.
        Args:
            item_id(str|None): The item id.
        Returns:
            str: The source type name.
        """
        return self.identifier

    def label(self, item_id: str) -> str:
        """Return the user-facing string that identifies and describes the item.
        Args:
            item_id(str): The item id.
        Returns:
            str: The label.
        """
        return self.model.get_data(item_id, "label")

    def setLabel(self, item_id: str, label: str) -> bool:
        """Return the user-facing string that identifies and describes the item.
        Args:
            item_id(str): The item id.
            label(str): The label to set.
        Returns:
            bool: The value changed state.
        """
        return self.model.set_data(item_id, "label", label)

    def thumbnail(self, item_id: str) -> bytes:
        """Return the raw data for a thumbnail image that represents the item.
        Args:
            item_id(str): The item id.
        Returns:
            str: The thumbnail file path.
        """
        return self.model.get_data(item_id, "thumbnail_file_content")

    def setThumbnail(self, item_id: str, thumbnail: str) -> bool:
        """Return the raw data for a thumbnail image that represents the item.
        Args:
            item_id(str): The item id.
            thumbnail(str): The thumbnail file path.
        Returns:
            bool: The value changed state.
        """
        return self.model.set_data(item_id, "thumbnail_file_path", thumbnail)

    def ownsFile(self, item_id: str) -> bool:
        """Return True if the filePath for this item is a file on disk
        that should be deleted if the item is deleted.

        Args:
            item_id(str): The item id.
        Returns:
            bool: The ownership state.
        """
        return False

    def setOwnsFile(self, item_id: str, owns_file: bool) -> bool:
        """Return True if the filePath for this item is a file on disk
        that should be deleted if the item is deleted.
        Args:
            item_id(str): The item id.
            owns_file(bool): The ownership state.
        Returns:
            bool: The value changed state.
        """
        return False

    def creationDate(self, item_id: str) -> int:
        """Return a long integer representing the unix timestamp
        at which the item was created.

        Args:
            item_id(str): The item id.
        Returns:
            str: The creation time.
        """
        return self.model.get_data(item_id, "creation_date")

    def modificationDate(self, item_id: str) -> int:
        """Return a long integer representing the unix timestamp
        at which the item was last modified.

        Args:
            item_id(str): The item id.
        Returns:
            str: The modification time.
        """
        return self.model.get_data(item_id, "modification_date")

    def setModificationDate(self, item_id: str, timestamp: str) -> bool:
        """Set the value of the modificationDate for this item.
        Return True if this call resulted in a change to this value.

        Args:
            item_id(str): The item id.
            timestamp(int): The modification time.
        Returns:
            bool: The value changed state.
        """
        return self.model.set_data(item_id, "modification_date", timestamp)

    def isStarred(self, item_id: str) -> bool:
        """Return True if this item has been marked as a “favorite” by the user.

        Args:
            item_id(str): The item id.
        Returns:
            bool: The state.
        """
        return self.model.get_data(item_id, "star")

    def setIsStarred(self, item_id: str, isstarred: bool) -> bool:
        """Set the value of the isStarred flag for this item.
        Return True if this call resulted in a change to this value.

         Args:
             item_id(str): The item id.
             isStarred(bool): The state.
         Returns:
             bool: The value changed state.
        """
        return self.model.set_data(item_id, "star", isstarred)

    def colorTag(self, item_id) -> str:
        """Return a string indicating a special color tag value that has been assigned by the user.
        These color strings are displayed as colored bars in the gallery browser UI.
        Supported values are blue, green, purple, yellow, teal, and red.

        Args:
            item_id(str): The item id.
        Returns:
            str: The color.
        """
        return self.model.get_data(item_id, "color")

    def setColorTag(self, item_id: str, color_tag: str) -> bool:
        """Set the value of the colorTag for this item.
        Return True if this call resulted in a change to this value.

        Args:
            item_id(str): The item id.
            color_tag(str): The color tag.
        Returns:
            bool: The value changed state.
        """
        return self.model.set_data(item_id, "color", color_tag)

    def metadata(self, item_id: str) -> dict:
        """Return a dictionary of metadata that has been associated
        with this item. This metadata may be user created, or
        automatically (such as by a renderer used to create an image
        in the snapshot gallery).

        Args:
            item_id(str): The item id.
        Returns:
            dict: The meta_data dict.
        """
        return self.model.get_data(item_id, "meta_data")

    def setMetadata(self, item_id: str, metadata: dict) -> bool:
        """Set the value of the metadata dictionary for
        this item. Return True if this call resulted in
        a change to this value.
        Args:
            item_id(str): The item id.
            metadata(str): The metadata dict.
        Returns:
            bool: The value changed state.
        """
        return self.model.set_data(item_id, "meta_data", metadata)

    def blindData(self, item_id: str) -> bytes:
        """Return a block of data source implementation specific
        binary data associated with the item.
        Returns:
            bytes: The binary data.
        """
        return self.model.get_data(item_id, "blind_data")

    def setBlindData(self, item_id: str, data: bytes) -> bool:
        """Set the value of the blindData for this item.
        Args:
            item_id(str): The item id.
            data(bytes): The binary data.
        Returns:
            bool: The value changed state.
        """
        return self.model.set_data(item_id, "blind_data", data)


def registerDataSources(manager):
    manager.registerDataSource("Asset Library", AssetLibrary)
