# climatePixDatabase

Module `climate_pix_database.py` to help manage ClimatePix database stored in Firebase.
Current code can be used to download all images and associated images metadata.
See `script.py` for usage examples.

# How to run

1) Install `firebase-admin`:
   ```
   pip install firebase-admin
   ```
2) Ask project owner to get credentials file `credentials.json`
   and place it in folder where you want to use this module.
3) Test module by running script `script.py`:
   ```
   python script.py
   ```

# Tutorial

The module `climate_pix_database.py` provide classes
`ClimatePixDatabase` (database management),
`UploadInfo` (data about an upload batch stored in database)
and `ImageInfo` (paths and metadata about an images from an upload)
to get access to data stored in Firebase. Please see script file
`script.py` to get examples of how to use these classes.
