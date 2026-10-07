from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator

phone_validator = RegexValidator(
    regex=r"^\+998\d{9}$",
    message="Telefon raqami +998XXXXXXXXX ko‘rinishida bo‘lishi kerak.",
)

image_extension_validator = FileExtensionValidator(allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS)


def validate_image_size(f):
    if f.size > settings.MAX_UPLOAD_SIZE:
        mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(f"Fayl hajmi {mb} MB dan oshmasligi kerak.")


IMAGE_VALIDATORS = [image_extension_validator, validate_image_size]


def normalize_phone(raw):
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if len(digits) == 9:
        digits = "998" + digits
    return "+" + digits if digits else ""
