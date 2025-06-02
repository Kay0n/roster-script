{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "tkinter-pynput";

  buildInputs = [
    pkgs.python312Full
    pkgs.python312Packages.tkinter
    pkgs.python312Packages.pynput
    pkgs.tk
  ];

  shellHook = ''
    VENV=.venv

    if test ! -d $VENV; then
      ${pkgs.python312.interpreter} -m venv $VENV
    fi
    source ./$VENV/bin/activate
    pip install -r requirements.txt
    zsh
  '';
}