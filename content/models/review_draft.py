import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class ReviewDraft(models.Model):
    """
    Temporary storage for in-progress review submissions.
    Drafts are automatically excluded if older than 7 days.
    """
    # Use UUID as primary key for security
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Owner of the draft
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_drafts',
        help_text="User who created this draft"
    )

    # Current step in the review flow
    step = models.CharField(
        max_length=50,
        default='basic-info',
        help_text="Current step ID in the review modal"
    )

    # Form data stored as JSON
    data = models.JSONField(
        default=dict,
        help_text="All form data including basic info, location, rating, and dishes"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Review Draft'
        verbose_name_plural = 'Review Drafts'
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"Draft by {self.user.username} - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_expired(self):
        """Check if draft is older than 7 days."""
        expiration_date = timezone.now() - timedelta(days=7)
        return self.updated_at < expiration_date

    @property
    def age_display(self):
        """Human-readable age of the draft."""
        now = timezone.now()
        delta = now - self.updated_at

        if delta.days > 0:
            if delta.days == 1:
                return "1 day ago"
            return f"{delta.days} days ago"

        hours = delta.seconds // 3600
        if hours > 0:
            if hours == 1:
                return "1 hour ago"
            return f"{hours} hours ago"

        minutes = delta.seconds // 60
        if minutes > 0:
            if minutes == 1:
                return "1 minute ago"
            return f"{minutes} minutes ago"

        return "Just now"

    @classmethod
    def get_latest_for_user(cls, user):
        """
        Get the most recent non-expired draft for a user.
        Returns None if no valid draft exists.
        """
        expiration_date = timezone.now() - timedelta(days=7)
        return cls.objects.filter(
            user=user,
            updated_at__gte=expiration_date
        ).first()

    @classmethod
    def cleanup_expired(cls):
        """Delete all drafts older than 7 days."""
        expiration_date = timezone.now() - timedelta(days=7)
        deleted_count, _ = cls.objects.filter(updated_at__lt=expiration_date).delete()
        return deleted_count
