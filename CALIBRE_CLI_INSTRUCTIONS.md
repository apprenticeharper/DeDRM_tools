# Using the DeDRM plugin with the Calibre command line interface

If you prefer the Calibre CLI instead of the GUI, follow this guide to
install and use the DeDRM plugin.

This guide assumes you are on Linux, but it may very well work on other
platforms.

## Step-by-step Tutorial

#### Install Calibre
   - Follow [Calibre's installation instructions](https://calibre-ebook.com/download_linux)

#### Install plugins
  - Download the DeDRM `.zip` archive from DeDRM_tools'
     [latest release](https://github.com/apprenticeharper/DeDRM_tools/releases/latest).
     Then unzip it.
  - Add the DeDRM plugin to Calibre:
     ```
     cd *the unzipped DeDRM_tools folder*
     calibre-customize --add DeDRM_calibre_plugin/DeDRM_plugin.zip
     ```
  - Add the Obok plugin:
    ```
    calibre-customize --add Obok_calibre_plugin/obok_plugin.zip
    ```

#### Enter your keys
  - Figure out what format DeDRM wants your key in by looking in
     [the code that handles that](DeDRM_plugin/prefs.py).
     - For Kindle eInk devices, DeDRM expects you to put a list of serial
       numbers in the `serials` field: `"serials": ["012345689abcdef"]` or
       `"serials": ["1111111111111111", "2222222222222222"]`.
  - Now add your keys to `$CALIBRE_CONFIG_DIRECTORY/plugins/dedrm.json`.

#### Import your books
  - Make a library folder
  ```
  mkdir library
  ```
  - Add your book(s) with this command:
  ```
  calibredb add /path/to/book.format --with-library=library
  ```

The DRM should be removed from your book, which you can find in the `library`
folder.
