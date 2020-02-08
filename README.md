# kodi-nfo-generator
The **kodi-nfo-generator** is a simple Python-based command-line
tool that allows you to generate [.nfo](https://kodi.wiki/view/NFO_files/Movies) 
files for movies that [Kodi](https://kodi.tv/) can use for its library.

This tool is aimed at people that manually curate their movie databases, in order
to avoid using scrapers that may pull in the wrong information (or none at all).
All the user has to do is place an ID file alongside their movie files,
the default is `*.imdb`, containing the unique IMDB movie ID (or full IMDB movie URL).
The tool will then scour the movie directories for these files and pull in the
information and create the `.nfo` files in the same location.

## Command-line

```
usage: kodi-nfo-gen [-h] --dir dir [--type {imdb}] [--recursive]
                    [--pattern glob] [--delay delay]
                    [--preferred_language lang]
                    [--fanart {none,download,use-existing}]
                    [--fanart_file fanart_file] [--dry_run] [--overwrite]
                    [--verbose] [--debug]

Generates Kodi .nfo files with information retrieved from IMDB using local
files with the unique IMDB movie ID.

optional arguments:
  -h, --help            show this help message and exit
  --dir dir             the directory to traverse
  --type {imdb}         what type of ID the movie ID files represent, ie the
                        website they are from
  --recursive           whether to traverse the directory recursively
  --pattern glob        the pattern for the files that contain the movie IDs
  --delay delay         the delay in seconds between web queries (to avoid
                        blacklisting)
  --preferred_language lang
                        the preferred language for the titles (ISO 639-1, see
                        https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
  --fanart {none,download,use-existing}
                        how to deal with fan-art
  --fanart_file fanart_file
                        when downloading or using existing fanart, use this
                        filename
  --dry_run             whether to perform a 'dry-run', ie only outputting the
                        .nfo content to stdout but not saving it to files
  --overwrite           whether to overwrite existing .nfo files, ie
                        recreating them with freshly retrieved data
  --verbose             whether to output logging information
  --debug               whether to output debugging information
```
