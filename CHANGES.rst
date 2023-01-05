Changelog
=========

0.0.9 (2023-01-06)
------------------

- using `download-missing` no longer generates `Ignoring unhandled fanart type: download-missing`
  message when fanart already present (just an output bug).
- improved checks for existing `.nfo` files to reduce IMDB requests
- added `kodi-nfo-rename` tool for renaming files using regular expressions
  (e.g., files of TV shows)
- the `kodi-nfo-gen` tool now has additional options for matching episode files
  rather than using hardcoded defaults: `--episode_pattern`, `--season_group`,
  `--episode_group`.


0.0.8 (2023-01-04)
------------------

- added `kodi-nfo-guess` tool that performs online database searches for directories
  that miss meta-files, like `.imdb`, which the `kodi-nfo-gen` tool uses as input.


0.0.7 (2023-01-03)
------------------

- adding `user-agent` to request headers now (https://github.com/fracpete/kodi-nfo-generator/pull/6)
- only making IMDB request when `--overwrite` flag present or `.nfo` not present, to avoid making
  too many calls to IMDB
- the `--delay` no longer applies when not writing a file
- fixed TV show .nfo generation (https://github.com/fracpete/kodi-nfo-generator/issues/1)
- added `download-missing` choice for downloading fanart only when it is missing locally
  (`download` always performs a download)


0.0.6 (2022-08-18)
------------------

- not all movie meta-data contains the `actor` field, now checking whether present
  (https://github.com/fracpete/kodi-nfo-generator/pull/4)


0.0.5 (2021-11-06)
------------------

- `setup.py` excludes versions of beautifulsoup that don't work
  (https://github.com/fracpete/kodi-nfo-generator/issues/2)
- added experimental support for generating .nfo output for TV series episodes
  (https://github.com/fracpete/kodi-nfo-generator/issues/1)


0.0.4 (2021-05-29)
------------------

- ratingValue is now set as string, not float; better handling when 
  preflang_title not available


0.0.3 (2021-03-11)
------------------

- restricting beautifulsoup version to <=4.6.0 as newer versions fail:
  https://github.com/fracpete/kodi-nfo-generator/issues/2


0.0.2 (2020-02-09)
------------------

- added ability to export movie IDs to a CSV file using `kodi-nfo-export`
- added ability to import movie IDs from a CSV file using `kodi-nfo-import`
- `kodi-nfo-gen` now handles movies that only have limited information available
  (e.g., no plot or no image)
- added interactive mode to tools (`--interactive`)


0.0.1 (2020-02-08)
------------------

- initial release, only supports IMDB for the time being
