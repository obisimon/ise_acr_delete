# Delete Sponsor Portal users at ISE (and probably other ISE tasks)

Scripts to delete ISE Sponsor Portal Users

## Install
using python 3.10, checkout [pyenv](https://github.com/pyenv/pyenv)

### use poetry:
```
poetry install
poetry shell
```
### plain:
```
pip install -r /path/to/requirements.txt
```

### settings and credentials

```
cp settings.py.dist settings.py
cp credentials.py.dist credentials.py
```

adjust the settings and credentials


## Usage
```
python ./ise.py  delete-sponsor-accounts --help
Usage: ise.py delete-sponsor-accounts [OPTIONS]

  Delete Sponsor Accounts

Options:
  -f, --filter TEXT      ISE Filter options to select which sponsor accounts
                         should be deleted
  --regex-username TEXT  Regular expression to match the usernames
  --regex-email TEXT     Regular expression to match the usernames
  --confirm              Confirm to really delete the sponsor accounts and
                         endpoints
  --endpoints            Include endpoints of the sponsor accounts
  --help                 Show this message and exit.

``` 