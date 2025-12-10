"""
With these settings, tests run faster.
"""

import os

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="M4z4A5d3vE1AaLWVWhCpPb1dMTDGsqoh5e0VxWG4TH4SPt3lhSqF4krfRw9L8sAy",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DATABASE
# ------------------------------------------------------------------------------
# Default to SQLite for local test runs to avoid requiring Postgres.
DATABASES["default"] = env.db("DATABASE_URL", default="sqlite:///db.sqlite3")

# CACHES
# ------------------------------------------------------------------------------
# Use in-memory cache during tests to avoid external Redis dependency.
CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "test-locmem",
}

# CELERY
# ------------------------------------------------------------------------------
# Use eager execution with in-memory broker/backend for tests.
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_BROKER_TRANSPORT_OPTIONS = {}

# Mark environment as testing for conditional shortcuts
TESTING = True

# S3 test config (avoid network calls in local runs)
S3_TEST_ENDPOINT = "memory://"
S3_TEST_KEY = "test"
S3_TEST_SECRET = "test"
S3_TEST_BUCKET = "ami-test"
S3_TEST_PUBLIC_BASE_URL = "http://example.com/test_prefix"

if S3_TEST_ENDPOINT.startswith("memory://"):
    from ami.utils import s3 as _s3

    _IN_MEMORY_S3: dict[str, dict[str, bytes]] = {}

    def _store(config: _s3.S3Config) -> dict[str, bytes]:
        return _IN_MEMORY_S3.setdefault(config.bucket_name, {})

    def _full_key(config: _s3.S3Config, key: str, subdir: str | None = None) -> str:
        return _s3.key_with_prefix(config, key, subdir=subdir).lstrip("/")

    def _list_files(
        config: _s3.S3Config,
        limit: int | None = 100000,
        subdir: str | None = None,
        regex_filter: str | None = None,
        file_extensions: list[str] = _s3.IMAGE_FILE_EXTENSIONS,
    ):
        regex = _s3._compile_regex_filter(regex_filter)
        prefix = _s3.make_full_prefix(config, subdir).lstrip("/")
        items = [(key, body) for key, body in _store(config).items() if not prefix or key.startswith(prefix)]
        count = 0
        for key, body in sorted(items):
            count += 1
            if _s3._filter_single_key(key, obj_size=len(body), regex=regex, file_extensions=file_extensions):
                yield {"Key": key, "Size": len(body)}, count
            if limit and count >= limit:
                break
        yield None, count

    def _write_file(config: _s3.S3Config, key: str, body: bytes):
        _store(config)[_full_key(config, key)] = body
        return {"Key": _full_key(config, key), "Size": len(body)}

    def _read_file(config: _s3.S3Config, key: str) -> bytes:
        return _store(config)[_full_key(config, key)]

    def _file_exists(config: _s3.S3Config, key: str) -> bool:
        return _full_key(config, key) in _store(config)

    def _create_bucket(config: _s3.S3Config, bucket_name: str, exists_ok: bool = True):
        _IN_MEMORY_S3.setdefault(bucket_name, {})
        return None

    _s3.list_files = _list_files  # type: ignore[assignment]
    _s3.list_files_paginated = _list_files  # type: ignore[assignment]
    _s3.write_file = _write_file  # type: ignore[assignment]
    _s3.read_file = _read_file  # type: ignore[assignment]
    _s3.file_exists = _file_exists  # type: ignore[assignment]
    _s3.create_bucket = _create_bucket  # type: ignore[assignment]

# For SQLite test runs, relax postgres-only field constraints
if DATABASES["default"].get("ENGINE", "").endswith("sqlite3"):
    from django.contrib.postgres.fields import ArrayField

    ArrayField.check = lambda *args, **kwargs: []  # type: ignore[assignment]
    ArrayField.db_type = lambda self, connection: "text"  # type: ignore[assignment]

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore # noqa: F405
# Your stuff...
# ------------------------------------------------------------------------------
