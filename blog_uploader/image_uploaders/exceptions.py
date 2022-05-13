class ImageUploaderException(Exception):
    pass


class S3UploaderException(ImageUploaderException):
    pass


class ChecksumMismatch(S3UploaderException):
    pass
