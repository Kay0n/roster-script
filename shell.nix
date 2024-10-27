{ pkgs ? import <nixpkgs> {} }:
(pkgs.buildFHSUserEnv {
  name = "tkinter test";
  targetPkgs = pkgs: (with pkgs; [
    python310Full
    python310Packages.pip
    python310Packages.tkinter
    tk
  ]);
  runScript = "zsh";
}).env
# for tkinter on nixos