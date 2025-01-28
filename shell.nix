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
    zsh
    source .venv/bin/activate
  '';
}