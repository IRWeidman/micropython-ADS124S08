# micropython-ADS124S08 Examples

## Getting started

All example scripts in this folder will use [`hwconfig.py`](hwconfig.py) to define any hardware-dependent code. To use the examples, simply edit the definitions in [`hwconfig.py`](hwconfig.py) to match your board/setup, then copy both [`hwconfig.py`](hwconfig.py) and the example script you want to try to your board (don't forget [`ads123s08.py`](../ads124s08.py)!).

The final directory should look something like this:

```
.
├── lib/
│   └── ...
├── ads124s08.py
├── hwconfig.py
├── simple_scan.py
└── main.py (optional)
```

Once the scripts are uploaded, simply run them by importing the example script through the repl or main.py.

``` python
import simple_scan.py
```
