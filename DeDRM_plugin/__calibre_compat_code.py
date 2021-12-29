
#@@CALIBRE_COMPAT_CODE_START@@
import sys, os

# Explicitly allow importing the parent folder
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Bugfix for Calibre < 5:
if "calibre" in sys.modules and sys.version_info[0] == 2:
    from calibre.utils.config import config_dir
    if os.path.join(config_dir, "plugins", "DeDRM.zip") not in sys.path:
        sys.path.insert(0, os.path.join(config_dir, "plugins", "DeDRM.zip"))
#@@CALIBRE_COMPAT_CODE_END@@
