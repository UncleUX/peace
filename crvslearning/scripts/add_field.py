#!/usr/bin/env python
"""
Script pour ajouter le champ additional_structures manuellement
"""

import subprocess
import sys

def add_field():
    """Ajouter le champ additional_structures"""
    
    script = '''
from django.db import connection
cursor = connection.cursor()
try:
    cursor.execute('ALTER TABLE courses_learningpathtemplate ADD COLUMN additional_structures VARCHAR(200) DEFAULT "";')
    print('Champ additional_structures ajoute avec succes')
except Exception as e:
    print(f'Erreur: {e}')
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Resultat:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Erreur execution: {e}")

if __name__ == "__main__":
    add_field()
