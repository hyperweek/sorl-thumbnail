DEBUG = False
BASEDIR = ''
SUBDIR = ''
PREFIX = ''
QUALITY = 85
CONVERT = '/usr/bin/convert'
WVPS = '/usr/bin/wvPS'
EXTENSION = 'jpg'
PROCESSORS = (
    'sorl.thumbnail.processors.colorspace',
    'sorl.thumbnail.processors.autocrop',
    'sorl.thumbnail.processors.scale_and_crop',
    'sorl.thumbnail.processors.filters',
)

from django.conf import settings
USE_S3 = 'S3' in settings.DEFAULT_FILE_STORAGE
