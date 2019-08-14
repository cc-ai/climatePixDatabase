# climatePixDatabase

Module `climatepixdb/database.py` provided to help manage ClimatePix database stored in Firebase. Available scripts:
- `climatepixdb/download`: helper to download images from database
- `climatepixdb/delete`: helper to delete images on database

# Tutorial

1\) Clone repository:
```
git clone https://github.com/cc-ai/climatePixDatabase.git
```

2\) Move into cloned repository.
```
cd climatePixDatabase/
```

3\) Install package using `pip`.
```
pip install .
```

4\) Ask project owner for credentials file `credentials.json`
and place it in folder where you want to execute the script (e.g. `my_images`).

5\) Move into your working folder, where `credentials.json` if available.
```
cd my_images
```

6\) Run a script. You can use parameter `-h` to get full help.
```
python -m climatepixdb.download -h
python -m climatepixdb.delete -h
```

7\) Example to download all public images grouped by category
into output folder `output_folder` while printing download info:
```
python -m climatepixdb.download --output output_folder --since all --categorize --verbose
```

8\) Example to download all public images (not grouped) uploaded since 10th of July, 2019
and store them into output folder `my_folder`; still print download info.
```
python -m climatepixdb.download --output my_folder --since 2019-07-10 --verbose
```

9\) Example to delete all development images uploaded after 10th of July, 2019.
```bash
python -m climatepixdb.delete --dev --after 2019-07-10
```

10\) Example to delete all public images uploaded before 10th of July, 2019.
```bash
python -m climatepixdb.delete --before 2019-07-10
```

# Reference

For API programming, see documentation strings in `climatepixdb/database.py`.
