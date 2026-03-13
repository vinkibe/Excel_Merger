from django.db import models
from django.utils import timezone


class MergeOperation(models.Model):
    MERGE_TYPES = [
        ('inner', 'Inner Join'),
        ('outer', 'Outer Join'),
        ('left', 'Left Join'),
        ('right', 'Right Join'),
    ]
    
    DUPLICATE_HANDLING = [
        ('keep_first', 'Keep First'),
        ('keep_last', 'Keep Last'),
        ('keep_all', 'Keep All'),
    ]
    
    session_id = models.CharField(max_length=255, unique=True)
    file1_name = models.CharField(max_length=255)
    file2_name = models.CharField(max_length=255)
    merge_key = models.CharField(max_length=255)
    merge_type = models.CharField(max_length=20, choices=MERGE_TYPES, default='outer')
    duplicate_handling = models.CharField(max_length=20, choices=DUPLICATE_HANDLING, default='keep_first')
    output_filename = models.CharField(max_length=255, blank=True)
    total_rows = models.IntegerField(default=0)
    file1_rows = models.IntegerField(default=0)
    file2_rows = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Merge Operation'
        verbose_name_plural = 'Merge Operations'
    
    def __str__(self):
        return f"{self.file1_name} + {self.file2_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class UploadedFile(models.Model):
    FILE_TYPES = [
        ('xlsx', 'Excel (.xlsx)'),
        ('xls', 'Excel (.xls)'),
        ('csv', 'CSV'),
    ]
    
    session_id = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_path = models.CharField(max_length=500)
    rows = models.IntegerField(default=0)
    columns = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Uploaded File'
        verbose_name_plural = 'Uploaded Files'
    
    def __str__(self):
        return f"{self.filename} ({self.rows} rows, {self.columns} cols)"
