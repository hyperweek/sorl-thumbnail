import re
import os
from django.db import models
from sorl.thumbnail import defaults
from django.conf import settings

re_thumbnail_file = re.compile(r'(?P<source_filename>.+)_(?P<x>\d+)x(?P<y>\d+)(?:_(?P<options>\w+))?_q(?P<quality>\d+)(?:.[^.]+)?$')

if defaults.USE_S3:
    import storage.backends.s3 as s3

def push_to_s3(file_path):
    s3_storage = s3.S3Storage()
    img_file = open(os.path.join(settings.MEDIA_ROOT, file_path),'r')
    s3_img_file = s3_storage.open(file_path, 'w')
    s3_img_file.write(img_file.read())
    img_file.close()
    s3_img_file.close()

def is_on_s3(file_path):
    s3_storage = s3.S3Storage() 
    return s3_storage.exists(file_path)

def check_path(path):
    # Ensure the directory exists
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    
def pull_from_s3(file_path):
    s3_storage = s3.S3Storage()     
    local_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
    check_path(local_file_path)
    img_file = open(local_file_path,'w')
    s3_img_file = s3_storage.open(file_path, 'r')
    img_file.write(s3_img_file.read())
    s3_img_file.close()
    img_file.close()

def remove_model_thumbnails(sender, instance, *args, **kwargs):
    """Remove all thumbnails for all ImageFields (and subclasses) in the model 
    
    To be used with signals on models which use thumbnail tags.

    Signals are used instead of overiding the delete() method because
    the delete() method is not always called, e.g. when calling delete()
    on a queryset.

    To attach to a model:

        signals.pre_delete.connect(remove_model_thumbnails, sender=Photo)
    """

    for field in instance._meta.fields:
        if isinstance(field, models.ImageField):
            relative_source_path = getattr(instance, field.name).name
            delete_thumbnails(relative_source_path)

def all_thumbnails(path, recursive=True, prefix=None, subdir=None):
    """
    Return a dictionary referencing all files which match the thumbnail format.

    Each key is a source image filename, relative to path.
    Each value is a list of dictionaries as explained in `thumbnails_for_file`.
    """
    # Fall back to using thumbnail settings. These are local imports so that
    # there is no requirement of Django to use the utils module.
    if prefix is None:
        from sorl.thumbnail.main import get_thumbnail_setting
        prefix = get_thumbnail_setting('PREFIX')
    if subdir is None:
        from sorl.thumbnail.main import get_thumbnail_setting
        subdir = get_thumbnail_setting('SUBDIR')
    thumbnail_files = {}
    if not path.endswith('/'):
        path = '%s/' % path
    len_path = len(path)
    if recursive:
        all = os.walk(path)
    else:
        files = []
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                files.append(file)
        all = [(path, [], files)]
    for dir_, subdirs, files in all:
        rel_dir = dir_[len_path:]
        for file in files:
            thumb = re_thumbnail_file.match(file)
            if not thumb:
                continue
            d = thumb.groupdict()
            source_filename = d.pop('source_filename')
            if prefix:
                source_path, source_filename = os.path.split(source_filename)
                if not source_filename.startswith(prefix):
                    continue
                source_filename = os.path.join(source_path,
                    source_filename[len(prefix):])
            d['options'] = d['options'] and d['options'].split('_') or []
            if subdir and rel_dir.endswith(subdir):
                rel_dir = rel_dir[:-len(subdir)]
            # Corner-case bug: if the filename didn't have an extension but did
            # have an underscore, the last underscore will get converted to a
            # '.'.
            m = re.match(r'(.*)_(.*)', source_filename)
            if m:
                 source_filename = '%s.%s' % m.groups()
            filename = os.path.join(rel_dir, source_filename)
            thumbnail_file = thumbnail_files.setdefault(filename, [])
            d['filename'] = os.path.join(dir_, file)
            thumbnail_file.append(d)
    return thumbnail_files


def thumbnails_for_file(relative_source_path, root=None, basedir=None,
                        subdir=None, prefix=None):
    """
    Return a list of dictionaries, one for each thumbnail belonging to the
    source image.

    The following list explains each key of the dictionary:

      `filename`  -- absolute thumbnail path
      `x` and `y` -- the size of the thumbnail
      `options`   -- list of options for this thumbnail
      `quality`   -- quality setting for this thumbnail
    """
    # Fall back to using thumbnail settings. These are local imports so that
    # there is no requirement of Django to use the utils module.
    if root is None:
        from django.conf import settings
        root = settings.MEDIA_ROOT
    if prefix is None:
        from sorl.thumbnail.main import get_thumbnail_setting
        prefix = get_thumbnail_setting('PREFIX')
    if subdir is None:
        from sorl.thumbnail.main import get_thumbnail_setting
        subdir = get_thumbnail_setting('SUBDIR')
    if basedir is None:
        from sorl.thumbnail.main import get_thumbnail_setting
        basedir = get_thumbnail_setting('BASEDIR')
    source_dir, filename = os.path.split(relative_source_path)
    thumbs_path = os.path.join(root, basedir, source_dir, subdir)
    if not os.path.isdir(thumbs_path):
        return []
    files = all_thumbnails(thumbs_path, recursive=False, prefix=prefix,
                           subdir='')
    return files.get(filename, [])


def delete_thumbnails(relative_source_path, root=None, basedir=None,
                      subdir=None, prefix=None):
    """
    Delete all thumbnails for a source image.
    """
    thumbs = thumbnails_for_file(relative_source_path, root, basedir, subdir,
                                 prefix)
    return _delete_using_thumbs_list(thumbs)


def _delete_using_thumbs_list(thumbs):
    deleted = 0
    for thumb_dict in thumbs:
        filename = thumb_dict['filename']
        try:
            os.remove(filename)
        except:
            pass
        else:
            deleted += 1
    return deleted


def delete_all_thumbnails(path, recursive=True):
    """
    Delete all files within a path which match the thumbnails pattern.

    By default, matching files from all sub-directories are also removed. To
    only remove from the path directory, set recursive=False.
    """
    total = 0
    for thumbs in all_thumbnails(path, recursive=recursive).values():
        total += _delete_using_thumbs_list(thumbs)
    return total
