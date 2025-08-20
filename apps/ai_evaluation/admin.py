"""
Admin configuration for AI Evaluation app
"""
from django.contrib import admin

# This app primarily provides services and doesn't have models
# Admin configuration would be added here if models are created in the future

# Example placeholder for future evaluation history model:
# @admin.register(EvaluationHistory)
# class EvaluationHistoryAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'session', 'evaluation_type', 'score', 'created_at')
#     list_filter = ('evaluation_type', 'created_at')
#     search_fields = ('user__email', 'session__session_id')
#     ordering = ('-created_at',)
