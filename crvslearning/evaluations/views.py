from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.conf import settings

from .models import EvaluationLevel, Attempt, EvaluationQuestion, EvaluationChoice, AttemptAnswer
from courses.models import Course, Lesson
from certifications.models import Certification

import os
import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors


def _user_level_completion(user, course, level: str) -> dict:
    modules = course.modules.filter(level=level).prefetch_related('lessons')
    lesson_ids = []
    for m in modules:
        lesson_ids.extend(list(m.lessons.values_list('id', flat=True)))

    total = len(lesson_ids)
    if total == 0:
        return {"total": 0, "done": 0, "percent": 0, "completed": False}

    from courses.models import LessonProgress
    done = LessonProgress.objects.filter(user=user, lesson_id__in=lesson_ids, is_completed=True).count()
    percent = int((done / total) * 100)
    return {"total": total, "done": done, "percent": percent, "completed": done == total}


# def _generate_certificate_pdf(cert: Certification, score: float) -> str:
    # Prepare paths
    media_root = getattr(settings, 'MEDIA_ROOT', '.')
    out_dir = os.path.join(media_root, 'certificates')
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, f"{cert.code}.pdf")

    # Create QR/verify URL
    verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
    scheme = 'https'
    if settings.DEBUG:
        scheme = 'http'
    base_url = f"{scheme}://{verify_host}"
    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    if not media_url.endswith('/'):
        media_url += '/'
    qr_target = f"{base_url}{media_url}certificates/{cert.code}.pdf"
    qr_img = qrcode.make(qr_target)
    qr_path = os.path.join(out_dir, f"{cert.code}.png")
    qr_img.save(qr_path)

    # Try to load a logo from static if present
    logo_path = None
    candidate_paths = []
    static_root = getattr(settings, 'STATIC_ROOT', '')
    if static_root:
        candidate_paths.append(os.path.join(static_root, 'img', 'logo.png'))
    for p in getattr(settings, 'STATICFILES_DIRS', []):
        candidate_paths.append(os.path.join(p, 'img', 'logo.png'))
    for p in candidate_paths:
        if os.path.exists(p):
            logo_path = p
            break

    # Build PDF in landscape A4
    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setTitle("Certification")

    # Background: subtle geometric lines
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.5)
    margin = 36
    # diagonal mesh
    for x in range(0, int(width) + 200, 120):
        c.line(x - 200, margin, x, height - margin)
    for x in range(0, int(width) + 200, 120):
        c.line(x - 200, height - margin, x, margin)

    # Header: logo top-left
    if logo_path:
        try:
            c.drawImage(ImageReader(logo_path), margin, height - 90, width=140, height=40, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    else:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, height - 70, "CRVS TRAININGS")

    # Title block centered
    center_x = width / 2
    y = height - 140
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawCentredString(center_x, y, "Civil Status Registration Office (BUNEC) certifies that")

    # Recipient name
    y -= 34
    recipient = (cert.user.get_full_name() or cert.user.username).upper()
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(center_x, y, recipient)

    # Lead-in line
    y -= 28
    c.setFont("Helvetica", 12)
    c.drawCentredString(center_x, y, "has successfully completed all program requirements and is certified as a")

    # Certificate title (red)
    y -= 36
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor('#dc2626'))  # red-600
    title_text = f"CRVS {cert.course.title} EXPERT"
    c.drawCentredString(center_x, y, title_text)

    # Subtitles (level + module)
    c.setFillColor(colors.black)
    y -= 24
    level_label = str(cert.get_level_display() if hasattr(cert, 'get_level_display') else cert.level)
    c.setFont("Helvetica", 12)
    c.drawCentredString(center_x, y, f"Level: {level_label}")

    # Optional: module label (take first module matching level)
    try:
        mod = cert.course.modules.filter(level=cert.level).first()
        if mod:
            y -= 18
            c.drawCentredString(center_x, y, f"Module: {mod.title}")
    except Exception:
        pass

    # Signature area bottom-left
    sig_y = 90
    c.setFont("Helvetica", 11)
    c.drawString(margin, sig_y + 28, "Alexandre M. YOMO")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(margin, sig_y + 14, "General Manager, BUNEC")
    # signature line
    c.setLineWidth(1)
    c.line(margin, sig_y + 8, margin + 220, sig_y + 8)

    # Seal bottom-right in grey box
    seal_w, seal_h = 70, 80
    seal_x, seal_y = width - margin - seal_w, 60
    c.setFillColor(colors.HexColor('#f3f4f6'))
    c.roundRect(seal_x, seal_y, seal_w, seal_h, 10, fill=True, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(seal_x + seal_w/2, seal_y + seal_h/2 + 6, "")
    try:
        c.drawImage(ImageReader(qr_path), seal_x + seal_w - 64, seal_y + 6, width=65, height=65, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # Footer meta: date and certificate number
    from django.utils import timezone
    issue_date = timezone.now().strftime('%B %d, %Y')
    c.setFont("Helvetica", 10)
    footer_text = f"Date of Issue: {issue_date} — Certificate Number: {cert.code}"
    c.drawCentredString(center_x, 36, footer_text)

    c.showPage()
    c.save()
    return pdf_path

# def _generate_certificate_pdf(cert: Certification, score: float) -> str:
#     import os
#     import qrcode
#     from django.conf import settings
#     from reportlab.lib.pagesizes import A4, landscape
#     from reportlab.pdfgen import canvas
#     from reportlab.lib import colors
#     from reportlab.lib.utils import ImageReader
#     from reportlab.pdfbase import pdfmetrics
#     from reportlab.pdfbase.ttfonts import TTFont

#     # =========================
#     # Prepare paths
#     # =========================
#     media_root = getattr(settings, 'MEDIA_ROOT', '.')
#     out_dir = os.path.join(media_root, 'certificates')
#     os.makedirs(out_dir, exist_ok=True)
#     pdf_path = os.path.join(out_dir, f"{cert.code}.pdf")

#     # =========================
#     # Create QR
#     # =========================
#     verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
#     scheme = 'https'
#     if settings.DEBUG:
#         scheme = 'http'
#     base_url = f"{scheme}://{verify_host}"

#     media_url = getattr(settings, 'MEDIA_URL', '/media/')
#     if not media_url.endswith('/'):
#         media_url += '/'

#     qr_target = f"{base_url}{media_url}certificates/{cert.code}.pdf"
#     qr_img = qrcode.make(qr_target)
#     qr_path = os.path.join(out_dir, f"{cert.code}.png")
#     qr_img.save(qr_path)

#     # =========================
#     # Register Poppins font
#     # =========================
#     font_dir = None
#     for p in getattr(settings, 'STATICFILES_DIRS', []):
#         candidate = os.path.join(p, 'fonts')
#         if os.path.exists(candidate):
#             font_dir = candidate
#             break

#     if not font_dir:
#         font_dir = os.path.join(getattr(settings, 'STATIC_ROOT', ''), 'fonts')

#     poppins_regular = os.path.join(font_dir, "Poppins-Regular.ttf")
#     poppins_bold = os.path.join(font_dir, "Poppins-Bold.ttf")

#     pdfmetrics.registerFont(TTFont("Poppins", poppins_regular))
#     pdfmetrics.registerFont(TTFont("Poppins-Bold", poppins_bold))

#     # =========================
#     # Build PDF
#     # =========================
#     c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
#     width, height = landscape(A4)
#     c.setTitle("Certification")

#     # =========================
#     # COLORS
#     # =========================
#     border_color = colors.HexColor("#34495e")
#     ribbon_blue = colors.HexColor("#2c3e50")
#     ribbon_gold = colors.HexColor("#c9a227")
#     text_gray = colors.HexColor("#4b5563")

#     margin = 24

#     # =========================
#     # DOUBLE BORDER
#     # =========================
#     c.setStrokeColor(border_color)
#     c.setLineWidth(4)
#     c.rect(margin, margin, width - 2*margin, height - 2*margin, fill=0)

#     c.setLineWidth(1.5)
#     c.rect(margin + 10, margin + 10, width - 2*(margin + 10), height - 2*(margin + 10), fill=0)

#     # =========================
#     # LEFT RIBBON
#     # =========================
#     ribbon_x = margin + 20
#     ribbon_w = 70

#     c.setFillColor(ribbon_blue)
#     c.rect(ribbon_x, margin + 10, ribbon_w, height - 2*(margin + 10), fill=1, stroke=0)

#     c.setFillColor(ribbon_gold)
#     c.rect(ribbon_x + 5, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)
#     c.rect(ribbon_x + ribbon_w - 11, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)

#     # =========================
#     # MEDAL
#     # =========================
#     medal_cx = ribbon_x + ribbon_w / 2
#     medal_cy = height - 180
#     medal_r = 55

#     c.setFillColor(colors.HexColor("#f5f3e7"))
#     c.setStrokeColor(ribbon_gold)
#     c.setLineWidth(4)
#     c.circle(medal_cx, medal_cy, medal_r, fill=1, stroke=1)

#     c.setFont("Poppins-Bold", 9)
#     c.setFillColor(ribbon_gold)
#     c.drawCentredString(medal_cx, medal_cy + 14, "LEARNING PATH")
#     c.drawCentredString(medal_cx, medal_cy - 18, "COMPLETION")

#     c.setFont("Poppins-Bold", 26)
#     c.drawCentredString(medal_cx, medal_cy - 2, "★")

#     # =========================
#     # CONTENT ORIGIN
#     # =========================
#     content_x = ribbon_x + ribbon_w + 60

#     # =========================
#     # HEADER
#     # =========================
#     c.setFont("Poppins-Bold", 18)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 120, "CRVS TRAININGS")

#     c.setFont("Poppins", 22)
#     c.drawString(content_x, height - 160, "Certificate of Completion")

#     # =========================
#     # NAME
#     # =========================
#     recipient = (cert.user.get_full_name() or cert.user.username)
#     c.setFont("Poppins", 14)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, height - 200, f"Congratulations, {recipient}")

#     # =========================
#     # TITLE
#     # =========================
#     c.setFont("Poppins-Bold", 28)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 260, cert.course.title)

#     # =========================
#     # META
#     # =========================
#     from django.utils import timezone
#     issue_date = timezone.now().strftime('%B %d, %Y')

#     c.setFont("Poppins", 12)
#     c.setFillColor(text_gray)
#     c.drawString(
#         content_x,
#         height - 300,
#         f"Learning program completed on {issue_date}"
#     )

#     # =========================
#     # DESCRIPTION
#     # =========================
#     text = c.beginText()
#     text.setTextOrigin(content_x, height - 350)
#     text.setFont("Poppins", 12)
#     text.setFillColor(colors.black)
#     text.textLine("By continuing to learn, you have expanded your perspective,")
#     text.textLine("sharpened your skills, and made yourself even more in demand.")
#     c.drawText(text)

#     # =========================
#     # SKILLS
#     # =========================
#     y_skills = height - 430
#     c.setFont("Poppins-Bold", 12)
#     c.drawString(content_x, y_skills, "Top skills covered")

#     c.setFont("Poppins", 11)
#     c.drawString(content_x, y_skills - 20, "CRVS, Civil Status Registration, Digital Identity")

#     # =========================
#     # SIGNATURE
#     # =========================
#     sig_y = 120
#     c.setFont("Poppins", 11)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, sig_y + 30, "Alexandre M. YOMO")
#     c.setFont("Poppins", 10)
#     c.drawString(content_x, sig_y + 14, "General Manager, BUNEC")

#     c.setLineWidth(1)
#     c.line(content_x, sig_y + 8, content_x + 260, sig_y + 8)

#     # =========================
#     # QR
#     # =========================
#     try:
#         c.drawImage(
#             ImageReader(qr_path),
#             width - margin - 110,
#             margin + 40,
#             width=80,
#             height=80,
#             preserveAspectRatio=True,
#             mask='auto'
#         )
#     except Exception:
#         pass

#     # =========================
#     # FOOTER
#     # =========================
#     c.setFont("Poppins", 9)
#     c.setFillColor(text_gray)
#     c.drawCentredString(
#         width / 2,
#         margin + 20,
#         f"Certificate ID: {cert.code}"
#     )

#     c.showPage()
#     c.save()

#     return pdf_path

# def _generate_certificate_pdf(cert: Certification, score: float) -> str:
#     import os
#     import qrcode
#     from django.conf import settings
#     from reportlab.lib.pagesizes import A4, landscape
#     from reportlab.pdfgen import canvas
#     from reportlab.lib import colors
#     from reportlab.lib.utils import ImageReader

#     # =========================
#     # Prepare paths (INCHANGÉ)
#     # =========================
#     media_root = getattr(settings, 'MEDIA_ROOT', '.')
#     out_dir = os.path.join(media_root, 'certificates')
#     os.makedirs(out_dir, exist_ok=True)
#     pdf_path = os.path.join(out_dir, f"{cert.code}.pdf")

#     # =========================
#     # Create QR (INCHANGÉ)
#     # =========================
#     verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
#     scheme = 'https'
#     if settings.DEBUG:
#         scheme = 'http'
#     base_url = f"{scheme}://{verify_host}"

#     media_url = getattr(settings, 'MEDIA_URL', '/media/')
#     if not media_url.endswith('/'):
#         media_url += '/'

#     qr_target = f"{base_url}{media_url}certificates/{cert.code}.pdf"
#     qr_img = qrcode.make(qr_target)
#     qr_path = os.path.join(out_dir, f"{cert.code}.png")
#     qr_img.save(qr_path)

#     # =========================
#     # Build PDF (SEUL LE VISUEL CHANGE)
#     # =========================
#     c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
#     width, height = landscape(A4)
#     c.setTitle("Certification")

#     # =========================
#     # COLORS
#     # =========================
#     border_color = colors.HexColor("#34495e")
#     ribbon_blue = colors.HexColor("#2c3e50")
#     ribbon_gold = colors.HexColor("#c9a227")
#     text_gray = colors.HexColor("#4b5563")

#     margin = 24

#     # =========================
#     # DOUBLE BORDER
#     # =========================
#     c.setStrokeColor(border_color)
#     c.setLineWidth(4)
#     c.rect(margin, margin, width - 2*margin, height - 2*margin, fill=0)

#     c.setLineWidth(1.5)
#     c.rect(margin + 10, margin + 10, width - 2*(margin + 10), height - 2*(margin + 10), fill=0)

#     # =========================
#     # LEFT RIBBON
#     # =========================
#     ribbon_x = margin + 20
#     ribbon_w = 70

#     c.setFillColor(ribbon_blue)
#     c.rect(ribbon_x, margin + 10, ribbon_w, height - 2*(margin + 10), fill=1, stroke=0)

#     c.setFillColor(ribbon_gold)
#     c.rect(ribbon_x + 5, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)
#     c.rect(ribbon_x + ribbon_w - 11, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)

#     # =========================
#     # MEDAL
#     # =========================
#     medal_cx = ribbon_x + ribbon_w / 2
#     medal_cy = height - 180
#     medal_r = 55

#     c.setFillColor(colors.HexColor("#f5f3e7"))
#     c.setStrokeColor(ribbon_gold)
#     c.setLineWidth(4)
#     c.circle(medal_cx, medal_cy, medal_r, fill=1, stroke=1)

#     c.setFont("Helvetica-Bold", 9)
#     c.setFillColor(ribbon_gold)
#     c.drawCentredString(medal_cx, medal_cy + 14, "LEARNING PATH")
#     c.drawCentredString(medal_cx, medal_cy - 18, "COMPLETION")

#     c.setFont("Helvetica-Bold", 24)
#     c.drawCentredString(medal_cx, medal_cy - 4, "★")

#     # =========================
#     # CONTENT ORIGIN
#     # =========================
#     content_x = ribbon_x + ribbon_w + 60

#     # =========================
#     # HEADER
#     # =========================
#     c.setFont("Helvetica-Bold", 18)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 120, "CRVS TRAININGS")

#     c.setFont("Helvetica", 22)
#     c.drawString(content_x, height - 160, "Certificate of Completion")

#     # =========================
#     # NAME
#     # =========================
#     recipient = (cert.user.get_full_name() or cert.user.username)
#     c.setFont("Helvetica", 14)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, height - 200, f"Congratulations, {recipient}")

#     # =========================
#     # TITLE
#     # =========================
#     c.setFont("Helvetica-Bold", 28)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 260, cert.course.title)

#     # =========================
#     # META
#     # =========================
#     from django.utils import timezone
#     issue_date = timezone.now().strftime('%B %d, %Y')

#     c.setFont("Helvetica", 12)
#     c.setFillColor(text_gray)
#     c.drawString(
#         content_x,
#         height - 300,
#         f"Learning program completed on {issue_date}"
#     )

#     # =========================
#     # DESCRIPTION
#     # =========================
#     text = c.beginText()
#     text.setTextOrigin(content_x, height - 350)
#     text.setFont("Helvetica", 12)
#     text.setFillColor(colors.black)
#     text.textLine("By continuing to learn, you have expanded your perspective,")
#     text.textLine("sharpened your skills, and made yourself even more in demand.")
#     c.drawText(text)

#     # =========================
#     # SKILLS
#     # =========================
#     y_skills = height - 430
#     c.setFont("Helvetica-Bold", 12)
#     c.drawString(content_x, y_skills, "Top skills covered")

#     c.setFont("Helvetica", 11)
#     c.drawString(content_x, y_skills - 20, "CRVS, Civil Status Registration, Digital Identity")

#     # =========================
#     # SIGNATURE
#     # =========================
#     sig_y = 120
#     c.setFont("Helvetica", 11)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, sig_y + 30, "Alexandre M. YOMO")
#     c.setFont("Helvetica-Oblique", 10)
#     c.drawString(content_x, sig_y + 14, "General Manager, BUNEC")

#     c.setLineWidth(1)
#     c.line(content_x, sig_y + 8, content_x + 260, sig_y + 8)

#     # =========================
#     # QR
#     # =========================
#     try:
#         c.drawImage(
#             ImageReader(qr_path),
#             width - margin - 110,
#             margin + 40,
#             width=80,
#             height=80,
#             preserveAspectRatio=True,
#             mask='auto'
#         )
#     except Exception:
#         pass

#     # =========================
#     # FOOTER
#     # =========================
#     c.setFont("Helvetica", 9)
#     c.setFillColor(text_gray)
#     c.drawCentredString(
#         width / 2,
#         margin + 20,
#         f"Certificate ID: {cert.code}"
#     )

#     c.showPage()
#     c.save()

#     return pdf_path

# def _generate_certificate_pdf(cert: Certification, score: float) -> str:
#     import os
#     import qrcode
#     from django.conf import settings
#     from reportlab.lib.pagesizes import A4, landscape
#     from reportlab.pdfgen import canvas
#     from reportlab.lib import colors
#     from reportlab.lib.utils import ImageReader

#     # =========================
#     # Prepare paths (INCHANGÉ)
#     # =========================
#     media_root = getattr(settings, 'MEDIA_ROOT', '.')
#     out_dir = os.path.join(media_root, 'certificates')
#     os.makedirs(out_dir, exist_ok=True)
#     pdf_path = os.path.join(out_dir, f"{cert.code}.pdf")

#     # =========================
#     # Create QR (INCHANGÉ)
#     # =========================
#     verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
#     scheme = 'https'
#     if settings.DEBUG:
#         scheme = 'http'
#     base_url = f"{scheme}://{verify_host}"

#     media_url = getattr(settings, 'MEDIA_URL', '/media/')
#     if not media_url.endswith('/'):
#         media_url += '/'

#     qr_target = f"{base_url}{media_url}certificates/{cert.code}.pdf"
#     qr_img = qrcode.make(qr_target)
#     qr_path = os.path.join(out_dir, f"{cert.code}.png")
#     qr_img.save(qr_path)

#     # =========================
#     # Try to locate static images (SIGNATURE + CACHET)
#     # =========================
#     signature_path = None
#     cachet_path = None

#     static_candidates = []
#     static_root = getattr(settings, 'STATIC_ROOT', '')
#     if static_root:
#         static_candidates.append(static_root)

#     for p in getattr(settings, 'STATICFILES_DIRS', []):
#         static_candidates.append(p)

#     for base in static_candidates:
#         sig = os.path.join(base, "img", "signature_dg.png")
#         stamp = os.path.join(base, "img", "cachet_bunec.png")
#         if os.path.exists(sig):
#             signature_path = sig
#         if os.path.exists(stamp):
#             cachet_path = stamp

#     # =========================
#     # Build PDF (SEUL LE VISUEL)
#     # =========================
#     c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
#     width, height = landscape(A4)
#     c.setTitle("Certification")

#     # =========================
#     # COLORS
#     # =========================
#     border_color = colors.HexColor("#34495e")
#     ribbon_blue = colors.HexColor("#2c3e50")
#     ribbon_gold = colors.HexColor("#c9a227")
#     text_gray = colors.HexColor("#4b5563")

#     margin = 24

#     # =========================
#     # DOUBLE BORDER
#     # =========================
#     c.setStrokeColor(border_color)
#     c.setLineWidth(4)
#     c.rect(margin, margin, width - 2*margin, height - 2*margin, fill=0)

#     c.setLineWidth(1.5)
#     c.rect(margin + 10, margin + 10, width - 2*(margin + 10), height - 2*(margin + 10), fill=0)

#     # =========================
#     # LEFT RIBBON
#     # =========================
#     ribbon_x = margin + 20
#     ribbon_w = 70

#     c.setFillColor(ribbon_blue)
#     c.rect(ribbon_x, margin + 10, ribbon_w, height - 2*(margin + 10), fill=1, stroke=0)

#     c.setFillColor(ribbon_gold)
#     c.rect(ribbon_x + 5, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)
#     c.rect(ribbon_x + ribbon_w - 11, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)

#     # =========================
#     # MEDAL
#     # =========================
#     medal_cx = ribbon_x + ribbon_w / 2
#     medal_cy = height - 180
#     medal_r = 55

#     c.setFillColor(colors.HexColor("#f5f3e7"))
#     c.setStrokeColor(ribbon_gold)
#     c.setLineWidth(4)
#     c.circle(medal_cx, medal_cy, medal_r, fill=1, stroke=1)

#     c.setFont("Helvetica-Bold", 9)
#     c.setFillColor(ribbon_gold)
#     c.drawCentredString(medal_cx, medal_cy + 14, "LEARNING PATH")
#     c.drawCentredString(medal_cx, medal_cy - 18, "COMPLETION")

#     c.setFont("Helvetica-Bold", 24)
#     c.drawCentredString(medal_cx, medal_cy - 4, "★")

#     # =========================
#     # CONTENT ORIGIN
#     # =========================
#     content_x = ribbon_x + ribbon_w + 60

#     # =========================
#     # HEADER
#     # =========================
#     c.setFont("Helvetica-Bold", 18)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 120, "CRVS TRAININGS")

#     c.setFont("Helvetica", 22)
#     c.drawString(content_x, height - 160, "Certificate of Completion")

#     # =========================
#     # NAME
#     # =========================
#     recipient = (cert.user.get_full_name() or cert.user.username)
#     c.setFont("Helvetica", 14)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, height - 200, f"Congratulations, {recipient}")

#     # =========================
#     # COURSE TITLE
#     # =========================
#     c.setFont("Helvetica-Bold", 28)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 260, cert.course.title)

#     # =========================
#     # LEVEL (RESTORED)
#     # =========================
#     y = height - 300
#     c.setFont("Helvetica", 12)
#     level_label = str(cert.get_level_display() if hasattr(cert, 'get_level_display') else cert.level)
#     c.drawString(content_x, y, f"Level: {level_label}")

#     # =========================
#     # MODULE (RESTORED)
#     # =========================
#     try:
#         mod = cert.course.modules.filter(level=cert.level).first()
#         if mod:
#             y -= 18
#             c.drawString(content_x, y, f"Module: {mod.title}")
#     except Exception:
#         pass

#     # =========================
#     # META DATE
#     # =========================
#     from django.utils import timezone
#     issue_date = timezone.now().strftime('%B %d, %Y')

#     y -= 28
#     c.setFont("Helvetica", 12)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, y, f"Learning program completed on {issue_date}")

#     # =========================
#     # DESCRIPTION
#     # =========================
#     y -= 40
#     text = c.beginText()
#     text.setTextOrigin(content_x, y)
#     text.setFont("Helvetica", 12)
#     text.setFillColor(colors.black)
#     text.textLine("By continuing to learn, you have expanded your perspective,")
#     text.textLine("sharpened your skills, and made yourself even more in demand.")
#     c.drawText(text)

#     # =========================
#     # SKILLS
#     # =========================
#     y -= 80
#     c.setFont("Helvetica-Bold", 12)
#     c.drawString(content_x, y, "Top skills covered")

#     c.setFont("Helvetica", 11)
#     c.drawString(content_x, y - 20, "CRVS, Civil Status Registration, Digital Identity")

#     # =========================
#     # SIGNATURE BLOCK (GAP AJOUTÉ)
#     # =========================
#     sig_y = 110

#     # Signature image
#     if signature_path:
#         try:
#             c.drawImage(
#                 ImageReader(signature_path),
#                 content_x,
#                 sig_y + 35,
#                 width=180,
#                 height=60,
#                 preserveAspectRatio=True,
#                 mask='auto'
#             )
#         except Exception:
#             pass

#     # Signature line
#     c.setLineWidth(1)
#     c.line(content_x, sig_y + 30, content_x + 260, sig_y + 30)

#     # Name + title
#     c.setFont("Helvetica", 11)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, sig_y + 12, "Alexandre M. YOMO")
#     c.setFont("Helvetica-Oblique", 10)
#     c.drawString(content_x, sig_y - 2, "General Manager, BUNEC")

#     # =========================
#     # CACHET
#     # =========================
#     if cachet_path:
#         try:
#             c.drawImage(
#                 ImageReader(cachet_path),
#                 content_x + 320,
#                 sig_y - 10,
#                 width=90,
#                 height=90,
#                 preserveAspectRatio=True,
#                 mask='auto'
#             )
#         except Exception:
#             pass

#     # =========================
#     # QR
#     # =========================
#     try:
#         c.drawImage(
#             ImageReader(qr_path),
#             width - margin - 110,
#             margin + 40,
#             width=80,
#             height=80,
#             preserveAspectRatio=True,
#             mask='auto'
#         )
#     except Exception:
#         pass

#     # =========================
#     # FOOTER
#     # =========================
#     c.setFont("Helvetica", 9)
#     c.setFillColor(text_gray)
#     c.drawCentredString(
#         width / 2,
#         margin + 20,
#         f"Certificate ID: {cert.code}"
#     )

#     c.showPage()
#     c.save()

#     return pdf_path

# def _generate_certificate_pdf(cert: Certification, score: float) -> str:
#     import os
#     import qrcode
#     from django.conf import settings
#     from reportlab.lib.pagesizes import A4, landscape
#     from reportlab.pdfgen import canvas
#     from reportlab.lib import colors
#     from reportlab.lib.utils import ImageReader

#     # =========================
#     # Prepare paths (INCHANGÉ)
#     # =========================
#     media_root = getattr(settings, 'MEDIA_ROOT', '.')
#     out_dir = os.path.join(media_root, 'certificates')
#     os.makedirs(out_dir, exist_ok=True)
#     pdf_path = os.path.join(out_dir, f"{cert.code}.pdf")

#     # =========================
#     # Create QR (INCHANGÉ)
#     # =========================
#     verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
#     scheme = 'https'
#     if settings.DEBUG:
#         scheme = 'http'
#     base_url = f"{scheme}://{verify_host}"

#     media_url = getattr(settings, 'MEDIA_URL', '/media/')
#     if not media_url.endswith('/'):
#         media_url += '/'

#     qr_target = f"{base_url}{media_url}certificates/{cert.code}.pdf"
#     qr_img = qrcode.make(qr_target)
#     qr_path = os.path.join(out_dir, f"{cert.code}.png")
#     qr_img.save(qr_path)

#     # =========================
#     # Locate static images (signature + cachet)
#     # =========================
#     signature_path = None
#     cachet_path = None

#     static_candidates = []
#     static_root = getattr(settings, 'STATIC_ROOT', '')
#     if static_root:
#         static_candidates.append(static_root)
#     for p in getattr(settings, 'STATICFILES_DIRS', []):
#         static_candidates.append(p)

#     for base in static_candidates:
#         sig = os.path.join(base, "img", "signature_dg.png")
#         stamp = os.path.join(base, "img", "cachet_bunec.png")
#         if os.path.exists(sig):
#             signature_path = sig
#         if os.path.exists(stamp):
#             cachet_path = stamp

#     # =========================
#     # Build PDF (VISUEL SEULEMENT)
#     # =========================
#     c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
#     width, height = landscape(A4)
#     c.setTitle("Certification")

#     # =========================
#     # COLORS
#     # =========================
#     border_color = colors.HexColor("#34495e")
#     ribbon_blue = colors.HexColor("#2c3e50")
#     ribbon_gold = colors.HexColor("#c9a227")
#     text_gray = colors.HexColor("#4b5563")

#     margin = 24

#     # =========================
#     # DOUBLE BORDER
#     # =========================
#     c.setStrokeColor(border_color)
#     c.setLineWidth(4)
#     c.rect(margin, margin, width - 2*margin, height - 2*margin, fill=0)
#     c.setLineWidth(1.5)
#     c.rect(margin + 10, margin + 10, width - 2*(margin + 10), height - 2*(margin + 10), fill=0)

#     # =========================
#     # LEFT RIBBON
#     # =========================
#     ribbon_x = margin + 20
#     ribbon_w = 70

#     c.setFillColor(ribbon_blue)
#     c.rect(ribbon_x, margin + 10, ribbon_w, height - 2*(margin + 10), fill=1, stroke=0)

#     c.setFillColor(ribbon_gold)
#     c.rect(ribbon_x + 5, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)
#     c.rect(ribbon_x + ribbon_w - 11, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)

#     # =========================
#     # MEDAL
#     # =========================
#     medal_cx = ribbon_x + ribbon_w / 2
#     medal_cy = height - 180
#     medal_r = 55

#     c.setFillColor(colors.HexColor("#f5f3e7"))
#     c.setStrokeColor(ribbon_gold)
#     c.setLineWidth(4)
#     c.circle(medal_cx, medal_cy, medal_r, fill=1, stroke=1)

#     c.setFont("Helvetica-Bold", 9)
#     c.setFillColor(ribbon_gold)
#     c.drawCentredString(medal_cx, medal_cy + 14, "LEARNING PATH")
#     c.drawCentredString(medal_cx, medal_cy - 18, "COMPLETION")

#     c.setFont("Helvetica-Bold", 24)
#     c.drawCentredString(medal_cx, medal_cy - 4, "★")

#     # =========================
#     # CONTENT ORIGIN
#     # =========================
#     content_x = ribbon_x + ribbon_w + 60

#     # =========================
#     # HEADER
#     # =========================
#     c.setFont("Helvetica-Bold", 18)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 120, "CRVS LEARNING")

#     c.setFont("Helvetica", 22)
#     c.drawString(content_x, height - 160, "Certificate of Completion")

#     # =========================
#     # NAME
#     # =========================
#     recipient = (cert.user.get_full_name() or cert.user.username)
#     c.setFont("Helvetica", 14)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, height - 200, f"Congratulations, {recipient}")

#     # =========================
#     # COURSE TITLE
#     # =========================
#     c.setFont("Helvetica-Bold", 28)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 260, cert.course.title)

#     # =========================
#     # LEVEL
#     # =========================
#     y = height - 300
#     c.setFont("Helvetica", 12)
#     level_label = str(cert.get_level_display() if hasattr(cert, 'get_level_display') else cert.level)
#     c.drawString(content_x, y, f"Level: {level_label}")

#     # =========================
#     # MODULE
#     # =========================
#     try:
#         mod = cert.course.modules.filter(level=cert.level).first()
#         if mod:
#             y -= 18
#             c.drawString(content_x, y, f"Module: {mod.title}")
#     except Exception:
#         pass

#     # =========================
#     # META DATE
#     # =========================
#     from django.utils import timezone
#     issue_date = timezone.now().strftime('%B %d, %Y')

#     y -= 28
#     c.setFont("Helvetica", 12)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, y, f"Learning program completed on {issue_date}")

#     # =========================
#     # DESCRIPTION
#     # =========================
#     y -= 40
#     text = c.beginText()
#     text.setTextOrigin(content_x, y)
#     text.setFont("Helvetica", 12)
#     text.setFillColor(colors.black)
#     text.textLine("By continuing to learn, you have expanded your perspective,")
#     text.textLine("sharpened your skills, and made yourself even more in demand.")
#     c.drawText(text)

#     # =========================
#     # >>> GAP AJOUTÉ ICI (≈ 8px)
#     # =========================
#     sig_y = 110 - 16   # on descend le bloc signature de 8 points

#     # =========================
#     # SIGNATURE BLOCK
#     # =========================

#     # Signature image
#     if signature_path:
#         try:
#             c.drawImage(
#                 ImageReader(signature_path),
#                 content_x,
#                 sig_y + 40,
#                 width=180,
#                 height=60,
#                 preserveAspectRatio=True,
#                 mask='auto'
#             )
#         except Exception:
#             pass

#     # Yellow line under signature
#     c.setStrokeColor(ribbon_gold)
#     c.setLineWidth(2)
#     c.line(content_x, sig_y + 35, content_x + 260, sig_y + 35)

#     # Name + institution
#     c.setFont("Helvetica-Bold", 11)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, sig_y + 18, "Alexandre Marie YOMO")
#     c.setFont("Helvetica", 10)
#     c.drawString(content_x, sig_y + 4, "CRVS Civil Status Registration Office")

#     # Cachet collé à la signature
#     if cachet_path:
#         try:
#             c.drawImage(
#                 ImageReader(cachet_path),
#                 content_x + 190,
#                 sig_y + 10,
#                 width=80,
#                 height=80,
#                 preserveAspectRatio=True,
#                 mask='auto'
#             )
#         except Exception:
#             pass

#     # =========================
#     # QR
#     # =========================
#     try:
#         c.drawImage(
#             ImageReader(qr_path),
#             width - margin - 110,
#             margin + 40,
#             width=80,
#             height=80,
#             preserveAspectRatio=True,
#             mask='auto'
#         )
#     except Exception:
#         pass

#     # =========================
#     # FOOTER
#     # =========================
#     c.setFont("Helvetica", 9)
#     c.setFillColor(text_gray)
#     c.drawCentredString(
#         width / 2,
#         margin + 20,
#         f"Certificate ID: {cert.code}"
#     )

#     c.showPage()
#     c.save()

#     return pdf_path

# def _generate_certificate_pdf(cert: Certification, score: float) -> str:
#     import os
#     import qrcode
#     from django.conf import settings
#     from reportlab.lib.pagesizes import A4, landscape
#     from reportlab.pdfgen import canvas
#     from reportlab.lib import colors
#     from reportlab.lib.utils import ImageReader
#     from django.utils import timezone

#     # =========================
#     # Prepare paths
#     # =========================
#     media_root = getattr(settings, 'MEDIA_ROOT', '.')
#     out_dir = os.path.join(media_root, 'certificates')
#     os.makedirs(out_dir, exist_ok=True)
#     pdf_path = os.path.join(out_dir, f"{cert.code}.pdf")

#     # =========================
#     # Create QR
#     # =========================
#     verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
#     scheme = 'https'
#     if settings.DEBUG:
#         scheme = 'http'
#     base_url = f"{scheme}://{verify_host}"

#     media_url = getattr(settings, 'MEDIA_URL', '/media/')
#     if not media_url.endswith('/'):
#         media_url += '/'

#     qr_target = f"{base_url}{media_url}certificates/{cert.code}.pdf"
#     qr_img = qrcode.make(qr_target)
#     qr_path = os.path.join(out_dir, f"{cert.code}.png")
#     qr_img.save(qr_path)

#     # =========================
#     # Locate static images
#     # =========================
#     signature_path = None
#     cachet_path = None

#     static_candidates = []
#     static_root = getattr(settings, 'STATIC_ROOT', '')
#     if static_root:
#         static_candidates.append(static_root)
#     for p in getattr(settings, 'STATICFILES_DIRS', []):
#         static_candidates.append(p)

#     for base in static_candidates:
#         sig = os.path.join(base, "img", "signature_dg.png")
#         stamp = os.path.join(base, "img", "cachet_bunec.png")
#         if os.path.exists(sig):
#             signature_path = sig
#         if os.path.exists(stamp):
#             cachet_path = stamp

#     # =========================
#     # Build PDF
#     # =========================
#     c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
#     width, height = landscape(A4)
#     c.setTitle("Certification")

#     # =========================
#     # Colors
#     # =========================
#     border_color = colors.HexColor("#34495e")
#     ribbon_blue = colors.HexColor("#2c3e50")
#     ribbon_gold = colors.HexColor("#c9a227")
#     text_gray = colors.HexColor("#4b5563")

#     margin = 24

#     # =========================
#     # Double Border
#     # =========================
#     c.setStrokeColor(border_color)
#     c.setLineWidth(4)
#     c.rect(margin, margin, width - 2*margin, height - 2*margin, fill=0)
#     c.setLineWidth(1.5)
#     c.rect(margin + 10, margin + 10, width - 2*(margin + 10), height - 2*(margin + 10), fill=0)

#     # =========================
#     # Left Ribbon
#     # =========================
#     ribbon_x = margin + 20
#     ribbon_w = 70

#     c.setFillColor(ribbon_blue)
#     c.rect(ribbon_x, margin + 10, ribbon_w, height - 2*(margin + 10), fill=1, stroke=0)

#     c.setFillColor(ribbon_gold)
#     c.rect(ribbon_x + 5, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)
#     c.rect(ribbon_x + ribbon_w - 11, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)

#     # =========================
#     # Medal
#     # =========================
#     medal_cx = ribbon_x + ribbon_w / 2
#     medal_cy = height - 180
#     medal_r = 55

#     c.setFillColor(colors.HexColor("#f5f3e7"))
#     c.setStrokeColor(ribbon_gold)
#     c.setLineWidth(4)
#     c.circle(medal_cx, medal_cy, medal_r, fill=1, stroke=1)

#     c.setFont("Helvetica-Bold", 9)
#     c.setFillColor(ribbon_gold)
#     c.drawCentredString(medal_cx, medal_cy + 14, "LEARNING PATH")
#     c.drawCentredString(medal_cx, medal_cy - 18, "COMPLETION")

#     c.setFont("Helvetica-Bold", 24)
#     c.drawCentredString(medal_cx, medal_cy - 4, "★")

#     # =========================
#     # Content Origin
#     # =========================
#     content_x = ribbon_x + ribbon_w + 60

#     # =========================
#     # Header
#     # =========================
#     c.setFont("Helvetica-Bold", 18)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, height - 120, "CRVS LEARNING")

#     c.setFont("Helvetica", 22)
#     c.drawString(content_x, height - 160, "Certificate of Completion")

#     # =========================
#     # Recipient Name
#     # =========================
#     recipient = (cert.user.get_full_name() or cert.user.username)
#     c.setFont("Helvetica", 14)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, height - 200, f"Congratulations, {recipient}")

#     # =========================
#     # Certificate Title (big and bold at the top)
#     # =========================
#     y = height - 260  # Starting position
#     if cert.title:
#         c.setFont("Helvetica-Bold", 32)  # Bigger and bold for certificate title
#         c.setFillColor(colors.black)
#         c.drawString(content_x, y, cert.title)
#         y -= 40  # Add some space after the title
    
#     # =========================
#     # Course Title + Module (same line, same size as level)
#     # =========================
#     c.setFont("Helvetica-Bold", 12)  # Same size as level
#     course_title = cert.course.title
#     c.drawString(content_x, y, course_title)
    
#     # Add module title on the same line if available
#     try:
#         mod = cert.course.modules.filter(level=cert.level).first()
#         if mod:
#             # Calculate position for module title
#             course_title_width = c.stringWidth(course_title, "Helvetica-Bold", 12)
#             text_gap = 5
#             c.drawString(content_x + course_title_width + text_gap, y, f"- {mod.title}")
#     except Exception:
#         pass
    
#     # =========================
#     # Level (below course and module)
#     # =========================
#     y -= 24  # Space before level
#     c.setFont("Helvetica", 12)  # Same size as course and module
#     level_label = str(cert.get_level_display() if hasattr(cert, 'get_level_display') else cert.level)
#     c.drawString(content_x, y, f"Level: {level_label}")
#     y -= 30  # Space after level for next section

#     # =========================
#     # Meta Date
#     # =========================
#     issue_date = timezone.now().strftime('%B %d, %Y')
#     y -= 2
#     c.setFont("Helvetica", 12)
#     c.setFillColor(text_gray)
#     c.drawString(content_x, y, f"Learning program completed on {issue_date}")

#     # =========================
#     # Description
#     # =========================
#     y -= 40
#     text = c.beginText()
#     text.setTextOrigin(content_x, y)
#     text.setFont("Helvetica", 12)
#     text.setFillColor(colors.black)
#     text.textLine("By continuing to learn, you have expanded your perspective,")
#     text.textLine("sharpened your skills, and made yourself even more in demand.")
#     c.drawText(text)

#     # =========================
#     # Gap before signature (≈ 8px)
#     # =========================
#     sig_y = 110 - 16

#     # =========================
#     # Signature Block
#     # =========================
#     if signature_path:
#         try:
#             c.drawImage(
#                 ImageReader(signature_path),
#                 content_x,
#                 sig_y + 40,
#                 width=180,
#                 height=60,
#                 preserveAspectRatio=True,
#                 mask='auto'
#             )
#         except Exception:
#             pass

#     # Yellow line under signature
#     c.setStrokeColor(ribbon_gold)
#     c.setLineWidth(2)
#     c.line(content_x, sig_y + 35, content_x + 260, sig_y + 35)

#     # Name + institution
#     c.setFont("Helvetica-Bold", 11)
#     c.setFillColor(colors.black)
#     c.drawString(content_x, sig_y + 18, "Alexandre Marie YOMO")
#     c.setFont("Helvetica", 10)
#     c.drawString(content_x, sig_y + 4, "CRVS Civil Status Registration Office")

#     # Cachet collé à la signature
#     if cachet_path:
#         try:
#             c.drawImage(
#                 ImageReader(cachet_path),
#                 content_x + 190,
#                 sig_y + 10,
#                 width=80,
#                 height=80,
#                 preserveAspectRatio=True,
#                 mask='auto'
#             )
#         except Exception:
#             pass

#     # =========================
#     # QR
#     # =========================
#     try:
#         c.drawImage(
#             ImageReader(qr_path),
#             width - margin - 110,
#             margin + 40,
#             width=80,
#             height=80,
#             preserveAspectRatio=True,
#             mask='auto'
#         )
#     except Exception:
#         pass

#     # =========================
#     # Footer
#     # =========================
#     c.setFont("Helvetica", 9)
#     c.setFillColor(text_gray)
#     c.drawCentredString(
#         width / 2,
#         margin + 20,
#         f"Certificate ID: {cert.code}"
#     )

#     c.showPage()
#     c.save()

#     return pdf_path

def _generate_certificate_pdf(cert: Certification, score: float) -> str:
    import os
    import qrcode
    from django.conf import settings
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from django.utils import timezone

    # =========================
    # Prepare paths
    # =========================
    media_root = getattr(settings, 'MEDIA_ROOT', '.')
    out_dir = os.path.join(media_root, 'certificates')
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, f"{cert.code}.pdf")

    # =========================
    # Create QR
    # =========================
    verify_host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', []) else 'localhost'
    scheme = 'https'
    if settings.DEBUG:
        scheme = 'http'
    base_url = f"{scheme}://{verify_host}"

    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    if not media_url.endswith('/'):
        media_url += '/'

    qr_target = f"{base_url}{media_url}certificates/{cert.code}.pdf"
    qr_img = qrcode.make(qr_target)
    qr_path = os.path.join(out_dir, f"{cert.code}.png")
    qr_img.save(qr_path)

    # =========================
    # Locate static images
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
    # Build PDF
    # =========================
    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setTitle("Certification")

    # =========================
    # Colors
    # =========================
    border_color = colors.HexColor("#34495e")
    ribbon_blue = colors.HexColor("#2c3e50")
    ribbon_gold = colors.HexColor("#c9a227")
    text_gray = colors.HexColor("#4b5563")

    margin = 24

    # =========================
    # Double Border
    # =========================
    c.setStrokeColor(border_color)
    c.setLineWidth(4)
    c.rect(margin, margin, width - 2*margin, height - 2*margin, fill=0)
    c.setLineWidth(1.5)
    c.rect(margin + 10, margin + 10, width - 2*(margin + 10), height - 2*(margin + 10), fill=0)

    # =========================
    # Left Ribbon
    # =========================
    ribbon_x = margin + 20
    ribbon_w = 70

    c.setFillColor(ribbon_blue)
    c.rect(ribbon_x, margin + 10, ribbon_w, height - 2*(margin + 10), fill=1, stroke=0)

    c.setFillColor(ribbon_gold)
    c.rect(ribbon_x + 5, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)
    c.rect(ribbon_x + ribbon_w - 11, margin + 10, 6, height - 2*(margin + 10), fill=1, stroke=0)

    # =========================
    # Medal
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
    c.drawCentredString(medal_cx, medal_cy + 14, "LEARNING PATH")
    c.drawCentredString(medal_cx, medal_cy - 18, "COMPLETION")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(medal_cx, medal_cy - 4, "★")

    # =========================
    # Content Origin
    # =========================
    content_x = ribbon_x + ribbon_w + 60

    # =========================
    # Header
    # =========================
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.black)
    c.drawString(content_x, height - 120, "CRVS LEARNING")

    c.setFont("Helvetica", 22)
    c.drawString(content_x, height - 160, "Certificate of Completion")

    # =========================
    # Recipient Name
    # =========================
    recipient = (cert.user.get_full_name() or cert.user.username)
    c.setFont("Helvetica", 14)
    c.setFillColor(text_gray)
    c.drawString(content_x, height - 200, f"Congratulations, {recipient}")

    # =========================
    # Certificate Title (big and bold at the top)
    # =========================
    y = height - 260  # Starting position
    if cert.title:
        c.setFont("Helvetica-Bold", 32)  # Bigger and bold for certificate title
        c.setFillColor(colors.black)
        c.drawString(content_x, y, cert.title)
        y -= 40  # Add some space after the title
    
    # =========================
    # Course Title (without module)
    # =========================
    c.setFont("Helvetica-Bold", 12)  # Same size as level
    course_title = cert.course.title
    c.drawString(content_x, y, course_title)
    
    # =========================
    # Level (below course title)
    # =========================
    y -= 24  # Space before level
    c.setFont("Helvetica", 12)  # Same size as course and module
    level_label = str(cert.get_level_display() if hasattr(cert, 'get_level_display') else cert.level)
    c.drawString(content_x, y, f"Level: {level_label}")
    y -= 30  # Space after level for next section

    # =========================
    # Meta Date
    # =========================
    issue_date = timezone.now().strftime('%B %d, %Y')
    y -= 2
    c.setFont("Helvetica", 12)
    c.setFillColor(text_gray)
    c.drawString(content_x, y, f"Learning program completed on {issue_date}")

    # =========================
    # Description
    # =========================
    y -= 40
    text = c.beginText()
    text.setTextOrigin(content_x, y)
    text.setFont("Helvetica", 12)
    text.setFillColor(colors.black)
    text.textLine("By continuing to learn, you have expanded your perspective,")
    text.textLine("sharpened your skills, and made yourself even more in demand.")
    c.drawText(text)

    # =========================
    # Gap before signature (≈ 8px)
    # =========================
    sig_y = 110 - 16

    # =========================
    # Signature Block
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
    c.drawString(content_x, sig_y + 4, "CRVS Civil Status Registration Office")

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
    # QR
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
    # Footer
    # =========================
    c.setFont("Helvetica", 9)
    c.setFillColor(text_gray)
    c.drawCentredString(
        width / 2,
        margin + 20,
        f"Certificate ID: {cert.code}"
    )

    c.showPage()
    c.save()

    return pdf_path




@login_required
def start_evaluation(request: HttpRequest, course_id: int, level: str) -> HttpResponse:
    course = get_object_or_404(Course, id=course_id)
    evaluation = get_object_or_404(EvaluationLevel, course=course, level=level, is_active=True)

    # Gate: ensure level is completed
    comp = _user_level_completion(request.user, course, level)
    if not comp["completed"]:
        messages.error(request, "Veuillez compléter toutes les leçons de ce niveau avant l'évaluation.")
        return redirect('courses:course_detail', course_id=course.id)

    # Enforce attempts rule: max 3 attempts total unless a success occurred earlier
    attempts_qs = Attempt.objects.filter(user=request.user, evaluation=evaluation)
    already_passed = attempts_qs.filter(passed=True).exists()
    attempts_count = attempts_qs.count()
    if already_passed:
        messages.error(request, "Vous avez déjà réussi cette évaluation. Nouvelle tentative non autorisée.")
        return redirect('courses:course_detail', course_id=course.id)
    if attempts_count >= 3:
        messages.error(request, "Nombre maximum de 3 tentatives atteint pour cette évaluation.")
        return redirect('courses:course_detail', course_id=course.id)

    if request.method == 'POST':
        # QCM grading
        questions = list(EvaluationQuestion.objects.filter(evaluation=evaluation).prefetch_related('choices'))
        total_points = sum(q.points for q in questions) or 1
        earned_points = 0

        attempt = Attempt.objects.create(user=request.user, evaluation=evaluation, score=0.0, passed=False)

        for q in questions:
            choice_id = request.POST.get(f'q_{q.id}')
            chosen = None
            if choice_id:
                try:
                    chosen = EvaluationChoice.objects.get(id=int(choice_id), question=q)
                except (EvaluationChoice.DoesNotExist, ValueError):
                    chosen = None
            AttemptAnswer.objects.create(attempt=attempt, question=q, choice=chosen)
            if chosen and chosen.is_correct:
                earned_points += q.points

        percent = round((earned_points / total_points) * 100, 2)
        passed = percent >= evaluation.threshold
        attempt.score = percent
        attempt.passed = passed
        attempt.save(update_fields=['score', 'passed'])

        if passed:
            # Create or get Certification
            cert, created = Certification.objects.get_or_create(
                user=request.user, 
                course=course, 
                level=level,
                defaults={'title': evaluation.title}
            )
            # Generate PDF if not set
            if not cert.pdf:
                pdf_path = _generate_certificate_pdf(cert, percent)
                media_root = getattr(settings, 'MEDIA_ROOT', '')
                try:
                    rel_path = os.path.relpath(str(pdf_path), str(media_root))
                except Exception:
                    rel_path = str(pdf_path)
                rel_path = rel_path.lstrip(os.sep)
                cert.pdf.name = rel_path
                cert.save()

            # 🎉 SWEETALERT DE FÉLICITATIONS
            request.session['evaluation_success_message'] = {
                'title': '🎉 FÉLICITATIONS !',
                'message': f'Vous avez brillamment réussi l\'évaluation "<strong>{evaluation.title}</strong>" avec un score de <strong>{percent}%</strong> !<br><br>Votre certificat a été généré et est disponible dans votre espace personnel.',
                'icon': 'success',
                'showConfirmButton': True,
                'confirmButtonText': 'Voir mon certificat',
                'timer': 8000,
                'timerProgressBar': True,
                'background': 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
                'color': '#fff'
            }
            
            messages.success(request, f"Félicitations ! Vous avez réussi avec {percent}%.")
            return redirect('courses:course_detail', course_id=course.id)
        else:
            # 💪 SWEETALERT D'ENCOURAGEMENT
            remaining_attempts = 3 - attempts_count
            request.session['evaluation_failure_message'] = {
                'title': '💪 CONTINUEZ VOS EFFORTS !',
                'message': f'Vous avez obtenu <strong>{percent}%</strong> à l\'évaluation "<strong>{evaluation.title}</strong>".<br><br>Ne vous découragez pas ! Chaque tentative vous rapproche du succès.<br><br><strong>Il vous reste {remaining_attempts} tentative{"s" if remaining_attempts > 1 else ""}.</strong>',
                'icon': 'info',
                'showConfirmButton': True,
                'confirmButtonText': 'Réessayer',
                'timer': 6000,
                'timerProgressBar': True,
                'background': 'linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)',
                'color': '#fff'
            }
            
            messages.error(request, f"Échec à l'évaluation ({percent}%). Vous pouvez réessayer.")
            return redirect('evaluations:start_level_evaluation', course_id=course.id, level=level)

    # GET: render QCM
    questions = EvaluationQuestion.objects.filter(evaluation=evaluation).prefetch_related('choices')
    return render(request, 'evaluations/start_evaluation.html', {
        'course': course,
        'evaluation': evaluation,
        'level': level,
        'threshold': evaluation.threshold,
        'questions': questions,
    })
