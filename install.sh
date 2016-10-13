#!/bin/bash

python -c "import pystr" 2> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing pysrt."
    sudo apt-get install python-pysrt
fi

sudo install horus.py /usr/bin/horus
install nautilus_script "$HOME/.local/share/nautilus/scripts/Download Subtitles"
