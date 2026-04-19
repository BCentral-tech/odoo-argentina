##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
import configparser

# pyafipws still imports SafeConfigParser in ws_sr_padron. Python 3.12 removed
# that deprecated alias, so expose it before any AFIP/ARCA connection is built.
if not hasattr(configparser, "SafeConfigParser"):
    configparser.SafeConfigParser = configparser.ConfigParser

from . import models
