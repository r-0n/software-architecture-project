"""
Enhanced queue worker management command.
Includes automatic cleanup of expired reservations.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from worker.queue import QueuedJob, finalize_flash_order, cleanup_expired_reservations
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs the enhanced asynchronous job queue worker with reservation cleanup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup-interval',
            type=int,
            default=300,  # 5 minutes
            help='Interval in seconds for cleanup of expired reservations'
        )
        parser.add_argument(
            '--poll-interval',
            type=int,
            default=5,
            help='Interval in seconds for polling new jobs'
        )

    def handle(self, *args, **options):
        cleanup_interval = options['cleanup_interval']
        poll_interval = options['poll_interval']
        last_cleanup = time.time()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting enhanced queue worker...\n'
                f'Cleanup interval: {cleanup_interval}s\n'
                f'Poll interval: {poll_interval}s'
            )
        )
        
        while True:
            current_time = time.time()
            
            # Periodic cleanup of expired reservations
            if current_time - last_cleanup >= cleanup_interval:
                try:
                    cleanup_expired_reservations()
                    self.stdout.write(
                        self.style.SUCCESS(f'Cleaned up expired reservations at {timezone.now()}')
                    )
                    last_cleanup = current_time
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error during cleanup: {e}')
                    )
            
            # Process pending jobs
            job = QueuedJob.objects.filter(status='PENDING').order_by('created_at').first()
            
            if job:
                self.stdout.write(f'Processing job {job.id}: {job.job_type}')
                
                # Mark as processing
                job.status = 'PROCESSING'
                job.processed_at = timezone.now()
                job.save()
                
                try:
                    # Process the job
                    if job.job_type == 'finalize_flash_order':
                        finalize_flash_order(job.payload)
                    else:
                        raise ValueError(f"Unknown job type: {job.job_type}")
                    
                    # Mark as completed
                    job.status = 'COMPLETED'
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully processed job {job.id}')
                    )
                    
                except Exception as e:
                    # Mark as failed
                    job.status = 'FAILED'
                    job.error_message = str(e)
                    self.stdout.write(
                        self.style.ERROR(f'Failed to process job {job.id}: {e}')
                    )
                    
                    # Log the error
                    logger.error(f"Job {job.id} failed: {e}", exc_info=True)
                
                finally:
                    job.save()
            else:
                # No jobs to process, sleep
                time.sleep(poll_interval)
