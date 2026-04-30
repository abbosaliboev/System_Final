import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from django.conf import settings
from io import BytesIO
from django.utils.dateparse import parse_datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .models import Report
from datetime import datetime

# ✅ Register Korean font (NanumGothic) using absolute path
_FONT_PATH = os.path.join(settings.BASE_DIR, 'assets', 'fonts', 'NanumGothic-Regular.ttf')
pdfmetrics.registerFont(TTFont('NanumGothic', _FONT_PATH))

class GeneratePDFReportView(APIView):
    def post(self, request):
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=400)

        try:
            start = parse_datetime(start_date)
            end = parse_datetime(end_date)
        except:
            return Response({"error": "Invalid date format"}, status=400)

        reports = Report.objects.filter(timestamp__range=(start, end)).order_by('timestamp')
        if not reports.exists():
            return Response({"error": "No reports found in this time range"}, status=404)

        # Prepare PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        styles = getSampleStyleSheet()

        # ✅ Use Korean font in styles
        styles['Title'].fontName = 'NanumGothic'
        styles['Normal'].fontName = 'NanumGothic'

        elements = []

        elements.append(Paragraph("직원 안전관리 현황 보고서", styles['Title']))
        elements.append(Spacer(1, 12))

        # Group by workerId
        workers = {}
        for r in reports:
            workers.setdefault(r.workerId, []).append(r)

        for workerId, entries in workers.items():
            first = entries[0]

            # Header info
            elements.append(Paragraph(f"<b>근로자명:</b> {first.worker}    <b>사원번호:</b> {first.workerId}", styles['Normal']))
            elements.append(Paragraph(f"<b>책임자:</b> {first.supervisor}    <b>ID:</b> {first.camera_id}", styles['Normal']))
            elements.append(Spacer(1, 12))

            # Table
            data = [['순번', '경고 일시', '이벤트', '조치 내용']]
            for i, entry in enumerate(entries, start=1):
                time_str = entry.timestamp.strftime('%Y-%m-%d %H:%M')
                data.append([str(i), time_str, entry.event, '경고 및 면담'])

            table = Table(data, colWidths=[40, 130, 150, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),  # ✅ Apply font to table
            ]))
            elements.append(table)
            elements.append(Spacer(1, 24))

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='report_summary.pdf')
