# climatePixDatabase

Script to help manage ClimatePix database stored in Firebase. Current code can be used to
download all images and associated images metadata. See function `main()` in `firebase.py`
for an usage example.

# How to run

1) Install `firebase-admin`:
   ```
   pip install firebase-admin
   ```
2) Ask project owner to get credentials file `credentials.json`
   and place it in same folder as `firebase.py`.
3) Run script  `firebase.py`:
   ```
   python firebase.py
   ```

# Tutorial

The script provide classes
`Firebase` (database management),
`UploadInfo` (data about an upload batch stored in database)
and `ImageInfo` (paths and metadata about an images from an upload)
to get access to data stored in Firebase. Please see `main()` function
in `firebase.py` to get examples of how to use these classes.
