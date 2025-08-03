# PyPi

Preparation:

* update help screens (including sub-commands)
* check whether examples in `README.md` are still up-to-date
* increment version in `setup.py`
* add new changelog section in `CHANGES.rst`
* commit/push all changes

Commands for releasing on pypi.org:

```
find -name "*~" -delete
rm dist/*
python3 setup.py clean
python3 setup.py sdist
twine upload dist/*
```


# Github

Steps:

* start new release (version: `vX.Y.Z`)
* enter release notes, i.e., significant changes since last release
* upload `kodi_nfo_generator-X.Y.Z.tar.gz` previously generated with `setup.py`
* publish
