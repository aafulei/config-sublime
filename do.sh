#!/bin/bash

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
DEST="$HOME/Library/Application Support/Sublime Text 3/Packages"
ROOT="$HOME/Library/Application Support/Sublime Text 3"
KEY_FILE="User/Default (OSX).sublime-keymap"
SET_FILE="User/Preferences.sublime-settings"
PAC_FILE="User/Package Control.sublime-settings"
LINE=$(printf -- "-%.0s" {1..100})

# interactive copy: diff, copy, view
icopy() {
    local result
    local status
    local answer
    local dir_to

    echo $LINE
    echo "[From < ] $1"
    echo "[To   > ] $2"
    echo $LINE

    result=$(diff "$1" "$2" 2>&1)
    status=$?

    if [ $status -eq 0 ]; then
        echo "Files are the same."
    elif [ $status -eq 1 ]; then
        echo "Files are different."
        echo $LINE
        echo "$result"
        echo $LINE
        if [ "$3" != "diff" ]; then
            read -p "Do you want to overwrite? [y/N] " answer
            case ${answer:0:1} in
                y|Y)
                    echo "Moving $2 to $2.old ..." && mv "$2" "$2.old"
                    echo "Copying $1 to $2 ..." && cp "$1" "$2"
                    ;;
                *)
                    ;;
            esac
        fi
    else
        if [ ! -e "$1" ]; then
            echo "$1 does not exist!"
            exit
        fi
        if [ ! -e "$2" ]; then
            echo "$2 does not exist ..."
            if [ "$3" != "diff" ]; then
                dir_to=$(dirname "$2")
                if [ ! -d $dir_to ]; then
                    echo "Making directory $dir_to ..." && mkdir -p $dir_to
                fi
                echo "Copying $1 to $2 ..." && cp "$1" "$2"
            fi
        fi
    fi

    if [ -e "$2" ]; then
        read -p "Do you want to view $2? [y/N] " answer
        case ${answer:0:1} in
            y|Y)
                cat "$2"
                ;;
            *)
                ;;
        esac
    fi
}

# copy source directory to destination
clone() {
    echo $LINE
    echo "[Source       ] $SRC"
    echo "[Destination  ] $DEST"
    echo $LINE

    if [ ! -d "$ROOT" ]; then
        echo "$ROOT does not exist!"
        echo "Please run Sublime Text 3 once and the directory shall be automatically created."
        exit
    fi

    if [ ! -f "$ROOT/Installed Packages/Package Control.sublime-package" ]; then
        echo "Please make sure Package Control has been installed in Sublime Text 3."
        exit
    fi

    if [ -e "$DEST" ]; then
        if [ -e "$DEST.old" ]; then
            echo "Removing $DEST.old ..." && rm -rf "$DEST.old"
        fi
        echo "Moving $DEST to $DEST.old ..." && mv "$DEST" "$DEST.old"
    fi
    echo "Copying $SRC to $DEST ..." && cp -r "$SRC" "$DEST"
}

show_help() {
    echo "$LINE
[Source       ] $SRC
[Destination  ] $DEST
[Target File 1] $KEY_FILE
[Target File 2] $SET_FILE
[Target File 3] $PAC_FILE
$LINE
--help      show this message and exit
--diff      compare target file(s) between source and destination
--push      copy target file(s) from source to destination
--pull      copy target file(s) from destination to source
--clone     copy entire source directory to destination
$LINE"
}

main() {
    if [ $# -eq 0 ]; then
        show_help
    else
        case "$1" in
            "--diff")
                icopy "$SRC/$KEY_FILE" "$DEST/$KEY_FILE" "diff"
                icopy "$SRC/$SET_FILE" "$DEST/$SET_FILE" "diff"
                icopy "$SRC/$PAC_FILE" "$DEST/$PAC_FILE" "diff"
                ;;
            "--push")
                icopy "$SRC/$KEY_FILE" "$DEST/$KEY_FILE" "push"
                icopy "$SRC/$SET_FILE" "$DEST/$SET_FILE" "push"
                icopy "$SRC/$PAC_FILE" "$DEST/$PAC_FILE" "push"
                ;;
            "--pull")
                icopy "$DEST/$KEY_FILE" "$SRC/$KEY_FILE" "pull"
                icopy "$DEST/$SET_FILE" "$SRC/$SET_FILE" "pull"
                icopy "$DEST/$PAC_FILE" "$SRC/$PAC_FILE" "pull"
                ;;
            "--clone")
                clone
                ;;
            *)
                show_help
                ;;
        esac
    fi
}

main "$@"
