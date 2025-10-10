from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Tag(models.Model):
    """Tag model for categorizing content"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    usage_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_tag_name'),
            models.UniqueConstraint(fields=['slug'], name='unique_tag_slug'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
