#!/usr/bin/env python
"""
Vérifier les parcours disponibles pour la structure commune
"""

import subprocess
import sys

def check_commune_templates():
    """Vérifier les templates pour la structure commune"""
    
    print("Verification des parcours pour la structure commune...")
    
    check_script = '''
from courses.models import LearningPathTemplate

print("📊 PARCOURS DISPONIBLES PAR STRUCTURE")
print("=" * 50)

# Compter les templates par structure
templates = LearningPathTemplate.objects.all()
structures = {}

for template in templates:
    structure_name = template.get_structure_display()
    if structure_name not in structures:
        structures[structure_name] = []
    structures[structure_name].append(template)

# Afficher les détails
for structure_name, struct_templates in structures.items():
    print(f"\\n🏢 {structure_name}:")
    print(f"   📋 Total: {len(struct_templates)} parcours")
    
    actifs = [t for t in struct_templates if t.is_active]
    print(f"   ✅ Actifs: {len(actifs)}")
    
    # Détails pour la commune
    if "commune" in structure_name.lower():
        print(f"   📝 Détails:")
        for template in struct_templates:
            status = "✅ Actif" if template.is_active else "❌ Inactif"
            print(f"      - {template.name} ({template.level}) {status}")
            print(f"        📚 Cours: {template.courses.count()}")
            print(f"        🎓 Certification: {'Oui' if getattr(template, 'certification_required', False) else 'Non'}")
            print(f"        📧 Auto-gen: {'Oui' if getattr(template, 'auto_generate_certification', False) else 'Non'}")

# Résumé spécifique pour la commune
commune_templates = [t for t in templates if t.structure == 'commune']
print(f"\\n🎯 RÉSUMÉ SPÉCIFIQUE - COMMUNE")
print("-" * 40)
print(f"📋 Total parcours commune: {len(commune_templates)}")
print(f"✅ Parcours actifs: {len([t for t in commune_templates if t.is_active])}")

if commune_templates:
    print(f"\\n📋 LISTE DES PARCOURS COMMUNE:")
    for i, template in enumerate(commune_templates, 1):
        status = "✅" if template.is_active else "❌"
        print(f"   {i}. {template.name} ({template.level}) {status}")
        print(f"      📚 {template.courses.count()} cours")
        print(f"      🎓 Certif: {'Oui' if getattr(template, 'certification_required', False) else 'Non'}")
else:
    print("❌ Aucun parcours trouvé pour la structure commune")

# Vérifier les templates multi-structures
multi_templates = [t for t in templates if t.structure == 'multi_structure']
print(f"\\n🌐 PARCOURS MULTI-STRUCTURES: {len(multi_templates)}")
if multi_templates:
    print("💡 Ces parcours sont disponibles pour TOUTES les structures")
    for template in multi_templates[:3]:  # Limiter à 3
        print(f"   - {template.name} ({template.level})")

print(f"\\n🎯 CONCLUSION")
if commune_templates:
    print("✅ OUI - Il y a des parcours pour la structure commune")
else:
    print("❌ NON - Aucun parcours spécifique pour la commune")
    print("💡 Solutions:")
    print("   1. Créer des templates pour la structure commune")
    print("   2. Utiliser les templates multi-structures")
    print("   3. Activer les templates existants")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', check_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Résultat:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Erreur execution: {e}")

if __name__ == "__main__":
    check_commune_templates()
