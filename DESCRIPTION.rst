The **kodi-nfo-generator** is a simple Python-based command-line
tool that allows you to generate `.nfo <https://kodi.wiki/view/NFO_files/Movies>`_ 
files for movies that `Kodi <https://kodi.tv/>`_ can use for its library.

This tool is aimed at people that manually curate their movie databases, in order
to avoid using scrapers that may pull in the wrong information (or none at all).
All the user has to do is place an ID file alongside their movie files,
the default is `*.imdb`, containing the unique IMDB movie ID (or full IMDB movie URL).
The tool will then scour the movie directories for these files and pull in the
information and create the `.nfo` files in the same location.
