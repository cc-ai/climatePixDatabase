# climatePixDatabase

Module `climatepixdb` helps manage ClimatePix database stored in Firebase. Available scripts:
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

You can also install it as an editable module:
```
pip install -e .
```

4\) Ask project owner for credentials file `credentials.json`
and place it in folder where you want to execute the script (e.g. `my_images`).

**update (2019/09/10)**: Backend Firebase account was changed. If you used a credentials file obtained
before 2019/09/10, you should ask for a new one to a project owner.

5\) Move into your working folder, where `credentials.json` is available.
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

11\) Examples to delete all invalid uploads in database. An invalid upload is an upload with no
associated images. Such cases may occur, for example if a user starts an upload but closes the
browser before upload was terminated. So, it may be useful to regularly clean database using
following command:
```bash
# Clean public collection
python -m climatepixdb.delete --invalid

# Clean dev collection
python -m climatepixdb.delete --invalid --dev
```

# Reference

For API programming, see documentation strings in module `climatepixdb`.
