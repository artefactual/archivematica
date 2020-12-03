# -*- coding: utf-8 -*-

"""Settings for basic user authentication."""

from settings.base import config

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": config.get("password_minimum_length")},
    }
]

DISABLE_PASSWORD_COMMON_VALIDATION = config.get("password_disable_common_validation")
if not DISABLE_PASSWORD_COMMON_VALIDATION:
    AUTH_PASSWORD_VALIDATORS.append(
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}
    )

DISABLE_PASSWORD_USER_ATTRIBUTE_SIMILARITY_VALIDATION = config.get(
    "password_disable_user_attribute_similarity_validation"
)
if not DISABLE_PASSWORD_USER_ATTRIBUTE_SIMILARITY_VALIDATION:
    AUTH_PASSWORD_VALIDATORS.append(
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        }
    )

DISABLE_PASSWORD_COMPLEXITY_VALIDATION = config.get(
    "password_disable_complexity_validation"
)
if not DISABLE_PASSWORD_COMPLEXITY_VALIDATION:
    AUTH_PASSWORD_VALIDATORS.append(
        {"NAME": "components.accounts.validators.PasswordComplexityValidator"}
    )
