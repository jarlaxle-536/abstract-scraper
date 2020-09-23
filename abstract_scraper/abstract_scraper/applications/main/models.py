from django.db import models

# Create your models here.

class Article(models.Model):
    doi = models.CharField(max_length=50, unique=True, blank=True, default=None)
    def __str__(self):
        return f'{self.doi}'

class Info(models.Model):
    article = models.OneToOneField(Article, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    authors = models.CharField(max_length=50)
    abstract = models.TextField(blank=True, default=None)
    references = models.ManyToManyField(Article, related_name='referenced_by')
    def __str__(self):
        return f'"{self.title}" [{self.article.doi}]'
