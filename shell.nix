{ pkgs ? import <nixpkgs> {} }:


let 
  system = builtins.currentSystem;
  venvDir = ".venv-${system}";
in


pkgs.mkShell {
  name = "tkinter-pynput";

  buildInputs = [
    pkgs.python312
    pkgs.python312Packages.tkinter
    pkgs.python312Packages.pynput
    pkgs.tk
    pkgs.geckodriver
  ];

  shellHook = ''
    export VENVDIR=".venv-${system}"
    if [ ! -d "${venvDir}" ]; then
      ${pkgs.python312.interpreter} -m venv ${venvDir}
    fi
    source ${venvDir}/bin/activate
    pip install -r requirements.txt
    # zsh
  '';
}