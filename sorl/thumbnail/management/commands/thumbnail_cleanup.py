from django.core.management.base import BaseCommand
import os
import re
from django.conf import settings
from sorl.thumbnail.main import get_thumbnail_setting

THUMB_RE = re.compile(r'^%s(.*)_\d{1,}x\d{1,}_[-\w]*q([1-9]\d?|100)\.jpg' % 
                      get_thumbnail_setting('PREFIX'))

class Command(BaseCommand):
    help = "Tries to delete thumbnails not in use."

    def handle(self, *args, **options):
        for (dirpath, dirnames, filenames) in os.walk(settings.MEDIA_ROOT):
            for f in filenames:
                m = THUMB_RE.match(f)
                if m:
                    del_me = os.path.join(dirpath, f)
                    print "Removing: %s" % del_me
                    os.remove(del_me)

