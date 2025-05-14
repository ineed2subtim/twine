# Linux specific commands:

## Tested system parameters
```
OS version: Ubuntu 20.04.6 LTS 
Kernel version: 5.4.0-167-generic
```

## Check Python3 version

Check your Python3 version. If it is less than 3.10 you need to upgrade. <br>
```
bash-3.2$ python3 --version 
Python 3.10.14
```

## Upgrading Python version if version <3.10

```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10
```

## Selecting Python 3.10 as default Python version

```
sudo update-alternatives --config python3			--> 	update-alternatives for python3	
```

