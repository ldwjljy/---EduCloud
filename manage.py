#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pymysql

# Configure pymysql to ignore cryptography requirement for legacy auth
pymysql.install_as_MySQLdb()
import MySQLdb as Database
Database.__version__ = "2.2.1"


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduCloud.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
