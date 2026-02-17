"""Patch installed packages to add missing on_delete to ForeignKey/OneToOneField for Django 3 compat."""
import re
import pathlib

packages = ['djangoplugins', 'popolo', 'popolo_sources']

for pkg_name in packages:
    try:
        pkg = __import__(pkg_name)
    except ImportError:
        print(f"Skipping {pkg_name} (not installed)")
        continue

    pkg_dir = pathlib.Path(pkg.__file__).parent
    for py_file in pkg_dir.glob('**/*.py'):
        text = py_file.read_text()
        original = text

        # Match ForeignKey(...) and OneToOneField(...) without on_delete
        for field_type in ['ForeignKey', 'OneToOneField']:
            pattern = rf'(models\.{field_type}\([^)]*)\)'
            def add_on_delete(m):
                inner = m.group(1)
                if 'on_delete' in inner:
                    return m.group(0)
                if 'null=True' in inner:
                    return inner + ', on_delete=models.SET_NULL)'
                return inner + ', on_delete=models.CASCADE)'
            text = re.sub(pattern, add_on_delete, text)

        if text != original:
            py_file.write_text(text)
            print(f"Patched: {py_file}")
