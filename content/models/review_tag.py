from django.db import models
from .review import Review


class ReviewTag(models.Model):
    """
    Junction table for Review and Tag relationship.
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='review_tags'
    )
    tag = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['review', 'tag']
        ordering = ['tag']
        verbose_name = 'Review Tag'
        verbose_name_plural = 'Review Tags'

    def __str__(self):
        return f"{self.review} - {self.tag}"
