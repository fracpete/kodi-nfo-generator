Changelog
=========

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
