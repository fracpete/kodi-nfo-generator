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

## Installation

You can install the tool with pip as follows:

```
pip install kodi-nfo-generator
```

## Command-line

The following parameters can be supplied to the `kodi-nfo-gen` tool:

```
usage: kodi-nfo-gen [-h] --dir DIR [--type {imdb}] [--recursive]
                    [--pattern GLOB] [--delay SECONDS]
                    [--preferred_language LANG]
                    [--fanart {none,download,use-existing}]
                    [--fanart_file FILE] [--dry_run] [--overwrite] [--verbose]
                    [--debug]

Generates Kodi .nfo files with information retrieved from IMDB using local
files with the unique IMDB movie ID.

optional arguments:
  -h, --help            show this help message and exit
  --dir DIR             the directory to traverse (default: None)
  --type {imdb}         what type of ID the movie ID files represent, ie the
                        website they are from (default: imdb)
  --recursive           whether to traverse the directory recursively
                        (default: False)
  --pattern GLOB        the pattern for the files that contain the movie IDs
                        (default: *.imdb)
  --delay SECONDS       the delay in seconds between web queries (to avoid
                        blacklisting) (default: 1)
  --preferred_language LANG
                        the preferred language for the titles (ISO 639-1, see
                        https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
                        (default: en)
  --fanart {none,download,use-existing}
                        how to deal with fan-art (default: none)
  --fanart_file FILE    when downloading or using existing fanart, use this
                        filename (default: folder.jpg)
  --dry_run             whether to perform a 'dry-run', ie only outputting the
                        .nfo content to stdout but not saving it to files
                        (default: False)
  --overwrite           whether to overwrite existing .nfo files, ie
                        recreating them with freshly retrieved data (default:
                        False)
  --verbose             whether to output logging information (default: False)
  --debug               whether to output debugging information (default:
                        False)
```

## Example

Assuming your movies are structured like this:

```
movies
|
+- Metropolis
|  |
|  +- Metropolis.mp4
|  |
|  +- Metropolis.imdb   # content: tt0017136
|
+- Spies
|  |
|  +- Spies.mkv
|  |
|  +- Spies.imdb   # content: https://www.imdb.com/title/tt0019415/?ref_=nm_knf_i2
|
+- movies
   |
   +- Nosferatu.mp4
   |
   +- Nosferatu.imdb   # content: tt0013442
   |
   +- Sunrise.mp4
   |
   +- Sunrise.imdb   # content: tt0018455
```

And for each movie an `.imdb` file with either the unique IMDB ID
or the full IMDB URL is present.

Then you can the tool for generating the `.nfo` files like this:

```
kodi-nfo-gen \
  --dir ./movies \
  --recursive \
  --verbose
```

If you also want to download fan art (e.g., as `folder.jpg`), then 
you can use the following command-line:

```
kodi-nfo-gen \
  --dir ./movies \
  --recursive \
  --fanart download \
  --verbose
```  
