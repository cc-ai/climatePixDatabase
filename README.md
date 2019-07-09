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

Script will:
1) download all uploads info in `public` collection,
2) print number of uploads in `public` collection,
3) download first image from first upload,
4) print path where downloaded image is stored.
   Path will be like `public/<uploadID>/<imageID>.<imageExtension>` in the folder where script was
   executed. Check function `main()` in script to see how to change save path.
