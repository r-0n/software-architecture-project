"""
Django management command to replay recorded HTTP requests for regression testing.
"""
import json
import os
import glob
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.contrib.auth.models import User
from django.conf import settings


class Command(BaseCommand):
    help = 'Replay recorded HTTP requests for regression testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            help='Directory containing recorded request files',
            default=getattr(settings, 'REQUEST_RECORD_DIR', 'recorded_requests')
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Specific file to replay'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='Pattern to match in file names'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare responses with original recordings'
        )
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Create test user for authenticated requests'
        )
        parser.add_argument(
            '--fail-fast',
            action='store_true',
            help='Stop on first mismatch'
        )

    def handle(self, *args, **options):
        record_dir = options['dir']
        specific_file = options['file']
        pattern = options['pattern']
        compare = options['compare']
        create_user = options['create_user']
        fail_fast = options['fail_fast']

        # Validate directory exists
        if not os.path.exists(record_dir):
            raise CommandError(f"Record directory does not exist: {record_dir}")

        # Get files to replay
        if specific_file:
            if not os.path.exists(specific_file):
                raise CommandError(f"File does not exist: {specific_file}")
            files_to_replay = [specific_file]
        else:
            files_to_replay = glob.glob(os.path.join(record_dir, '*.json'))
            if pattern:
                files_to_replay = [f for f in files_to_replay if pattern in f]

        if not files_to_replay:
            raise CommandError("No recorded request files found")

        # Create test user if requested
        if create_user:
            user, created = User.objects.get_or_create(
                username='testuser',
                defaults={'email': 'test@example.com'}
            )
            if created:
                user.set_password('testpass123')
                user.save()

        # Initialize test client
        client = Client()
        if create_user:
            client.force_login(user)

        # Replay requests
        mismatches = 0
        for file_path in files_to_replay:
            try:
                with open(file_path, 'r') as f:
                    record = json.load(f)
                
                request_data = record['request']
                original_response = record['response']
                
                # Replay the request
                if request_data['method'] == 'GET':
                    response = client.get(request_data['path'])
                elif request_data['method'] == 'POST':
                    post_data = request_data.get('post_data', {})
                    response = client.post(request_data['path'], post_data)
                else:
                    self.stdout.write(f"Skipping unsupported method: {request_data['method']}")
                    continue
                
                # Compare responses if requested
                if compare:
                    if response.status_code != original_response['status_code']:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Mismatch in {os.path.basename(file_path)}: "
                                f"Status {response.status_code} != {original_response['status_code']}"
                            )
                        )
                        mismatches += 1
                        if fail_fast:
                            raise CommandError("Mismatch detected, stopping due to --fail-fast")
                
                self.stdout.write(f"Replayed: {os.path.basename(file_path)}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error replaying {file_path}: {e}")
                )
                if fail_fast:
                    raise CommandError(f"Error during replay: {e}")

        # Summary
        if compare:
            if mismatches == 0:
                self.stdout.write(self.style.SUCCESS("All replays matched original responses"))
            else:
                self.stdout.write(
                    self.style.WARNING(f"Found {mismatches} mismatches")
                )
                raise CommandError(f"Regression detected: {mismatches} mismatches")
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully replayed {len(files_to_replay)} requests"))
