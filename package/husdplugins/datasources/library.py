import hou
import husd
import json
from dataclasses import dataclass

from pxr import Sdf, Usd, UsdShade


@dataclass
class AssetItem:
    color = ""
    starred = False

@dataclass
class AssetItemColor():
    blue = "blue"
    green = "green"
    purple = "purple"
    yellow = "yellow"
    teal = "teal"
    red = "red"
        

class AssetLibrary(husd.datasource.DataSource):
    def __init__(self, source_identifier, args=None):
        pass

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

    def sourceIdentifier(self) -> str:
        """The source identifier string used to create this data source object.
        Returns:
            str: Data source identifier.
        """

    def sourceArgs(self) -> str:
        """The args string used to create this data source object.
        Returns:
            str: Data source args string.
        """

    def infoHtml(self) -> str:
        """Return a string in HTML format that will be
        displayed at the top of the asset gallery window.
        Provides custom information about the data source.

        Returns:
            str: A html parse-able string.
        """

    def saveAs(self, source_identifier) -> bool:
        """Create a copy of the data source, if supported.
        This will also create copies of the item files, if
        the ownsFile flag is True.
        Args:
            source_identifier(str): The save source identifier.
        Returns:
            str: The success state.
        """

    def startTransaction(self):
        """For writable data sources, this method is used to group
        multiple calls to edit the data source.
        """

    def endTransaction(self, commit=True):
        """This method is always called after a call to startTransaction,
        and indicates that the group of data source edits has been completed.
        Args:
            commit (bool): If True, make the changes persistent.
        """

    def itemIds(self) -> tuple[str]:
        """A unique identifier for each asset available in the data source.
        Returns:
            list[str]: The item identifiers.
        """

    def updatedItemIds(self) -> tuple[str]:
        """Return a unique identifier for any asset that has changed since
        the last call to this method. This method is polled regularly by the
        asset gallery to handle cases where the underlying data source may change,
        or where data my not have been available when it was queried, but the item’s
        data has since become available.

        Returns:
            tuple[str]: Item identifiers of items that have data changes.
        """

    def parentId(self, item_id: str) -> str:
        """The unique identifier for this item’s parent item.
        Args:
            item_id(str): The id of the item whose parent to query.
        Returns:
            str: The parent item identifier.
        """

    def setParentId(self, item_id: str, parent_item_id: str) -> bool:
        """Set the unique identifier for this item’s parent item.
        Args:
            item_id(str): The item identifier.
            parent_item_id(str): The parent item identifier.
        Returns:
            bool: The success state.
        """

    def childItemIds(self, item_id: str) -> tuple[str]:
        """A list of unique identifiers for all assets that
        have this item set as its parent.
        Args:
            item_id(str): The parent item id.
        Returns:
            tuple[str]: The child item ids.
        """

    def prepareItemForUse(self, item_id: str) -> str:
        """Make sure that the item is ready to be used.
        For data sources that point to remote databases,
        this method may involve downloading the item’s data.

        Args:
            item_id(str): The item id.
        Returns:
            str: Empty string if item is ready, otherwise error.
        """

    def markItemsForDeletion(self, item_ids: tuple[str]) -> bool:
        """Marks one or more items to be deleted.
        Args:
            item_ids(tuple[str]): The item ids to mark as deleted.
        Returns:
            str: The success state.
        """

    def unmarkItemsForDeletion(self, item_ids: tuple[str]) -> bool:
        """Remove the indicator in the data source that the
        supplied items should be deleted.
        Args:
            item_ids(tuple[str]): The item ids to restore.
        Returns:
            str: The success state.
        """

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

    def filePath(self, item_id: str) -> str:
        """Return a string that can be used to access
        the raw data associated with this item.

        Args:
            item_id(str): The item id.
        Returns:
            str: The file path.
        """

    def setFilePath(self, item_id: str, file_path: str) -> bool:
        """Set the value of the filePath for this item.
        Return True if this call resulted in a change to this value.

        Args:
            item_id(str): The item id.
            file_path(str): The file path.
        Returns:
            str: The success state.
        """

    def generateItemFilePath(self, item_id: str, file_ext: str) -> str:
        """Return a unique file path with an extension provided in file_ext.
        Args:
            item_id(str): The item id.
            file_ext(str): The file extension.
        Returns:
            str: The file path.
        """

    def createTag(self, tag: str) -> bool:
        """Create a tag in the data source, but do not assign it to any items.
        Return True if the tag did not already exist and was created.

        Args:
            tag(str): The tag name.
        Returns:
            str: The success state.
        """

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

    def removeTag(self, item_id, tag) -> bool:
        """Removes a tag from a specific item.
        Return True if the tag was removed from the item.
        Return False if the tag was not assigned to the item.

        Args:
            item_id(str): The item id.
            tag(str): The tag name.
        Returns:
            str: Data source args string.
        """

    def status(self, item_id) -> str:
        """Return a string describing the current status of this item.
        Args:
            item_id(str): The item id.
        Returns:
            str: The status.
        """

    def typeName(self, item_id) -> str:
        """Return the type of asset identified by the id.
        This will either be snapshot (for a snapshot in a
        snapshot gallery) or asset (for an asset in an asset gallery).
        Args:
            item_id(str): The item id.
        Returns:
            str: The type name.
        """

    def sourceTypeName(self, item_id: str | None = None) -> str:
        """Return the data source type of the asset identified by the id.
        Args:
            item_id(str|None): The item id.
        Returns:
            str: The source type name.
        """

    def label(self, item_id: str) -> str:
        """Return the user-facing string that identifies and describes the item.
        Args:
            item_id(str): The item id.
        Returns:
            str: The label.
        """

    def setLabel(self, item_id: str, label: str) -> bool:
        """Return the user-facing string that identifies and describes the item.
        Args:
            item_id(str): The item id.
            label(str): The label to set.
        Returns:
            str: The label.
        """

    def thumbnail(self, item_id: str) -> bytes:
        """Return the raw data for a thumbnail image that represents the item.
        Args:
            item_id(str): The item id.
        Returns:
            str: The thumbnail file path.
        """

    def setThumbnail(self, item_id: str, thumbnail: str) -> bool:
        """Return the raw data for a thumbnail image that represents the item.
        Args:
            item_id(str): The item id.
            thumbnail(str): The thumbnail file path.
        Returns:
            bool: The value changed state.
        """

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

    def creationDate(self, item_id: str) -> int:
        """Return a long integer representing the unix timestamp
        at which the item was created.

        Args:
            item_id(str): The item id.
        Returns:
            str: The creation time.
        """

    def modificationDate(self, item_id: str) -> int:
        """Return a long integer representing the unix timestamp
        at which the item was last modified.

        Args:
            item_id(str): The item id.
        Returns:
            str: The modification time.
        """

    def setModificationDate(self, item_id: str, timestamp: str) -> bool:
        """Set the value of the modificationDate for this item.
        Return True if this call resulted in a change to this value.

        Args:
            item_id(str): The item id.
            timestamp(int): The modification time.
        Returns:
            bool: The value changed state.
        """

    def isStarred(self, item_id: str) -> bool:
        """Return True if this item has been marked as a “favorite” by the user.

        Args:
            item_id(str): The item id.
        Returns:
            bool: The state.
        """

    def setIsStarred(self, item_id: str, isstarred: bool) -> bool:
       """Set the value of the isStarred flag for this item.
       Return True if this call resulted in a change to this value.

        Args:
            item_id(str): The item id.
            isStarred(bool): The state.
        Returns:
            bool: The value changed state.
        """

    def colorTag(item_id) -> str:
        """Return a string indicating a special color tag value that has been assigned by the user.
        These color strings are displayed as colored bars in the gallery browser UI.
        Supported values are blue, green, purple, yellow, teal, and red.

        Args:
            item_id(str): The item id.
        Returns:
            str: The color.
        """

    def setColorTag(self, item_id: str, color_tag: str) -> bool:
        """Set the value of the colorTag for this item.
        Return True if this call resulted in a change to this value.
        
        Args:
            item_id(str): The item id.
            color_tag(str): The color tag.
        Returns:
            bool: The value changed state.
        """

    def metadata(self, item_id: str) -> dict:
        """Return a dictionary of metadata that has been associated
        with this item. This metadata may be user created, or
        automatically (such as by a renderer used to create an image
        in the snapshot gallery).

        Args:
            item_id(str): The item id.
        Returns:
            dict: The metadata dict.
        """

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

    def blindData(self, item_id: str) -> bytes:
        """Return a block of data source implementation specific
        binary data associated with the item.
        Returns:
            bytes: The binary data.
        """

    def setBlindData(self, item_id: str, data: bytes) -> bool:
        """Set the value of the blindData for this item.
        Args:
            item_id(str): The item id.
            data(bytes): The binary data.
        Returns:
            bool: The value changed state.
        """


def registerDataSources(manager):
    manager.registerDataSource("Asset Library", AssetLibrary)
