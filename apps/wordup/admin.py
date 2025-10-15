from django.contrib import admin
from .models import Word, UserWordProgress


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ['word', 'difficulty', 'part_of_speech', 'created_at']
    list_filter = ['difficulty', 'part_of_speech']
    search_fields = ['word', 'definition']
    ordering = ['word']


@admin.register(UserWordProgress)
class UserWordProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'word', 'is_mastered', 'attempts', 'mastered_at', 'last_practiced_at']
    list_filter = ['is_mastered', 'word__difficulty']
    search_fields = ['user__username', 'word__word']
    raw_id_fields = ['user', 'word']
    readonly_fields = ['first_attempted_at', 'last_practiced_at']
    ordering = ['-last_practiced_at']
