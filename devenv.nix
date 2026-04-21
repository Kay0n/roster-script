# @autorun
{pkgs, ...}:
{

  dotenv.disableHint = true;

  languages.python = {
    enable = true;
    package = pkgs.python313;
    venv = {
      enable = true;
      requirements = ''
        openpyxl
        numpy
        selenium
        keyboard
        pytest
        python-dotenv
        pynput
      '';
    };
  };

  packages = [
    pkgs.python313Packages.pynput
    pkgs.geckodriver
  ];


  scripts.run.exec = ''
    python ./src/main.py
  '';
}
