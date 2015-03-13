# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'

TEXT_DRM_FREE = ' (*: drm - free)'
LAB_DRM_FREE = '* : drm - free'

try:
    from PyQt5.Qt import (Qt, QVBoxLayout, QLabel, QApplication, QGroupBox, 
                          QDialogButtonBox, QHBoxLayout, QTextBrowser, QProgressDialog, 
                          QTimer, QSize, QDialog, QIcon, QTableWidget, QTableWidgetItem)
except ImportError:
    from PyQt4.Qt import (Qt, QVBoxLayout, QLabel, QApplication, QGroupBox, 
                          QDialogButtonBox, QHBoxLayout, QTextBrowser, QProgressDialog, 
                          QTimer, QSize, QDialog, QIcon, QTableWidget, QTableWidgetItem)

try:
    from PyQt5.QtWidgets import (QListWidget, QAbstractItemView)
except ImportError:
        from PyQt4.QtGui import (QListWidget, QAbstractItemView)

from calibre.gui2 import gprefs, warning_dialog, error_dialog
from calibre.gui2.dialogs.message_box import MessageBox

#from calibre.ptempfile import remove_dir

from calibre_plugins.obok_dedrm.utilities import (SizePersistedDialog, ImageTitleLayout, 
                                        showErrorDlg, get_icon, convert_qvariant, debug_print
                                        )
from calibre_plugins.obok_dedrm.__init__ import (PLUGIN_NAME,  
                        PLUGIN_SAFE_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION)

try:
    debug_print("obok::dialogs.py - loading translations")
    load_translations()
except NameError:
    debug_print("obok::dialogs.py - exception when loading translations")
    pass # load_translations() added in calibre 1.9

class SelectionDialog(SizePersistedDialog):
    '''
    Dialog to select the kobo books to decrypt
    '''
    def __init__(self, gui, interface_action, books):
        '''
        :param gui: Parent gui
        :param interface_action: InterfaceActionObject (InterfacePluginAction class from action.py)
        :param books: list of Kobo book
        '''
        
        self.books = books
        self.gui = gui
        self.interface_action = interface_action
        self.books = books

        SizePersistedDialog.__init__(self, gui, PLUGIN_NAME + 'plugin:selections dialog')
        self.setWindowTitle(_(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        title_layout = ImageTitleLayout(self, 'images/obok.png', _('Obok DeDRM'))
        layout.addLayout(title_layout)

        help_label = QLabel(_('<a href="http://www.foo.com/">Help</a>'), self)
        help_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        help_label.setAlignment(Qt.AlignRight)
        help_label.linkActivated.connect(self._help_link_activated)
        title_layout.addWidget(help_label)
        title_layout.setAlignment(Qt.AlignTop)

        layout.addSpacing(5)
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)
#        self.listy = QListWidget()
#        self.listy.setSelectionMode(QAbstractItemView.ExtendedSelection)
#        main_layout.addWidget(self.listy)
#        self.listy.addItems(books)
        self.books_table = BookListTableWidget(self)
        main_layout.addWidget(self.books_table)

        layout.addSpacing(10)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._ok_clicked)
        button_box.rejected.connect(self.reject)
        self.select_all_button = button_box.addButton(_("Select All"), QDialogButtonBox.ResetRole)
        self.select_all_button.setToolTip(_("Select all books to add them to the calibre library."))
        self.select_all_button.clicked.connect(self._select_all_clicked)
        self.select_drm_button = button_box.addButton(_("All with DRM"), QDialogButtonBox.ResetRole)
        self.select_drm_button.setToolTip(_("Select all books with DRM."))
        self.select_drm_button.clicked.connect(self._select_drm_clicked)
        self.select_free_button = button_box.addButton(_("All DRM free"), QDialogButtonBox.ResetRole)
        self.select_free_button.setToolTip(_("Select all books without DRM."))
        self.select_free_button.clicked.connect(self._select_free_clicked)
        layout.addWidget(button_box)

        # Cause our dialog size to be restored from prefs or created on first usage
        self.resize_dialog()
        self.books_table.populate_table(self.books)

    def _select_all_clicked(self):
        self.books_table.select_all()

    def _select_drm_clicked(self):
        self.books_table.select_drm(True)

    def _select_free_clicked(self):
        self.books_table.select_drm(False)

    def _help_link_activated(self, url):
        '''
        :param url: Dummy url to pass to the show_help method of the InterfacePluginAction class
        '''
        self.interface_action.show_help()

    def _ok_clicked(self):
        '''
        Build an index of the selected titles
        '''
        if len(self.books_table.selectedItems()):
            self.accept()
        else:
            msg = 'You must make a selection!'
            showErrorDlg(msg, self)

    def getBooks(self):
        '''
        Method to return the selected books
        '''
        return self.books_table.get_books()


class BookListTableWidget(QTableWidget):

    def __init__(self, parent):
        QTableWidget.__init__(self, parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

    def populate_table(self, books):
        self.clear()
        self.setAlternatingRowColors(True)
        self.setRowCount(len(books))
        header_labels = ['DRM', _('Title'), _('Author'), _('Series'), 'book_id']
        self.setColumnCount(len(header_labels))
        self.setHorizontalHeaderLabels(header_labels)
        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setStretchLastSection(True)

        self.books = {}
        for row, book in enumerate(books):
            self.populate_table_row(row, book)
            self.books[row] = book

        self.setSortingEnabled(False)
        self.resizeColumnsToContents()
        self.setMinimumColumnWidth(1, 100)
        self.setMinimumColumnWidth(2, 100)
        self.setMinimumSize(300, 0)
        if len(books) > 0:
            self.selectRow(0)
        self.hideColumn(4)
        self.setSortingEnabled(True)

    def setMinimumColumnWidth(self, col, minimum):
        if self.columnWidth(col) < minimum:
            self.setColumnWidth(col, minimum)

    def populate_table_row(self, row, book):
        if book.has_drm:
            icon = get_icon('drm-locked.png')
            val = 1
        else:
            icon = get_icon('drm-unlocked.png')
            val = 0

        status_cell = IconWidgetItem(None, icon, val)
        status_cell.setData(Qt.UserRole, val)
        self.setItem(row, 0, status_cell)
        self.setItem(row, 1, ReadOnlyTableWidgetItem(book.title))
        self.setItem(row, 2, AuthorTableWidgetItem(book.author, book.author))
        self.setItem(row, 3, SeriesTableWidgetItem(book.series, book.series_index))
        self.setItem(row, 4, NumericTableWidgetItem(row))

    def get_books(self):
#        debug_print("BookListTableWidget:get_books - self.books:", self.books)
        books = []
        if len(self.selectedItems()):
            for row in range(self.rowCount()):
#                debug_print("BookListTableWidget:get_books - row:", row)
                if self.item(row, 0).isSelected():
                    book_num = convert_qvariant(self.item(row, 4).data(Qt.DisplayRole))
                    debug_print("BookListTableWidget:get_books - book_num:", book_num)
                    book = self.books[book_num]
                    debug_print("BookListTableWidget:get_books - book:", book.title)
                    books.append(book)
        return books

    def select_all(self):
        self .selectAll()

    def select_drm(self, has_drm):
        self.clearSelection()
        current_selection_mode = self.selectionMode()
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        for row in range(self.rowCount()):
#           debug_print("BookListTableWidget:select_drm - row:", row)
            if convert_qvariant(self.item(row, 0).data(Qt.UserRole)) == 1:
#                debug_print("BookListTableWidget:select_drm - has DRM:", row)
                if has_drm:
                    self.selectRow(row)
            else:
#                debug_print("BookListTableWidget:select_drm - DRM free:", row)
                if not has_drm:
                    self.selectRow(row)
        self.setSelectionMode(current_selection_mode)


class DecryptAddProgressDialog(QProgressDialog):
    '''
    Use the QTimer singleShot method to dole out books one at
    a time to the indicated callback function from action.py
    '''
    def __init__(self, gui, indices, callback_fn, db, db_type='calibre', status_msg_type='books', action_type=('Decrypting','Decryption')):
        '''
        :param gui: Parent gui
        :param indices: List of Kobo books or list calibre book maps (indicated by param db_type)
        :param callback_fn: the function from action.py that will do the heavy lifting (get_decrypted_kobo_books or add_new_books)
        :param db: kobo database object or calibre database cache (indicated by param db_type)
        :param db_type: string indicating what kind of database param db is
        :param status_msg_type: string to indicate what the ProgressDialog is operating on (cosmetic only)
        :param action_type: 2-Tuple of strings indicating what the ProgressDialog is doing to param status_msg_type (cosmetic only)
        '''

        self.total_count = len(indices)
        QProgressDialog.__init__(self, '', 'Cancel', 0, self.total_count, gui)
        self.setMinimumWidth(500)
        self.indices, self.callback_fn, self.db, self.db_type = indices, callback_fn, db, db_type
        self.action_type, self.status_msg_type = action_type, status_msg_type
        self.gui = gui
        self.setWindowTitle('{0} {1} {2}...'.format(self.action_type[0], self.total_count, self.status_msg_type))
        self.i, self.successes, self.failures = 0, [], []
        QTimer.singleShot(0, self.do_book_action)
        self.exec_()

    def do_book_action(self):
        if self.wasCanceled():
            return self.do_close()
        if self.i >= self.total_count:
            return self.do_close()
        book = self.indices[self.i]
        self.i += 1

        # Get the title and build the caption and label text from the string parameters provided
        if self.db_type == 'calibre':
            dtitle = book[0].title
        elif self.db_type == 'kobo':
            dtitle = book.title
        self.setWindowTitle('{0} {1} {2}  ({3} {4} failures)...'.format(self.action_type[0], self.total_count,
                                                                self.status_msg_type, len(self.failures), self.action_type[1]))
        self.setLabelText('{0}: {1}'.format(self.action_type[0], dtitle))
        # If a calibre db, feed the calibre bookmap to action.py's add_new_books method
        if self.db_type == 'calibre':
            if self.callback_fn([book]):
                self.successes.append(book)
            else:
                self.failures.append(book)
        # If a kobo db, feed the index to the kobo book to action.py's get_decrypted_kobo_books method
        elif self.db_type == 'kobo':
            if self.callback_fn(book):
                debug_print("DecryptAddProgressDialog::do_book_action - decrypted book: '%s'" % dtitle)
                self.successes.append(book)
            else:
                debug_print("DecryptAddProgressDialog::do_book_action - book decryption failed: '%s'" % dtitle)
                self.failures.append(book)
        self.setValue(self.i)

        # Lather, rinse, repeat.
        QTimer.singleShot(0, self.do_book_action)

    def do_close(self):
        self.hide()
        self.gui = None

class AddEpubFormatsProgressDialog(QProgressDialog):
    '''
    Use the QTimer singleShot method to dole out epub formats one at
    a time to the indicated callback function from action.py
    '''
    def __init__(self, gui, entries, callback_fn, status_msg_type='formats', action_type=('Adding','Added')):
        '''
        :param gui: Parent gui
        :param entries: List of 3-tuples  [(target calibre id, calibre metadata object, path to epub file)]
        :param callback_fn: the function from action.py that will do the heavy lifting (process_epub_formats)
        :param status_msg_type: string to indicate what the ProgressDialog is operating on (cosmetic only)
        :param action_type: 2-tuple of strings indicating what the ProgressDialog is doing to param status_msg_type (cosmetic only)
        '''

        self.total_count = len(entries)
        QProgressDialog.__init__(self, '', 'Cancel', 0, self.total_count, gui)
        self.setMinimumWidth(500)
        self.entries, self.callback_fn = entries, callback_fn
        self.action_type, self.status_msg_type = action_type, status_msg_type
        self.gui = gui
        self.setWindowTitle('{0} {1} {2}...'.format(self.action_type[0], self.total_count, self.status_msg_type))
        self.i, self.successes, self.failures = 0, [], []
        QTimer.singleShot(0, self.do_book_action)
        self.exec_()

    def do_book_action(self):
        if self.wasCanceled():
            return self.do_close()
        if self.i >= self.total_count:
            return self.do_close()
        epub_format = self.entries[self.i]
        self.i += 1

        # assign the elements of the 3-tuple details to legible variables
        book_id, mi, path = epub_format[0], epub_format[1], epub_format[2]
        
        # Get the title and build the caption and label text from the string parameters provided
        dtitle = mi.title
        self.setWindowTitle('{0} {1} {2}  ({3} {4} failures)...'.format(self.action_type[0], self.total_count,
                                                                self.status_msg_type, len(self.failures), self.action_type[1]))
        self.setLabelText('{0}: {1}'.format(self.action_type[0], dtitle))
        # Send the necessary elements to the process_epub_formats callback function (action.py)
        # and record the results
        if self.callback_fn(book_id, mi, path):
            self.successes.append((book_id, mi, path))
        else:
            self.failures.append((book_id, mi, path))
        self.setValue(self.i)

        # Lather, rinse, repeat
        QTimer.singleShot(0, self.do_book_action)

    def do_close(self):
        self.hide()
        self.gui = None

class ViewLog(QDialog):
    '''
    Show a detailed summary of results as html.
    '''
    def __init__(self, title, html, parent=None):
        '''
        :param title: Caption for window title
        :param html: HTML string log/report
        '''
        QDialog.__init__(self, parent)
        self.l = l = QVBoxLayout()
        self.setLayout(l)

        self.tb = QTextBrowser(self)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        # Rather than formatting the text in <pre> blocks like the calibre
        # ViewLog does, instead just format it inside divs to keep style formatting
        html = html.replace('\t','&nbsp;&nbsp;&nbsp;&nbsp;')#.replace('\n', '<br/>')
        html = html.replace('> ','>&nbsp;')
        self.tb.setHtml('<div>{0}</div>'.format(html))
        QApplication.restoreOverrideCursor()
        l.addWidget(self.tb)

        self.bb = QDialogButtonBox(QDialogButtonBox.Ok)
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)
        self.copy_button = self.bb.addButton(_('Copy to clipboard'),
                self.bb.ActionRole)
        self.copy_button.setIcon(QIcon(I('edit-copy.png')))
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        l.addWidget(self.bb)
        self.setModal(False)
        self.resize(QSize(700, 500))
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(I('dialog_information.png')))
        self.show()

    def copy_to_clipboard(self):
        txt = self.tb.toPlainText()
        QApplication.clipboard().setText(txt)


class ResultsSummaryDialog(MessageBox): 
    def __init__(self, parent, title, msg, log='', det_msg=''):
        '''
        :param log: An HTML log
        :param title: The title for this popup
        :param msg: The msg to display
        :param det_msg: Detailed message
        '''
        MessageBox.__init__(self, MessageBox.INFO, title, msg,
                det_msg=det_msg, show_copy_button=False,
                parent=parent)
        self.log = log
        self.vlb = self.bb.addButton(_('View Report'), self.bb.ActionRole)
        self.vlb.setIcon(QIcon(I('dialog_information.png')))
        self.vlb.clicked.connect(self.show_log)
        self.det_msg_toggle.setVisible(bool(det_msg))
        self.vlb.setVisible(bool(log))

    def show_log(self):
        self.log_viewer = ViewLog(PLUGIN_NAME + ' v' + PLUGIN_VERSION, self.log,
                parent=self)


class ReadOnlyTableWidgetItem(QTableWidgetItem):
    def __init__(self, text):
        if text is None:
            text = ''
        QTableWidgetItem.__init__(self, text, QTableWidgetItem.UserType)
        self.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

class AuthorTableWidgetItem(ReadOnlyTableWidgetItem):
    def __init__(self, text, sort_key):
        ReadOnlyTableWidgetItem.__init__(self, text)
        self.sort_key = sort_key

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        return self.sort_key < other.sort_key

class SeriesTableWidgetItem(ReadOnlyTableWidgetItem):
    def __init__(self, series, series_index=None):
        display = ''
        if series:
            if series_index:
                from calibre.ebooks.metadata import fmt_sidx
                display = '%s [%s]' % (series, fmt_sidx(series_index))
                self.sortKey = '%s%04d' % (series, series_index)
            else:
                display = series
                self.sortKey = series
        ReadOnlyTableWidgetItem.__init__(self, display)

class IconWidgetItem(ReadOnlyTableWidgetItem):
    def __init__(self, text, icon, sort_key):
        ReadOnlyTableWidgetItem.__init__(self, text)
        if icon:
            self.setIcon(icon)
        self.sort_key = sort_key

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    def __lt__(self, other):
        return self.sort_key < other.sort_key

class NumericTableWidgetItem(QTableWidgetItem):

    def __init__(self, number, is_read_only=False):
        QTableWidgetItem.__init__(self, '', QTableWidgetItem.UserType)
        self.setData(Qt.DisplayRole, number)
        if is_read_only:
            self.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)

