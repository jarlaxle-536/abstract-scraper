from django.db import models

class Proxy(models.Model):

    ip_address = models.GenericIPAddressField(blank=False, default=None)
    port = models.CharField(blank=False, default=None, max_length=50)
    conn_succ = models.IntegerField(default=0)
    conn_total = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'proxy'
        verbose_name_plural = 'proxies'
        unique_together = ('ip_address', 'port', )

    def __str__(self):
        return f'{self.ip_address}:{self.port}'
