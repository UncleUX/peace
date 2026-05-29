import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from tracking.models import CourseReminder

User = get_user_model()

print("🔍 Vérification simple des rappels...")

# Vérifier cynthia.essomba
cynthia = User.objects.filter(username='cynthia.essomba').first()
if cynthia:
    print(f"✅ Cynthia trouvé: {cynthia.username} (role: {cynthia.role})")
    
    # Ses rappels
    reminders = CourseReminder.objects.filter(user=cynthia)
    print(f"🔔 Rappels pour cynthia: {reminders.count()}")
    
    for r in reminders:
        print(f"   - {r.course.title}")
        print(f"     Progression: {r.progress_percentage}%")
        print(f"     Actif: {r.is_active}")
else:
    print("❌ Cynthia.essomba non trouvé")

# Vérifier tous les rappels
all_reminders = CourseReminder.objects.all()
print(f"\n📊 Total rappels dans la base: {all_reminders.count()}")

for r in all_reminders:
    print(f"   - {r.user.username} → {r.course.title}")
