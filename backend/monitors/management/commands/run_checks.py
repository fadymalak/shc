from django.core.management.base import BaseCommand
from monitors.tasks import check_all_monitors


class Command(BaseCommand):
    help = 'Run checks for all active monitors'

    def handle(self, *args, **options):
        self.stdout.write('Running checks for all monitors...')
        check_all_monitors.delay()
        self.stdout.write(self.style.SUCCESS('Checks queued successfully'))
