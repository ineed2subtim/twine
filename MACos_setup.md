# MAC OS specific commands

## Mac Tested system parameters
```
OS version: MacOS Sonoma 14.5
Kernel version: Darwin Kernel Version 23.5.0
```

## Mac specific python guide
This guide assumes you are using `homebrew` to install and update python. If you are using something different then you will need to look up the equivalent commands in your chosen tool. <br>

To install `python 3.10` version you can run ```brew install python@3.10```
This will not replace your original version, it will simply install version 3.10 in addition, so if you run `python3 ...` you will still run things in your original python version. However, when running pip or python programs, as we do in this readme, you can specify a version by calling `pip3.10` or `python3.10` instead of `pip3` and `python3`. 
For example: `pip3.10 install virtualenv virtualenvwrapper` <br>

If you wanted to completely replace your version then you would also have to update your shell profile. Alternativly, you could use a tool like `pyenv` which lets you set python version locally and globally as you wish, providing more control over your environment. <br>

