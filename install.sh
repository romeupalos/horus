#!/bin/bash

python -c "import pysrt" 2> /dev/null
if [ "$?" -ne 0 ]; then
    echo "Installing pysrt."
    sudo apt-get install python-pysrt
fi

echo "Installing horus to /usr/bin"
sudo install horus.py /usr/bin/horus

echo "Installing nautilus script"
install nautilus_script "$HOME/.local/share/nautilus/scripts/Download Subtitles"

echo "Done."
