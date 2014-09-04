# -*- coding: utf-8 -*-

from .TaskTreeItem import TaskTreeColumn
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant


class TaskTreeModel(QAbstractItemModel):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._root = None

    def setRoot(self, root):
        self._root = root

    def headerData(self, section: int, orientation: "Qt.Orientation", role: int = None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == TaskTreeColumn.FileName:
                return "文件名"
            elif section == TaskTreeColumn.FileSize:
                return "大小"
            else:
                raise ValueError()

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs):
        return 2  # filename, filesize

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        if not self._root:
            return 0

        if parent.isValid():
            parentItem = parent.internalPointer()
            return parentItem.childrenCount()
        else:
            return self._root.childrenCount()

    def _indexToItem(self, index: QModelIndex):
        if not index.isValid():
            return self._root
        else:
            return index.internalPointer()

    def data(self, index: QModelIndex, role: int = None):
        if not index.isValid():
            return None
        item = index.internalPointer()

        if role in (Qt.DisplayRole, Qt.EditRole):
            return item.data(index.column())
        elif role == Qt.CheckStateRole and index.column() == TaskTreeColumn.FileName:
            return item.selected
        elif role == Qt.DecorationRole and index.column() == TaskTreeColumn.FileName:
            # TODO: use with real icons
            from PyQt5.QtGui import QIcon
            return QIcon.fromTheme("xware-desktop")

        return None

    def setData(self, index: QModelIndex, value: QVariant, role: int = None):
        if not index.isValid():
            return False
        item = index.internalPointer()

        if role == Qt.CheckStateRole:
            childrenCount = item.childrenCount()
            if childrenCount:
                for i in range(childrenCount):
                    self.setData(index.child(i, 0), value, role = role)
            else:
                item.selected = bool(value)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])

            # recalculate parents
            p = index
            while True:
                p = p.parent()
                if p.isValid():
                    self.dataChanged.emit(p, p, [Qt.CheckStateRole])
                else:
                    break

            # success
            return True

        if role == Qt.EditRole:
            assert index.column() == TaskTreeColumn.FileName
            item.name = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True

        return False

    def flags(self, index: QModelIndex):
        result = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == TaskTreeColumn.FileName:
            result |= Qt.ItemIsUserCheckable | Qt.ItemIsTristate
            if index.row() == 0:
                result |= Qt.ItemIsEditable

        return result

    def index(self, row: int, column: int, parent: QModelIndex = None):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentItem = self._indexToItem(parent)
        childItem = parentItem.nthChild(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index: QModelIndex = None):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self._root:
            return QModelIndex()
        else:
            return self.createIndex(parentItem.siblingNumber(), 0, parentItem)
