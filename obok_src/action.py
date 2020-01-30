# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'


import os, traceback, zipfile

try:
    from PyQt5.Qt import QToolButton, QUrl
except ImportError:
    from PyQt4.Qt import QToolButton, QUrl
 
from calibre.gui2 import open_url, question_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import config_dir
from calibre.ptempfile import (PersistentTemporaryDirectory,
                               PersistentTemporaryFile, remove_dir)

from calibre.ebooks.metadata.meta import get_metadata

from calibre_plugins.obok_dedrm.dialogs import (SelectionDialog, DecryptAddProgressDialog,
                                                AddEpubFormatsProgressDialog, ResultsSummaryDialog)
from calibre_plugins.obok_dedrm.config import plugin_prefs as cfg
from calibre_plugins.obok_dedrm.__init__ import (PLUGIN_NAME, PLUGIN_SAFE_NAME, 
                                PLUGIN_VERSION, PLUGIN_DESCRIPTION, HELPFILE_NAME)
from calibre_plugins.obok_dedrm.utilities import (
                            get_icon, set_plugin_icon_resources, showErrorDlg, format_plural,
                            debug_print
                            )

from calibre_plugins.obok_dedrm.obok.obok import KoboLibrary
from calibre_plugins.obok_dedrm.obok.legacy_obok import legacy_obok

PLUGIN_ICONS = ['images/obok.png']

try:
    debug_print("obok::action_err.py - loading translations")
    load_translations()
except NameError:
    debug_print("obok::action_err.py - exception when loading translations")
    pass # load_translations() added in calibre 1.9

class InterfacePluginAction(InterfaceAction):
    name = PLUGIN_NAME
    action_spec = (PLUGIN_NAME, None,
            _(PLUGIN_DESCRIPTION), None)
    popup_type = QToolButton.InstantPopup
    action_type = 'current'

    def genesis(self):
        icon_resources = self.load_resources(PLUGIN_ICONS)
        set_plugin_icon_resources(PLUGIN_NAME, icon_resources)
        
        self.qaction.setIcon(get_icon(PLUGIN_ICONS[0]))
        self.qaction.triggered.connect(self.launchObok)
        self.gui.keyboard.finalize()

    def launchObok(self):
        '''
        Main processing/distribution method
        '''
        self.count = 0
        self.books_to_add = []
        self.formats_to_add = []
        self.add_books_cancelled = False
        self.decryption_errors = []
        self.userkeys = []
        self.duplicate_book_list = []
        self.no_home_for_book = []
        self.ids_of_new_books = []
        self.successful_format_adds =[]
        self.add_formats_cancelled = False
        self.tdir = PersistentTemporaryDirectory('_obok', prefix='')
        self.db = self.gui.current_db.new_api
        self.current_idx = self.gui.library_view.currentIndex()

        print ('Running {}'.format(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
        #
        # search for connected device in case serials are saved
        tmpserials = cfg['kobo_serials']
        device_path = None
        try:
            device = self.parent().device_manager.connected_device
            if (device):
                device_path = device._main_prefix
                debug_print("get_device_settings - device_path=", device_path)
            else:
                debug_print("didn't find device")
        except:
            debug_print("Exception getting device path. Probably not an E-Ink Kobo device")

        # Get the Kobo Library object (obok v3.01)
        self.library = KoboLibrary(tmpserials, device_path, cfg['kobo_directory'])
        debug_print ("got kobodir %s" % self.library.kobodir)
        if (self.library.kobodir == ''):
            # linux and no device connected, but could be extended
            # to the case where on Windows/Mac the prog is not installed
            msg = _('<p>Could not find Kobo Library\n<p>Windows/Mac: do you have Kobo Desktop installed?\n<p>Windows/Mac/Linux: In case you have an Kobo eInk device, connect the device.')
            showErrorDlg(msg, None)
            return


        # Get a list of Kobo titles
        books = self.build_book_list()
        if len(books) < 1:
            msg = _('<p>No books found in Kobo Library\nAre you sure it\'s installed\configured\synchronized?')
            showErrorDlg(msg, None)
            return
        
        # Check to see if a key can be retrieved using the legacy obok method.
        legacy_key = legacy_obok().get_legacy_cookie_id
        if legacy_key is not None:
            print (_('Legacy key found: '), legacy_key.encode('hex_codec'))
            self.userkeys.append(legacy_key)
        # Add userkeys found through the normal obok method to the list to try.
        try:
            candidate_keys = self.library.userkeys
        except:
            print (_('Trouble retrieving keys with newer obok method.'))
            traceback.print_exc()
        else:
            if len(candidate_keys):
                self.userkeys.extend(candidate_keys)
                print (_('Found {0} possible keys to try.').format(len(self.userkeys)))
        if not len(self.userkeys):
            msg = _('<p>No userkeys found to decrypt books with. No point in proceeding.')
            showErrorDlg(msg, None)
            return

        # Launch the Dialog so the user can select titles.
        dlg = SelectionDialog(self.gui, self, books)
        if dlg.exec_():
            books_to_import = dlg.getBooks()
            self.count = len(books_to_import)
            debug_print("InterfacePluginAction::launchObok - number of books to decrypt: %d" % self.count)
            # Feed the titles, the callback function (self.get_decrypted_kobo_books)
            # and the Kobo library object to the ProgressDialog dispatcher.
            d = DecryptAddProgressDialog(self.gui, books_to_import, self.get_decrypted_kobo_books, self.library, 'kobo',
                               status_msg_type='Kobo books', action_type=('Decrypting', 'Decryption'))
            # Canceled the decryption process; clean up and exit.
            if d.wasCanceled():
                print (_('{} - Decryption canceled by user.').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
                self.library.close()
                remove_dir(self.tdir)
                return
        else:
            # Canceled the selection process; clean up and exit.
            self.library.close()
            remove_dir(self.tdir)
            return
        # Close Kobo Library object
        self.library.close()

        # If we have decrypted books to work with, feed the list of decrypted books details 
        # and the callback function (self.add_new_books) to the ProgressDialog dispatcher.
        if len(self.books_to_add):
            d = DecryptAddProgressDialog(self.gui, self.books_to_add, self.add_new_books, self.db, 'calibre',
                               status_msg_type='new calibre books', action_type=('Adding','Addition'))
            # Canceled the "add new books to calibre" process;
            # show the results of what got added before cancellation.
            if d.wasCanceled():
                print (_('{} - "Add books" canceled by user.').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
                self.add_books_cancelled = True
                print (_('{} - wrapping up results.').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
                self.wrap_up_results()
                remove_dir(self.tdir)
                return
        # If books couldn't be added because of duplicate entries in calibre, ask
        # if we should try to add the decrypted epubs to existing calibre library entries.
        if len(self.duplicate_book_list):
            if cfg['finding_homes_for_formats'] == 'Always':
                self.process_epub_formats()
            elif cfg['finding_homes_for_formats'] == 'Never':
                self.no_home_for_book.extend([entry[0] for entry in self.duplicate_book_list])
            else:
                if self.ask_about_inserting_epubs():
                    # Find homes for the epub decrypted formats in existing calibre library entries.
                    self.process_epub_formats()
                else:
                    print (_('{} - User opted not to try to insert EPUB formats').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
                    self.no_home_for_book.extend([entry[0] for entry in self.duplicate_book_list])

        print (_('{} - wrapping up results.').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
        self.wrap_up_results()
        remove_dir(self.tdir)
        return

    def show_help(self):
        '''
        Extract on demand the help file resource
        '''
        def get_help_file_resource():
            # We will write the help file out every time, in case the user upgrades the plugin zip
            # and there is a newer help file contained within it.
            file_path = os.path.join(config_dir, 'plugins', HELPFILE_NAME)
            file_data = self.load_resources(HELPFILE_NAME)[HELPFILE_NAME]
            with open(file_path,'w') as f:
                f.write(file_data)
            return file_path
        url = 'file:///' + get_help_file_resource()
        open_url(QUrl(url))

    def build_book_list(self):
        '''
        Connect to Kobo db and get titles.
        '''
        return self.library.books

    def get_decrypted_kobo_books(self, book):
        '''
        This method is a call-back function used by DecryptAddProgressDialog in dialogs.py to decrypt Kobo books
        
        :param book: A KoboBook object that is to be decrypted.
        '''
        print (_('{0} - Decrypting {1}').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION, book.title))
        decrypted = self.decryptBook(book)
        if decrypted['success']:
            # Build a list of calibre "book maps" for calibre's add_book function.
            mi = get_metadata(decrypted['fileobj'], 'epub')
            bookmap = {'EPUB':decrypted['fileobj'].name}
            self.books_to_add.append((mi, bookmap))
        else:
            # Book is probably still encrypted.
            print (_('{0} - Couldn\'t decrypt {1}').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION, book.title))
            self.decryption_errors.append((book.title, _('decryption errors')))
            return False
        return True

    def add_new_books(self, books_to_add):
        '''
        This method is a call-back function used by DecryptAddProgressDialog in dialogs.py to add books to calibre
        (It's set up to handle multiple books, but will only be fed books one at a time by DecryptAddProgressDialog)
        
        :param books_to_add: List of calibre bookmaps (created in get_decrypted_kobo_books)
        '''
        added = self.db.add_books(books_to_add, add_duplicates=False, run_hooks=False)
        if len(added[0]):
            # Record the id(s) that got added
            for id in added[0]:
                print (_('{0} - Added {1}').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION, books_to_add[0][0].title))
                self.ids_of_new_books.append((id, books_to_add[0][0]))
        if len(added[1]):
            # Build a list of details about the books that didn't get added because duplicate were detected.
            for mi, map in added[1]:
                print (_('{0} - {1} already exists. Will try to add format later.').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION, mi.title))
                self.duplicate_book_list.append((mi, map['EPUB'], _('duplicate detected')))
            return False
        return True

    def add_epub_format(self, book_id, mi, path):
        '''
        This method is a call-back function used by AddEpubFormatsProgressDialog in dialogs.py
        
        :param book_id: calibre ID of the book to add the encrypted epub to.
        :param mi: calibre metadata object
        :param path: path to the decrypted epub (temp file)
        '''
        if self.db.add_format(book_id, 'EPUB', path, replace=False, run_hooks=False):
            self.successful_format_adds.append((book_id, mi))
            print (_('{0} - Successfully added EPUB format to existing {1}').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION, mi.title))
            return True
        # we really shouldn't get here.
        print (_('{0} - Error adding EPUB format to existing {1}. This really shouldn\'t happen.').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION, mi.title))
        self.no_home_for_book.append(mi)
        return False

    def process_epub_formats(self):
        '''
        Ask the user if they want to try to find homes for those books that already had an entry in calibre
        '''
        for book in self.duplicate_book_list:
            mi, tmp_file = book[0], book[1]
            dup_ids = self.db.find_identical_books(mi)
            home_id = self.find_a_home(dup_ids)
            if home_id is not None:
                # Found an epub-free duplicate to add the epub to.
                # build a list for the add_epub_format method to use.
                self.formats_to_add.append((home_id, mi, tmp_file))
            else:
                self.no_home_for_book.append(mi)
        # If we found homes for decrypted epubs in existing calibre entries, feed the list of decrypted book 
        # details and the callback function (self.add_epub_format) to the ProgressDialog dispatcher.
        if self.formats_to_add:
            d = AddEpubFormatsProgressDialog(self.gui, self.formats_to_add, self.add_epub_format)
            if d.wasCanceled():
                print (_('{} - "Insert formats" canceled by user.').format(PLUGIN_NAME + ' v' + PLUGIN_VERSION))
                self.add_formats_cancelled = True
                return
            #return
        return

    def wrap_up_results(self):
        '''
        Present the results
        '''
        caption = PLUGIN_NAME + ' v' + PLUGIN_VERSION
        # Refresh the gui and highlight new entries/modified entries.
        if len(self.ids_of_new_books) or len(self.successful_format_adds):
            self.refresh_gui_lib()

        msg, log = self.build_report()

        sd = ResultsSummaryDialog(self.gui, caption, msg, log)
        sd.exec_()
        return
    
    def ask_about_inserting_epubs(self):
        '''
        Build question dialog with details about kobo books 
        that couldn't be added to calibre as new books.
        '''
        ''' Terisa: Improve the message
        '''
        caption = PLUGIN_NAME + ' v' + PLUGIN_VERSION
        plural = format_plural(len(self.ids_of_new_books))
        det_msg = ''
        if self.count > 1:
            msg = _('<p><b>{0}</b> EPUB{2} successfully added to library.<br /><br /><b>{1}</b> ').format(len(self.ids_of_new_books), len(self.duplicate_book_list), plural)
            msg += _('not added because books with the same title/author were detected.<br /><br />Would you like to try and add the EPUB format{0}').format(plural)
            msg += _(' to those existing entries?<br /><br />NOTE: no pre-existing EPUBs will be overwritten.')
            for entry in self.duplicate_book_list:
                det_msg += _('{0} -- not added because of {1} in your library.\n\n').format(entry[0].title, entry[2])
        else:
            msg = _('<p><b>{0}</b> -- not added because of {1} in your library.<br /><br />').format(self.duplicate_book_list[0][0].title, self.duplicate_book_list[0][2])
            msg += _('Would you like to try and add the EPUB format to an available calibre duplicate?<br /><br />')
            msg += _('NOTE: no pre-existing EPUB will be overwritten.')
            
        return question_dialog(self.gui, caption, msg, det_msg)

    def find_a_home(self, ids):
        '''
        Find the ID of the first EPUB-Free duplicate available
        
        :param ids: List of calibre IDs that might serve as a home.
        '''
        for id in ids:
            # Find the first entry that matches the incoming book that doesn't have an EPUB format.
            if not self.db.has_format(id, 'EPUB'):
                return id
                break
        return None

    def refresh_gui_lib(self):
        '''
        Update the GUI; highlight the books that were added/modified
        '''
        if self.current_idx.isValid():
            self.gui.library_view.model().current_changed(self.current_idx, self.current_idx)
        new_entries = [id for id, mi in self.ids_of_new_books]
        if new_entries:
            self.gui.library_view.model().db.data.books_added(new_entries)
            self.gui.library_view.model().books_added(len(new_entries))
        new_entries.extend([id for id, mi in self.successful_format_adds])
        self.gui.db_images.reset()
        self.gui.tags_view.recount()
        self.gui.library_view.model().set_highlight_only(True)
        self.gui.library_view.select_rows(new_entries)
        return

    def decryptBook(self, book):
        '''
        Decrypt Kobo book

        :param book: obok file object
        '''
        result = {}
        result['success'] = False
        result['fileobj'] = None

        zin = zipfile.ZipFile(book.filename, 'r')
        #print ('Kobo library filename: {0}'.format(book.filename))
        for userkey in self.userkeys:
            print (_('Trying key: '), userkey.encode('hex_codec'))
            check = True
            try:
                fileout = PersistentTemporaryFile('.epub', dir=self.tdir)
                #print ('Temp file: {0}'.format(fileout.name))
                # modify the output file to be compressed by default
                zout = zipfile.ZipFile(fileout.name, "w", zipfile.ZIP_DEFLATED)
                # ensure that the mimetype file is the first written to the epub container
                # and is stored with no compression
                members = zin.namelist();
                try:
                    members.remove('mimetype')
                except Exception:
                    pass
                zout.writestr('mimetype', 'application/epub+zip', zipfile.ZIP_STORED)
                # end of mimetype mod
                for filename in members:
                    contents = zin.read(filename)
                    if filename in book.encryptedfiles:
                        file = book.encryptedfiles[filename]
                        contents = file.decrypt(userkey, contents)
                        # Parse failures mean the key is probably wrong.
                        if check:
                            check = not file.check(contents)
                    zout.writestr(filename, contents)
                zout.close()
                zin.close()
                result['success'] = True
                result['fileobj'] = fileout
                print ('Success!')
                return result
            except ValueError:
                print (_('Decryption failed, trying next key.'))
                zout.close()
                continue
            except Exception:
                print (_('Unknown Error decrypting, trying next key..'))
                zout.close()
                continue
        result['fileobj'] = book.filename
        zin.close()
        return result

    def build_report(self):
        log = ''
        processed = len(self.ids_of_new_books) + len(self.successful_format_adds)

        if processed == self.count:
            if self.count > 1:
                msg = _('<p>All selected Kobo books added as new calibre books or inserted into existing calibre ebooks.<br /><br />No issues.')
            else:
                # Single book ... don't get fancy.
                title = self.ids_of_new_books[0][1].title if self.ids_of_new_books else self.successful_format_adds[0][1].title
                msg = _('<p>{0} successfully added.').format(title)
            return (msg, log)
        else:
            if self.count != 1:
                msg = _('<p>Not all selected Kobo books made it into calibre.<br /><br />View report for details.')
                log += _('<p><b>Total attempted:</b> {}</p>\n').format(self.count)
                log += _('<p><b>Decryption errors:</b> {}</p>\n').format(len(self.decryption_errors))
                if self.decryption_errors:
                    log += '<ul>\n'
                    for title, reason in self.decryption_errors:
                        log += '<li>{}</li>\n'.format(title)
                    log += '</ul>\n'
                log += _('<p><b>New Books created:</b> {}</p>\n').format(len(self.ids_of_new_books))
                if self.ids_of_new_books:
                    log += '<ul>\n'
                    for id, mi in self.ids_of_new_books:
                        log += '<li>{}</li>\n'.format(mi.title)
                    log += '</ul>\n'
                if self.add_books_cancelled:
                    log += _('<p><b>Duplicates that weren\'t added:</b> {}</p>\n').format(len(self.duplicate_book_list))
                    if self.duplicate_book_list:
                        log += '<ul>\n'
                        for book in self.duplicate_book_list:
                            log += '<li>{}</li>\n'.format(book[0].title)
                        log += '</ul>\n'
                    cancelled_count = self.count - (len(self.decryption_errors) + len(self.ids_of_new_books) + len(self.duplicate_book_list))
                    if cancelled_count > 0:
                        log += _('<p><b>Book imports cancelled by user:</b> {}</p>\n').format(cancelled_count)
                    return (msg, log)
                log += _('<p><b>New EPUB formats inserted in existing calibre books:</b> {0}</p>\n').format(len(self.successful_format_adds))        
                if self.successful_format_adds:
                    log += '<ul>\n'
                    for id, mi in self.successful_format_adds:
                        log += '<li>{}</li>\n'.format(mi.title)
                    log += '</ul>\n'
                log += _('<p><b>EPUB formats NOT inserted into existing calibre books:</b> {}<br />\n').format(len(self.no_home_for_book))
                log += _('(Either because the user <i>chose</i> not to insert them, or because all duplicates already had an EPUB format)')
                if self.no_home_for_book:
                    log += '<ul>\n'
                    for mi in self.no_home_for_book:
                        log += '<li>{}</li>\n'.format(mi.title)
                    log += '</ul>\n'
                if self.add_formats_cancelled:
                    cancelled_count = self.count - (len(self.decryption_errors) + len(self.ids_of_new_books) + len(self.successful_format_adds) + len(self.no_home_for_book))
                    if cancelled_count > 0:
                        log += _('<p><b>Format imports cancelled by user:</b> {}</p>\n').format(cancelled_count)
                return (msg, log)
            else:
                
                # Single book ... don't get fancy.
                if self.ids_of_new_books:
                    title = self.ids_of_new_books[0][1].title
                elif self.successful_format_adds:
                    title = self.successful_format_adds[0][1].title
                elif self.no_home_for_book:
                    title = self.no_home_for_book[0].title
                elif self.decryption_errors:
                    title = self.decryption_errors[0][0]
                else:
                    title = _('Unknown Book Title')
                if self.decryption_errors:
                    reason = _('it couldn\'t be decrypted.')
                elif self.no_home_for_book:
                    reason = _('user CHOSE not to insert the new EPUB format, or all existing calibre entries HAD an EPUB format already.')
                else:
                    reason = _('of unknown reasons. Gosh I\'m embarrassed!')
                msg = _('<p>{0} not added because {1}').format(title, reason)
                return (msg, log)
 
