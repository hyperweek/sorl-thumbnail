from django.core.management.base import BaseCommand
import os
import re
from django.conf import settings
from sorl.thumbnail.main import get_thumbnail_setting

THUMB_RE = re.compile(r'^%s(.*)_\d{1,}x\d{1,}_[-\w]*q([1-9]\d?|100)\.jpg' % 
                      get_thumbnail_setting('PREFIX'))

class Command(BaseCommand):
    help = "Tries to delete thumbnails not in use."

    def get_thumbnail_path(self, path):
        basedir = get_thumbnail_setting('BASEDIR')
        subdir = get_thumbnail_setting('SUBDIR')
        return os.path.join(basedir, path, subdir)

    def handle(self, *args, **options):
        paths = ['.']
        for path in paths:
            thumbnail_path = self.get_thumbnail_path(path)
            file_list = os.listdir(os.path.join(settings.MEDIA_ROOT, thumbnail_path))
            for fn in file_list:
                m = THUMB_RE.match(fn)
                if m:
                    # Due to that the naming of thumbnails replaces the dot before
                    # extension with an underscore we have 2 possibilities for the
                    # original filename. If either present we do not delete
                    # suspected thumbnail.
                    # org_fn is the expected original filename w/o extension
                    # org_fn_alt is the expected original filename with extension
                    org_fn = m.group(1)
                    org_fn_exists = os.path.isfile(os.path.join(settings.MEDIA_ROOT, path, org_fn))
                    
                    usc_pos = org_fn.rfind("_")
                    if usc_pos != -1:
                        org_fn_alt = "%s.%s" % (org_fn[0:usc_pos], org_fn[usc_pos+1:])
                        org_fn_alt_exists = os.path.isfile(
                            os.path.join(settings.MEDIA_ROOT, path, org_fn_alt))
                    else:
                        org_fn_alt_exists = False
                    if not org_fn_exists and not org_fn_alt_exists:
                        del_me = os.path.join(settings.MEDIA_ROOT, thumbnail_path, fn)
                        print "Removing: %s" % del_me
                        os.remove(del_me)

