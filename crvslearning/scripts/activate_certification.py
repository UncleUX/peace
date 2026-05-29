#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from courses.models import LearningPathTemplate

# Activer la certification sur le template "Expert Commune"
try:
    template = LearningPathTemplate.objects.get(name="Expert Commune")
    
    # Activer les champs de certification
    template.certification_required = True
    template.certification_threshold = 80
    template.auto_generate_certification = True
    template.certification_level = 'beginner'
    template.certificate_template_name = 'default'
    
    template.save()
    
    print(f"✅ Template '{template.name}' mis à jour avec succès !")
    print(f"🎓 Certification requise: {template.certification_required}")
    print(f"📊 Seuil: {template.certification_threshold}%")
    print(f"🤖 Auto-génération: {template.auto_generate_certification}")
    print(f"🎯 Niveau: {template.certification_level}")
    
except LearningPathTemplate.DoesNotExist:
    print("❌ Template 'agent communal debutant' non trouvé")
    
    # Lister les templates disponibles
    templates = LearningPathTemplate.objects.all()
    print(f"\n📋 Templates disponibles ({templates.count()}):")
    for t in templates:
        print(f"   - {t.name}")
        
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n🚀 Vous pouvez maintenant vérifier sango.ku avec:")
print("python3 manage.py check_user_certification \"sango.ku\"")
