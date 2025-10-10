from django.db import models
from django.contrib.contenttypes.fields import GenericRelation


class Encyclopedia(models.Model):
    """Encyclopedia entry model for testing Image attachments"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    images = GenericRelation('Image')

    def __str__(self):
        return self.title
