# LANPONG
https://github.com/pedramhaqiqi/LANPONG/assets/63091219/94362195-b21c-49c3-a09c-767df601e6fd


## Try Out!:
  - Create a new account using ```ssh new@lanpong.hopto.me -p 2222```
  - Login using created account ```ssh 'username'@lanpong.hopto.me -p 2222```

## Setup

### Requirements

- This project assumes you're using a Unix-like system (Linux, macOS, WSL, etc.)
- `python3` in your terminal should point to a `python>=3.10` installation.
- `pip` shuold be installed on your python version.

### Installation

Upgrade `pip` to the latest version:
```bash
python3 -m pip install --upgrade pip
```

Install `poetry`:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

You will be instructed to add `poetry` to your `PATH` variable.
Make sure to do this, then restart your terminal.

From within the project directory (the one containing this file), install the project dependencies, and the project itself:
```bash
poetry install
```

## Usage

Finally (again, from within the project directory), run the following command:
```bash
$ python -m lanpong
```

This will immediatly start the LANPONG SSH server.
You should see the following output:

```
Listening for connection on 0.0.0.0:2222
```

You can now connect to the server using the following command:
```bash
$ ssh new@<server-ip> -p 2222
```

Once you create a new user, you can join as that user using the following command:
```bash
$ ssh <username>@<server-ip> -p 2222
```

## Production Server Domain (Online)
```bash
lanpong.hopto.me
```
