# xpymenu
A dynamic menu inspired by dmenu for X11 written in Python.

## Dependencies

Python 3.1+.

## Usage

Display items in a window:

```bash
python3 xpymenu.py foo bar test
```

## Installation

Clone this repository and
```
git clone https://github.com/Irreq/xpymenu.git


```
Go to the directory:
```
cd xpymenu
```
Copy `xpymenu` to somewhere in your `$PATH`:
```
cp xpymenu /usr/local/bin
```

## Keyboard

The menu should be self-explainatory, and pressing any other key than the regular alphabetical keys quits the program as it prohibits you from typing anywhere else.

- `Left`, `Right`: move the cursor.
- `Esc`: quit without selecting an item.
- `Return`: select an item.
