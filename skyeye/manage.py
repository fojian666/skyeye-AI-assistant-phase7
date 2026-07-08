#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtus.settings')
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
    print("""
__        _______ _     ____ ___  __  __ _____   _____ ___     ____ _____ _   _ ____  
\ \      / / ____| |   / ___/ _ \|  \/  | ____| |_   _/ _ \   / ___|_   _| | | / ___| 
 \ \ /\ / /|  _| | |  | |  | | | | |\/| |  _|     | || | | | | |  _  | | | | | \___ \ 
  \ V  V / | |___| |__| |__| |_| | |  | | |___    | || |_| | | |_| | | | | |_| |___) |
   \_/\_/  |_____|_____\____\___/|_|  |_|_____|   |_| \___/   \____| |_|  \___/|____/    v1.1
                                                                                      
    """)
    main()
