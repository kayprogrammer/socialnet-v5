from app.api.utils.file_processors import ALLOWED_FILE_TYPES, ALLOWED_IMAGE_TYPES


def validate_image_type(value):
    if value and value not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Image type not allowed!")
    return value


def validate_file_type(value):
    if value and value not in ALLOWED_FILE_TYPES:
        raise ValueError("File type not allowed!")
    return value
