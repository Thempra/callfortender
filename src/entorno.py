# app/data_validation/__init__.py

from .validators import EmailValidator, PasswordValidator


# app/data_validation/validators.py

import re
from typing import Optional


class EmailValidator:
    """
    Validator for email addresses.
    """

    def __init__(self, email: str):
        """
        Initialize the EmailValidator with an email address.

        :param email: The email address to validate.
        """
        self.email = email

    def is_valid(self) -> bool:
        """
        Check if the email address is valid.

        :return: True if the email is valid, False otherwise.
        """
        return re.match(r"[^@]+@[^@]+\.[^@]+", self.email) is not None


class PasswordValidator:
    """
    Validator for passwords.
    """

    def __init__(self, password: str):
        """
        Initialize the PasswordValidator with a password.

        :param password: The password to validate.
        """
        self.password = password

    def is_valid(self) -> bool:
        """
        Check if the password meets all validation criteria.

        :return: True if the password is valid, False otherwise.
        """
        return (
            len(self.password) >= 8 and
            self._has_uppercase() and
            self._has_lowercase() and
            self._has_digit() and
            self._has_special_character()
        )

    def _has_uppercase(self) -> bool:
        """
        Check if the password contains at least one uppercase letter.

        :return: True if there is an uppercase letter, False otherwise.
        """
        return any(c.isupper() for c in self.password)

    def _has_lowercase(self) -> bool:
        """
        Check if the password contains at least one lowercase letter.

        :return: True if there is a lowercase letter, False otherwise.
        """
        return any(c.islower() for c in self.password)

    def _has_digit(self) -> bool:
        """
        Check if the password contains at least one digit.

        :return: True if there is a digit, False otherwise.
        """
        return any(c.isdigit() for c in self.password)

    def _has_special_character(self) -> bool:
        """
        Check if the password contains at least one special character.

        :return: True if there is a special character, False otherwise.
        """
        return re.search(r"[!@#$%^&*(),.?\":{}|<>]", self.password) is not None


# app/data_validation/validation_service.py

from typing import Optional
from .validators import EmailValidator, PasswordValidator


class ValidationService:
    """
    Service for performing data validation tasks.
    """

    def validate_email(self, email: str) -> bool:
        """
        Validate an email address.

        :param email: The email address to validate.
        :return: True if the email is valid, False otherwise.
        """
        validator = EmailValidator(email)
        return validator.is_valid()

    def validate_password(self, password: str) -> bool:
        """
        Validate a password.

        :param password: The password to validate.
        :return: True if the password is valid, False otherwise.
        """
        validator = PasswordValidator(password)
        return validator.is_valid()