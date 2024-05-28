from tortoise.exceptions import ValidationError

def not_negative(value):
    if value < 0:
        raise ValidationError("Value must be greater than or equal to zero.")