import os
import sys

from django.core.management import BaseCommand, ManagementUtility
from django.conf import settings


class Command(BaseCommand):
    help = """run async job"""

