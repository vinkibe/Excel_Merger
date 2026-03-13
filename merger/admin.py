from django.contrib import admin
from .models import MergeOperation, UploadedFile


@admin.register(MergeOperation)
class MergeOperationAdmin(admin.ModelAdmin):
    list_display = ('file1_name', 'file2_name', 'merge_key', 'merge_type', 'total_rows', 'created_at')
    list_filter = ('merge_type', 'duplicate_handling', 'created_at')
    search_fields = ('file1_name', 'file2_name', 'session_id')
    readonly_fields = ('session_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Files', {
            'fields': ('session_id', 'file1_name', 'file2_name')
        }),
        ('Merge Settings', {
            'fields': ('merge_key', 'merge_type', 'duplicate_handling')
        }),
        ('Results', {
            'fields': ('total_rows', 'file1_rows', 'file2_rows', 'output_filename')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'file_type', 'rows', 'columns', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('filename', 'session_id')
    readonly_fields = ('session_id', 'uploaded_at')
    fieldsets = (
        ('File Info', {
            'fields': ('filename', 'file_type', 'session_id')
        }),
        ('Statistics', {
            'fields': ('rows', 'columns')
        }),
        ('Storage', {
            'fields': ('file_path',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
