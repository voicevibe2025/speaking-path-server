"""
Management command to fetch IPA pronunciation for words using Free Dictionary API.
Usage: python manage.py fetch_ipa
"""
import requests
from django.core.management.base import BaseCommand
from apps.wordup.models import Word


class Command(BaseCommand):
    help = 'Fetch IPA pronunciation for words from Free Dictionary API'

    def handle(self, *args, **options):
        words = Word.objects.filter(ipa_pronunciation='')
        total = words.count()
        
        self.stdout.write(f"Fetching IPA for {total} words...")
        
        success_count = 0
        fail_count = 0
        
        for word in words:
            try:
                # Free Dictionary API - no API key needed!
                url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.word.lower()}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract IPA from phonetics
                    ipa = None
                    if data and len(data) > 0:
                        phonetics = data[0].get('phonetics', [])
                        for phonetic in phonetics:
                            if phonetic.get('text'):
                                ipa = phonetic['text']
                                break
                    
                    if ipa:
                        word.ipa_pronunciation = ipa
                        word.save()
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ {word.word}: {ipa}")
                        )
                    else:
                        fail_count += 1
                        self.stdout.write(
                            self.style.WARNING(f"⚠ {word.word}: No IPA found")
                        )
                else:
                    fail_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"⚠ {word.word}: API returned {response.status_code}")
                    )
                    
            except Exception as e:
                fail_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ {word.word}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Success: {success_count}, Failed: {fail_count}"
            )
        )
