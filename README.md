# Look up various dictionaries

## Supports

- Merriam-Webster Collegiate® Dictionary with Audio (a [developer API key](https://dictionaryapi.com) required)
- Urban Dictionary
- Google Translate

## Usage

- `command + l`: Show word definitions in large type.
- `command + c`: Copy current word.
- `command + return`: For M-W Dictionary, pronounce current word (using QuickTime Player) if there's a speaker icon beside the word; otherwise, pronounce current word using system voice.
- `return`: Open current word in browser.

## Dependencies

- `python>=3.7`
- [`requests`](https://requests.readthedocs.io/en/latest/)
- [`fake-useragent`](https://fake-useragent.readthedocs.io/en/latest/)

Optional:

- [`mpg123`](https://www.mpg123.de): Used to pronounce M-W words. If not installed, will fall back to calling QuickTime Player through `osascript`.

## Installation

1. Clone the repository to `/path/to/repo`.
2. (Recommended) Create a virtualenv under `/path/to/repo`, e.g., named `venv`, and activate it:

```bash
python3 -m virtualenv venv
. venv/bin/activate
```

3. Install the dependencies and install the source code:

```bash
pip install -r requirements.txt
pip install .
```

4. Check out current Python runtime and copy to clipboard:

```bash
which python3 | tr -d '\n' | pbcopy
```

5. Double-click the alfredworkflow file `Dictionaries.alfredworkflow` to install it.
6. When configuring the workflow, paste the Python runtime to the `Python Runtime` field.
7. Continue configuring the workflow to your need.

## See also

- [YoudaoTranslate | 有道翻译](https://github.com/wensonsmith/YoudaoTranslator)
- [whyliam.workflows.youdao](https://github.com/whyliam/whyliam.workflows.youdao)
- [Alfred 查词扩展](https://github.com/liberize/alfred-dict-workflow)
