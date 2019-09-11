class UploadError(Exception):
    """ Specific upload exception raised if a upload document from database is invalid. """


class CredentialsError(Exception):
    def __init__(self, file_name):
        super(CredentialsError, self).__init__(
"""
-----------------------------------------------
MISSING CREDENTIALS FILE TO CONNECT TO DATABASE
-----------------------------------------------
Credentials file %s not found in working directory.
If you have this file, either place it here or execute your script where the file is stored.
Otherwise, please contact CCAI project members to get a copy of this file.
Thanks!
""" % file_name
        )
