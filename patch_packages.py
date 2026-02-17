"""Patch installed packages for Django 3 compatibility."""
import re
import pathlib

packages = ['djangoplugins', 'popolo', 'popolo_sources', 'subdomains', 'popit']


def find_matching_paren(text, start):
    """Find the index of the closing paren matching the open paren at start."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    return -1


def patch_on_delete(text):
    """Add missing on_delete to ForeignKey/OneToOneField."""
    result = text
    offset = 0
    for field_type in ['ForeignKey', 'OneToOneField']:
        pattern = re.compile(rf'models\.{field_type}\(')
        for m in pattern.finditer(text):
            open_paren = m.end() - 1
            close_paren = find_matching_paren(text, open_paren)
            if close_paren == -1:
                continue
            inner = text[open_paren + 1:close_paren]
            if 'on_delete' in inner:
                continue
            if 'null=True' in inner:
                insert = ', on_delete=models.SET_NULL'
            else:
                insert = ', on_delete=models.CASCADE'
            pos = close_paren + offset
            result = result[:pos] + insert + result[pos:]
            offset += len(insert)
    return result


def patch_subfieldbase(text):
    """Remove __metaclass__ = models.SubfieldBase (removed in Django 2.0)."""
    text = re.sub(r'\s*__metaclass__\s*=\s*models\.SubfieldBase\n', '\n', text)
    return text


def patch_django3_imports(text):
    """Replace removed Django 3 imports with their Python 3 equivalents."""
    replacements = [
        # django.utils.six -> six
        ('from django.utils.six import', 'from six import'),
        ('from django.utils import six', 'import six'),
        # django.utils.encoding
        ('from django.utils.encoding import python_2_unicode_compatible', 'python_2_unicode_compatible = lambda cls: cls'),
        # django.utils.translation
        ('from django.utils.translation import ugettext_lazy as _', 'from django.utils.translation import gettext_lazy as _'),
        ('from django.utils.translation import ugettext as _', 'from django.utils.translation import gettext as _'),
        ('from django.utils.translation import ugettext_lazy', 'from django.utils.translation import gettext_lazy as ugettext_lazy'),
        ('from django.utils.translation import ugettext', 'from django.utils.translation import gettext as ugettext'),
        # django.core.urlresolvers -> django.urls
        ('from django.core.urlresolvers import', 'from django.urls import'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


for pkg_name in packages:
    try:
        pkg = __import__(pkg_name)
    except ImportError:
        print(f"Skipping {pkg_name} (not installed)")
        continue

    pkg_dir = pathlib.Path(pkg.__file__).parent
    for py_file in pkg_dir.glob('**/*.py'):
        text = py_file.read_text()
        patched = patch_on_delete(text)
        patched = patch_subfieldbase(patched)
        patched = patch_django3_imports(patched)
        if patched != text:
            py_file.write_text(patched)
            print(f"Patched: {py_file}")
