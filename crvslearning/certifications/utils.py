"""
Utilitaires pour la gestion automatique des certifications
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from courses.models import LearningPath, CourseCompletion, LearningPathTemplate
from .models import Certification
from courses.signals import update_learning_path_on_course_completion
import uuid


def generate_automatic_certification(user, template):
    """
    Génère automatiquement une certification basée sur la completion du parcours
    """
    
    # Vérifier si la certification est requise
    if not getattr(template, 'certification_required', False):
        return None, "Certification non requise pour ce parcours"
    
    # Vérifier si une certification existe déjà pour ce template
    existing_certification = Certification.objects.filter(
        user=user,
        template=template
    ).first()
    
    if existing_certification:
        return existing_certification, "Certification déjà existante"
    
    # Calculer le taux de completion
    from courses.models import LearningPath
    try:
        learning_path = LearningPath.objects.get(user=user)
    except LearningPath.DoesNotExist:
        return None, "LearningPath non trouvé"
    
    total_courses = template.courses.count()
    if total_courses == 0:
        return None, "Aucun cours dans le template"
    
    completed_courses = learning_path.completed_courses.filter(id__in=template.courses.all()).count()
    completion_rate = completed_courses / total_courses
    
    # Vérifier le seuil
    required_threshold = getattr(template, 'certification_threshold', 80) / 100
    
    if completion_rate < required_threshold:
        return None, f"Taux de completion insuffisant ({completion_rate:.1%} < {required_threshold:.1%})"
    
    # Déterminer le niveau de certification
    certification_level = getattr(template, 'certification_level', 'beginner')
    
    # Créer la certification automatique
    certification = Certification.objects.create(
        user=user,
        template=template,
        course=None,  # Pas de cours pour les certifications de template
        level=certification_level,
        title=f"Certification {certification_level.upper()} - {template.name}",
        code=generate_certification_code(user, template, certification_level),
        is_valid=True
    )
    
    # Mettre à jour le LearningPath
    learning_path.certification_obtained = True
    learning_path.certification_date = timezone.now()
    learning_path.save()
    
    return certification, f"Certification générée avec succès (taux: {completion_rate:.1%})"


def determine_certification_level(template, completed_courses, total_courses):
    """
    Détermine le niveau de certification basé sur le parcours et la performance
    """
    
    # Niveau de base du template
    base_level = template.level
    
    # Logique de progression
    if base_level == 'beginner':
        if completed_courses == total_courses:
            return 'beginner'
        elif completed_courses >= total_courses * 0.8:
            return 'beginner'
        else:
            return None
    
    elif base_level == 'intermediate':
        if completed_courses == total_courses:
            return 'intermediate'
        elif completed_courses >= total_courses * 0.9:
            return 'intermediate'
        else:
            return None
    
    elif base_level == 'advanced':
        if completed_courses == total_courses:
            return 'advanced'
        elif completed_courses >= total_courses * 0.95:
            return 'advanced'
        else:
            return None
    
    return base_level


def generate_certification_code(user, template, level):
    """
    Génère un code de certification unique
    """
    import random
    timestamp = timezone.now().strftime("%Y%m%d")
    user_id = user.id
    template_code = template.id
    random_suffix = random.randint(1000, 9999)
    
    return f"CRVS-{level.upper()}-{timestamp}-{user_id}-{template_code}-{random_suffix}"


def check_certification_eligibility(user, learning_path):
    """
    Vérifie si l'utilisateur est éligible à une certification
    """
    
    if not learning_path.template:
        return False, "Aucun template assigné"
    
    template = learning_path.template
    
    # Vérifier si la certification est requise
    if not getattr(template, 'certification_required', False):
        return False, "Certification non requise pour ce parcours"
    
    # Vérifier la completion des cours
    total_courses = template.courses.count()
    completed_courses = learning_path.completed_courses.filter(id__in=template.courses.all()).count()
    
    if total_courses == 0:
        return False, "Aucun cours dans le template"
    
    completion_rate = completed_courses / total_courses
    
    # Utiliser le seuil configuré dans le template
    required_threshold = getattr(template, 'certification_threshold', 80) / 100
    
    if completion_rate >= required_threshold:
        return True, f"Éligible (taux: {completion_rate:.1%} >= {required_threshold:.1%})"
    else:
        return False, f"Non éligible (taux: {completion_rate:.1%} < {required_threshold:.1%})"


def generate_certificate_pdf_unified(certification, score=None):
    """
    Fonction unifiée pour générer tous les types de certificats
    """
    from django.template.loader import render_to_string
    import io
    
    try:
        # Détecter le type de certification
        if certification.template and not certification.course:
            # TYPE PARCOURS
            context = {
                'certification': certification,
                'user': certification.user,
                'issue_date': certification.issued_at,
                'validation_code': certification.code,
                'pathway_name': certification.template.name,
                'type': 'pathway'
            }
            template_name = 'certifications/pathway_certificate.html'
            
        elif certification.course and not certification.template:
            # TYPE ÉVALUATION
            context = {
                'certification': certification,
                'user': certification.user,
                'issue_date': certification.issued_at,
                'validation_code': certification.code,
                'course_title': certification.course.title,
                'score': score,
                'type': 'evaluation'
            }
            template_name = 'certifications/evaluation_certificate.html'
            
        else:
            # TYPE PAR DÉFAUT OU HYBRIDE
            context = {
                'certification': certification,
                'user': certification.user,
                'issue_date': certification.issued_at,
                'validation_code': certification.code,
                'type': 'default'
            }
            template_name = 'certifications/certificate_template.html'
        
        # Générer le contenu HTML
        html_content = render_to_string(template_name, context)
        
        # UTILISER VRAIMENT LE HTML pour le PDF
        try:
            # Essayer d'utiliser WeasyPrint si disponible
            from weasyprint import HTML, CSS
            pdf_buffer = HTML(string=html_content).write_pdf()
            buffer = io.BytesIO(pdf_buffer)
            return buffer
        except ImportError:
            # FORCER LE DESIGN PROFESSIONNEL - UTILISE FICHIER DISQUE
            pdf_path = _generate_professional_pdf(certification, score, context)
            # Lire le fichier et retourner buffer pour compatibilité avec les vues
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            buffer = io.BytesIO(pdf_content)
            return buffer
        
    except Exception as e:
        print(f"Erreur génération PDF unifié: {e}")
        # FORCER LE DESIGN PROFESSIONNEL MÊME EN CAS D'ERREUR
        try:
            pdf_path = _generate_professional_pdf(certification, score, context)
            # Lire le fichier et retourner buffer pour compatibilité avec les vues
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            buffer = io.BytesIO(pdf_content)
            return buffer
        except Exception as prof_error:
            print(f"Erreur design professionnel: {prof_error}")
            # DERNIER RECOURS : design basique amélioré
            return _generate_basic_pdf(certification, score)


def _generate_professional_pdf(certification, score, context):
    """
    Génère un PDF professionnel avec la structure exacte de l'évaluation
    Adapté pour les parcours d'apprentissage
    """
    import os
    import qrcode
    from django.conf import settings
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from django.utils import timezone

    # =========================
    # Prepare paths (IDENTIQUE ÉVALUATION)
    # =========================
    media_root = getattr(settings, 'MEDIA_ROOT', '.')
    out_dir = os.path.join(media_root, 'certificates')
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, f"pathway_{certification.code}.pdf")

    # =========================
    # Create QR (IDENTIQUE ÉVALUATION)
    # =========================
    verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
    scheme = 'https'
    if settings.DEBUG:
        scheme = 'http'
    base_url = f"{scheme}://{verify_host}"

    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    if not media_url.endswith('/'):
        media_url += '/'

    qr_target = f"{base_url}{media_url}certificates/pathway_{certification.code}.pdf"
    qr_img = qrcode.make(qr_target)
    qr_path = os.path.join(out_dir, f"pathway_{certification.code}.png")
    qr_img.save(qr_path)

    # =========================
    # Locate static images (IDENTIQUE ÉVALUATION)
    # =========================
    signature_path = None
    cachet_path = None

    static_candidates = []
    static_root = getattr(settings, 'STATIC_ROOT', '')
    if static_root:
        static_candidates.append(static_root)
    for p in getattr(settings, 'STATICFILES_DIRS', []):
        static_candidates.append(p)

    for base in static_candidates:
        sig = os.path.join(base, "img", "signature_dg.png")
        stamp = os.path.join(base, "img", "cachet_bunec.png")
        if os.path.exists(sig):
            signature_path = sig
        if os.path.exists(stamp):
            cachet_path = stamp

    # =========================
    # Build PDF (IDENTIQUE ÉVALUATION)
    # =========================
    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setTitle("Certification")

    # =========================
    # Colors (ADAPTÉ POUR PARCOURS)
    # =========================
    border_color = colors.HexColor("#34495e")
    ribbon_color = colors.HexColor("#4f46e5")  # BLEU pour parcours
    ribbon_gold = colors.HexColor("#c9a227")
    text_gray = colors.HexColor("#4b5563")

    margin = 24

    # =========================
    # Double Border (IDENTIQUE ÉVALUATION)
    # =========================
    c.setStrokeColor(border_color)
    c.setLineWidth(4)
    c.rect(margin, margin, width - 2*margin, height - 2*margin, fill=0)
    c.setLineWidth(1.5)
    c.rect(margin + 10, margin + 10, width - 2*(margin + 10), height - 2*(margin + 10), fill=0)

    # =========================
    # Left Ribbon (IDENTIQUE ÉVALUATION)
    # =========================
    ribbon_x = margin + 20
    ribbon_w = 70

    c.setFillColor(ribbon_color)  # BLEU pour parcours
    c.rect(ribbon_x, margin + 10, ribbon_w, height - 2*(margin + 10), fill=1, stroke=0)

    c.setFillColor(ribbon_gold)
    c.rect(ribbon_x + 5, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)
    c.rect(ribbon_x + ribbon_w - 11, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)

    # =========================
    # Medal (IDENTIQUE ÉVALUATION)
    # =========================
    medal_cx = ribbon_x + ribbon_w / 2
    medal_cy = height - 180
    medal_r = 55

    c.setFillColor(colors.HexColor("#f5f3e7"))
    c.setStrokeColor(ribbon_gold)
    c.setLineWidth(4)
    c.circle(medal_cx, medal_cy, medal_r, fill=1, stroke=1)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ribbon_gold)
    c.drawCentredString(medal_cx, medal_cy + 14, "LEARNING")
    c.drawCentredString(medal_cx, medal_cy - 18, "PATH")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(medal_cx, medal_cy - 4, "★")

    # =========================
    # Content Origin (IDENTIQUE ÉVALUATION)
    # =========================
    content_x = ribbon_x + ribbon_w + 60

    # =========================
    # Header (ADAPTÉ POUR PARCOURS)
    # =========================
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.black)
    c.drawString(content_x, height - 120, "CRVS LEARNING")

    c.setFont("Helvetica", 22)
    c.drawString(content_x, height - 160, "Certificate of Learning Path Completion")

    # =========================
    # Recipient Name (IDENTIQUE ÉVALUATION)
    # =========================
    recipient = (certification.user.get_full_name() or certification.user.username)
    c.setFont("Helvetica", 14)
    c.setFillColor(text_gray)
    c.drawString(content_x, height - 200, f"Congratulations, {recipient}")

    # =========================
    # Certificate Title (NORMALISÉ PARCOURS)
    # =========================
    y = height - 260
    
    # Titre normalisé pour les parcours
    if certification.template:
        level = certification.get_level_display().upper()
        
        # Mapping des niveaux CRVS
        if level == 'BEGINNER' or level == 'DÉBUTANT':
            title = f"CRVS 1 - ASSOCIATE"
        elif level == 'INTERMEDIATE' or level == 'INTERMÉDIAIRE':
            title = f"CRVS 2 - PROFESSIONAL"
        elif level == 'ADVANCED' or level == 'AVANCÉ':
            title = f"CRVS 3 - EXPERT"
        else:
            # Fallback pour autres niveaux
            title = f"Certification {level} - {certification.template.name}"
        
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(colors.black)
        c.drawString(content_x, y, title)
        y -= 40
    elif certification.title:
        # Pour les évaluations, garder le titre existant
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(colors.black)
        c.drawString(content_x, y, certification.title)
        y -= 40

    # =========================
    # Learning Path Title (ADAPTÉ POUR PARCOURS)
    # =========================
    c.setFont("Helvetica-Bold", 12)
    if certification.template:
        pathway_title = certification.template.name
        c.drawString(content_x, y, pathway_title)
    else:
        c.drawString(content_x, y, "Learning Path")
    
    # =========================
    # Level (IDENTIQUE ÉVALUATION)
    # =========================
    y -= 24
    c.setFont("Helvetica", 12)
    level_label = str(certification.get_level_display() if hasattr(certification, 'get_level_display') else certification.level)
    c.drawString(content_x, y, f"Level: {level_label}")
    y -= 30

    # =========================
    # Meta Date (IDENTIQUE ÉVALUATION)
    # =========================
    issue_date = certification.issued_at.strftime('%B %d, %Y')
    y -= 2
    c.setFont("Helvetica", 12)
    c.setFillColor(text_gray)
    c.drawString(content_x, y, f"Learning program completed on {issue_date}")

    # =========================
    # Description (ADAPTÉ POUR PARCOURS)
    # =========================
    y -= 40
    text = c.beginText()
    text.setTextOrigin(content_x, y)
    text.setFont("Helvetica", 12)
    text.setFillColor(colors.black)
    text.textLine("By completing this learning path, you have mastered essential skills,")
    text.textLine("gained valuable knowledge, and advanced your professional development.")
    c.drawText(text)

    # =========================
    # Gap before signature (IDENTIQUE ÉVALUATION)
    # =========================
    sig_y = 110 - 16

    # =========================
    # Signature Block (IDENTIQUE ÉVALUATION)
    # =========================
    if signature_path:
        try:
            c.drawImage(
                ImageReader(signature_path),
                content_x,
                sig_y + 40,
                width=180,
                height=60,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            pass

    # Yellow line under signature
    c.setStrokeColor(ribbon_gold)
    c.setLineWidth(2)
    c.line(content_x, sig_y + 35, content_x + 260, sig_y + 35)

    # Name + institution
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(content_x, sig_y + 18, "Alexandre Marie YOMO")
    c.setFont("Helvetica", 10)
    c.drawString(content_x, sig_y + 4, "BUNEC GENERAL MANAGER")

    # Cachet collé à la signature
    if cachet_path:
        try:
            c.drawImage(
                ImageReader(cachet_path),
                content_x + 190,
                sig_y + 10,
                width=80,
                height=80,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            pass

    # =========================
    # QR (IDENTIQUE ÉVALUATION)
    # =========================
    try:
        c.drawImage(
            ImageReader(qr_path),
            width - margin - 110,
            margin + 40,
            width=80,
            height=80,
            preserveAspectRatio=True,
            mask='auto'
        )
    except Exception:
        pass

    # =========================
    # Footer (IDENTIQUE ÉVALUATION)
    # =========================
    c.setFont("Helvetica", 9)
    c.setFillColor(text_gray)
    c.drawCentredString(
        width / 2,
        margin + 20,
        f"Certificate ID: {certification.code}"
    )

    c.showPage()
    c.save()

    # RETOURNER LE CHEMIN DU FICHIER (COMME ÉVALUATION)
    return pdf_path


def _generate_basic_pdf(certification, score):
    """Génère un PDF basique mais avec design amélioré (FORCÉ)"""
    import io  # Import manquant ajouté
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import HexColor
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Design amélioré même en fallback
    if certification.template:
        # STYLE PARCOURS (BLEU)
        main_color = HexColor('#4f46e5')
        title_prefix = "PARCOURS"
        info_text = f"Parcours: {certification.template.name}"
    else:
        # STYLE ÉVALUATION (VERT)
        main_color = HexColor('#059669')
        title_prefix = "ÉVALUATION"
        info_text = f"Cours: {certification.course.title}"
    
    # Bordure
    p.setStrokeColor(HexColor('#34495e'))
    p.setLineWidth(2)
    p.rect(20, 20, width - 40, height - 40, fill=0)
    
    # Titre avec couleur (NORMALISÉ PARCOURS)
    p.setFillColor(main_color)
    p.setFont("Helvetica-Bold", 28)
    
    # Titre normalisé pour les parcours
    if certification.template:
        level = certification.get_level_display().upper()
        
        # Mapping des niveaux CRVS
        if level == 'BEGINNER' or level == 'DÉBUTANT':
            title = f"CRVS 1 - ASSOCIATE"
        elif level == 'INTERMEDIATE' or level == 'INTERMÉDIAIRE':
            title = f"CRVS 2 - PROFESSIONAL"
        elif level == 'ADVANCED' or level == 'AVANCÉ':
            title = f"CRVS 3 - EXPERT"
        else:
            # Fallback pour autres niveaux
            title = f"Certification {level} - {certification.template.name}"
        
        p.drawString(100, 750, title)
    else:
        # Pour les évaluations, format standard
        p.drawString(100, 750, f"Certification {certification.get_level_display().upper()}")
    
    # Informations
    p.setFillColor(HexColor('#374151'))
    p.setFont("Helvetica", 18)
    p.drawString(100, 700, f"Délivré à: {certification.user.get_full_name() or certification.user.username}")
    
    p.setFont("Helvetica", 16)
    p.drawString(100, 650, info_text)
    p.drawString(100, 620, f"Date: {certification.issued_at.strftime('%d/%m/%Y')}")
    p.drawString(100, 590, f"Code: {certification.code}")
    
    if score is not None:
        p.drawString(100, 560, f"Score: {score}%")
    
    # Footer
    p.setFont("Helvetica-Oblique", 12)
    p.setFillColor(HexColor('#6b7280'))
    p.drawString(100, 100, "CRVS Learning - Certification Platform")
    
    p.save()
    buffer.seek(0)
    
    return buffer


def _generate_minimal_pdf(certification):
    """Génère un PDF minimal en dernier recours"""
    import io  # Import manquant ajouté
    from reportlab.pdfgen import canvas
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica", 16)
    p.drawString(100, 750, f"Certification {certification.code}")
    p.drawString(100, 700, f"Délivré à: {certification.user.username}")
    p.drawString(100, 650, f"Date: {certification.issued_at.strftime('%d/%m/%Y')}")
    
    p.save()
    buffer.seek(0)
    
    return buffer


def create_certification_pdf(certification):
    """
    Crée un PDF de certification (placeholder pour l'implémentation)
    """
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    # Template HTML pour la certification
    context = {
        'certification': certification,
        'user': certification.user,
        'issue_date': certification.issued_at,
        'validation_code': certification.code
    }
    
    html_content = render_to_string('certifications/certificate_template.html', context)
    
    # Génération PDF (à implémenter)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Ajout du contenu (simplifié pour l'exemple)
    p.drawString(100, 750, f"Certification {certification.level.upper()}")
    p.drawString(100, 700, f"Délivré à: {certification.user.get_full_name()}")
    p.drawString(100, 650, f"Date: {certification.issued_at.strftime('%d/%m/%Y')}")
    p.drawString(100, 600, f"Code: {certification.code}")
    
    p.save()
    buffer.seek(0)
    
    return buffer


# Signals pour la certification automatique
@receiver(post_save, sender=LearningPath)
def check_and_generate_certification(sender, instance, created, **kwargs):
    """
    Vérifie et génère automatiquement une certification quand le parcours est mis à jour
    """
    if created:
        return  # Ne pas générer pour les nouveaux parcours
    
    # Vérifier si le parcours est complété
    if not instance.template:
        return
    
    eligibility, message = check_certification_eligibility(instance.user, instance)
    
    if eligibility:
        certification, result_message = generate_automatic_certification(
            instance.user, 
            instance.template
        )
        
        if certification:
            print(f"🎓 Certification automatique générée: {certification}")
            
            # Envoyer notification (à implémenter)
            from courses.notifications import send_certification_notification
            send_certification_notification(instance.user, certification)


@receiver(post_save, sender=CourseCompletion)
def update_certification_on_new_completion(sender, instance, created, **kwargs):
    """
    Met à jour la certification quand un nouveau cours est complété
    """
    if not created:
        return
    
    user = instance.user
    learning_path = user.learning_path
    
    if not learning_path or not learning_path.template:
        return
    
    # Vérifier l'éligibilité à la certification
    eligibility, message = check_certification_eligibility(user, learning_path)
    
    if eligibility:
        # Générer ou mettre à jour la certification
        certification, result_message = generate_automatic_certification(
            user, 
            learning_path.template
        )
        
        if certification:
            print(f"🎓 Certification mise à jour: {certification}")


def get_user_certifications(user):
    """
    Récupère toutes les certifications de l'utilisateur
    """
    return Certification.objects.filter(user=user, is_valid=True).order_by('-issued_at')


def get_certification_stats(user):
    """
    Statistiques des certifications de l'utilisateur
    """
    certifications = get_user_certifications(user)
    
    stats = {
        'total_certifications': certifications.count(),
        'by_level': {},
        'latest': certifications.first() if certifications.exists() else None,
        'valid_certifications': certifications.filter(is_valid=True).count()
    }
    
    # Comptage par niveau
    for cert in certifications:
        level = cert.get_level_display()
        stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
    
    return stats
