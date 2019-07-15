# climatePixDatabase

Module `climatepixdb/database.py` and script `climatepixdb/download.py`
to help manage ClimatePix database stored in Firebase.

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

6\) Script module is `climatepixdb.download`. You can use parameter `-h` to get full help.
```
python -m climatepixdb.download -h
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

# Reference

For API programming, see documentation strings in `climatepixdb/database.py`.
