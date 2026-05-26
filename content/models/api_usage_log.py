from django.db import models


class ApiUsageLog(models.Model):
    endpoint = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['endpoint', 'timestamp'], name='content_apiusagelog_ep_ts_idx'),
        ]

    def __str__(self):
        return f'{self.endpoint} @ {self.timestamp:%Y-%m-%d %H:%M}'
