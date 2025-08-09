from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
import os
from typing import Optional

from ..models import Acceptance, AcceptanceDefect


class PDFService:
    """Service für PDF-Generierung"""
    
    @staticmethod
    def generate_acceptance_protocol(acceptance: Acceptance) -> str:
        """Generiere Abnahmeprotokoll als PDF"""
        try:
            # Erstelle Verzeichnis falls nicht vorhanden (projektbasiert, wenn bekannt)
            project_id = data.get('project_id') if isinstance(data, dict) else None
            pdf_dir = f"storage/acceptances/project_{project_id}" if project_id else "storage/acceptances"
            os.makedirs(pdf_dir, exist_ok=True)
            
            # PDF-Dateiname
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"abnahmeprotokoll_{acceptance.id}_{timestamp}.pdf"
            filepath = os.path.join(pdf_dir, filename)
            
            # PDF-Dokument erstellen
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20
            )
            
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            normal_style.spaceAfter = 6
            
            # Story (Inhalt) sammeln
            story = []
            
            # Titel
            story.append(Paragraph("ABNAHMEPROTOKOLL", title_style))
            story.append(Spacer(1, 12))
            
            # Projekt-Informationen
            story.append(Paragraph("1. PROJEKT-INFORMATIONEN", heading_style))
            
            project_data = [
                ['Projekt:', acceptance.project.title if acceptance.project else 'N/A'],
                ['Gewerk:', acceptance.milestone.title if acceptance.milestone else 'N/A'],
                ['Projekt-Nr.:', f"P-{acceptance.project_id}" if acceptance.project_id else 'N/A'],
                ['Gewerk-Nr.:', f"M-{acceptance.milestone_id}" if acceptance.milestone_id else 'N/A'],
                ['Abnahme-Nr.:', f"A-{acceptance.id}"],
            ]
            
            if acceptance.project and hasattr(acceptance.project, 'address'):
                project_data.append(['Adresse:', acceptance.project.address or 'N/A'])
            
            project_table = Table(project_data, colWidths=[4*cm, 12*cm])
            project_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(project_table)
            story.append(Spacer(1, 20))
            
            # Teilnehmer
            story.append(Paragraph("2. TEILNEHMER", heading_style))
            
            participants_data = [
                ['Bauträger/Auftraggeber:', f"{acceptance.contractor.first_name} {acceptance.contractor.last_name}" if acceptance.contractor else 'N/A'],
                ['E-Mail:', acceptance.contractor.email if acceptance.contractor else 'N/A'],
                ['Dienstleister/Auftragnehmer:', f"{acceptance.service_provider.first_name} {acceptance.service_provider.last_name}" if acceptance.service_provider else 'N/A'],
                ['E-Mail:', acceptance.service_provider.email if acceptance.service_provider else 'N/A'],
            ]
            
            participants_table = Table(participants_data, colWidths=[4*cm, 12*cm])
            participants_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(participants_table)
            story.append(Spacer(1, 20))
            
            # Abnahme-Details
            story.append(Paragraph("3. ABNAHME-DETAILS", heading_style))
            
            # Status formatieren
            status_text = "Abgenommen" if acceptance.accepted else "Unter Vorbehalt" if acceptance.accepted is False else "Offen"
            acceptance_type_text = {
                'FINAL': 'Endabnahme',
                'PARTIAL': 'Teilabnahme', 
                'TECHNICAL': 'Technische Abnahme',
                'VISUAL': 'Sichtabnahme'
            }.get(acceptance.acceptance_type.value if acceptance.acceptance_type else 'FINAL', 'Endabnahme')
            
            details_data = [
                ['Art der Abnahme:', acceptance_type_text],
                ['Status:', status_text],
                ['Abnahme-Datum:', acceptance.completed_at.strftime("%d.%m.%Y %H:%M") if acceptance.completed_at else 'N/A'],
                ['Beginn der Abnahme:', acceptance.started_at.strftime("%d.%m.%Y %H:%M") if acceptance.started_at else 'N/A'],
            ]
            
            if acceptance.warranty_start_date:
                details_data.append(['Gewährleistungsbeginn:', acceptance.warranty_start_date.strftime("%d.%m.%Y")])
                details_data.append(['Gewährleistungszeit:', f"{acceptance.warranty_period_months} Monate"])
            
            details_table = Table(details_data, colWidths=[4*cm, 12*cm])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 20))
            
            # Bewertung
            if acceptance.overall_rating:
                story.append(Paragraph("4. BEWERTUNG", heading_style))
                
                rating_data = []
                if acceptance.quality_rating:
                    rating_data.append(['Qualität der Arbeiten:', f"{acceptance.quality_rating}/5 Sterne"])
                if acceptance.timeliness_rating:
                    rating_data.append(['Termintreue:', f"{acceptance.timeliness_rating}/5 Sterne"])
                if acceptance.overall_rating:
                    rating_data.append(['Gesamtbewertung:', f"{acceptance.overall_rating}/5 Sterne"])
                
                if rating_data:
                    rating_table = Table(rating_data, colWidths=[4*cm, 12*cm])
                    rating_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ]))
                    story.append(rating_table)
                    story.append(Spacer(1, 20))
            
            # Notizen
            if acceptance.acceptance_notes or acceptance.contractor_notes:
                story.append(Paragraph("5. NOTIZEN UND BEMERKUNGEN", heading_style))
                
                if acceptance.acceptance_notes:
                    story.append(Paragraph("<b>Allgemeine Notizen:</b>", normal_style))
                    story.append(Paragraph(acceptance.acceptance_notes, normal_style))
                    story.append(Spacer(1, 10))
                
                if acceptance.contractor_notes:
                    story.append(Paragraph("<b>Notizen des Bauträgers:</b>", normal_style))
                    story.append(Paragraph(acceptance.contractor_notes, normal_style))
                    story.append(Spacer(1, 20))
            
            # Mängel
            if acceptance.defects and len(acceptance.defects) > 0:
                story.append(Paragraph("6. MÄNGELLISTE", heading_style))
                
                defect_data = [['Nr.', 'Titel', 'Schweregrad', 'Ort', 'Beschreibung']]
                
                for i, defect in enumerate(acceptance.defects, 1):
                    severity_text = {
                        'MINOR': 'Geringfügig',
                        'MAJOR': 'Erheblich', 
                        'CRITICAL': 'Kritisch'
                    }.get(defect.severity.value if defect.severity else 'MINOR', 'Geringfügig')
                    
                    defect_data.append([
                        str(i),
                        defect.title or 'N/A',
                        severity_text,
                        f"{defect.location or ''} {defect.room or ''}".strip() or 'N/A',
                        defect.description or 'N/A'
                    ])
                
                defect_table = Table(defect_data, colWidths=[1*cm, 4*cm, 2.5*cm, 3*cm, 5.5*cm])
                defect_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(defect_table)
                story.append(Spacer(1, 20))
            
            # Rechtliche Hinweise
            story.append(Paragraph("7. RECHTLICHE HINWEISE", heading_style))
            
            legal_text = """
            <b>Gewährleistung:</b><br/>
            Mit der Abnahme beginnt die Gewährleistungszeit gemäß BGB. Die Gewährleistungszeit beträgt bei Bauwerken 5 Jahre, 
            bei beweglichen Sachen 2 Jahre ab Abnahme.<br/><br/>
            
            <b>Mängel:</b><br/>
            Offensichtliche Mängel, die bei der Abnahme nicht gerügt wurden, können später nicht mehr geltend gemacht werden. 
            Versteckte Mängel können innerhalb der Gewährleistungszeit gerügt werden.<br/><br/>
            
            <b>Beweislast:</b><br/>
            Nach der Abnahme liegt die Beweislast für Mängel beim Auftraggeber.
            """
            
            story.append(Paragraph(legal_text, normal_style))
            story.append(Spacer(1, 30))
            
            # Unterschriften
            story.append(Paragraph("8. UNTERSCHRIFTEN", heading_style))
            
            signature_data = [
                ['', '', ''],
                ['Datum, Ort', 'Bauträger/Auftraggeber', 'Dienstleister/Auftragnehmer'],
                ['', '', ''],
                ['', '', ''],
                [f"{datetime.now().strftime('%d.%m.%Y')}, {acceptance.project.address if acceptance.project and hasattr(acceptance.project, 'address') else 'BuildWise'}", 
                 f"{acceptance.contractor.first_name} {acceptance.contractor.last_name}" if acceptance.contractor else '',
                 f"{acceptance.service_provider.first_name} {acceptance.service_provider.last_name}" if acceptance.service_provider else '']
            ]
            
            signature_table = Table(signature_data, colWidths=[5*cm, 5.5*cm, 5.5*cm])
            signature_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LINEABOVE', (1, 3), (1, 3), 1, colors.black),
                ('LINEABOVE', (2, 3), (2, 3), 1, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(signature_table)
            
            # Footer
            story.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
            story.append(Paragraph(f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} mit BuildWise", footer_style))
            
            # PDF generieren
            doc.build(story)
            
            print(f"✅ PDF-Abnahmeprotokoll erstellt: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Fehler bei PDF-Generierung: {e}")
            raise


    @staticmethod
    def generate_defect_report(acceptance: Acceptance) -> Optional[str]:
        """Generiere separaten Mängelbericht als PDF"""
        if not acceptance.defects or len(acceptance.defects) == 0:
            return None
            
        try:
            # Erstelle Verzeichnis falls nicht vorhanden (projektbasiert, wenn bekannt)
            project_id = data.get('project_id') if isinstance(data, dict) else None
            pdf_dir = f"storage/acceptances/project_{project_id}" if project_id else "storage/acceptances"
            os.makedirs(pdf_dir, exist_ok=True)
            
            # PDF-Dateiname
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"maengelbericht_{acceptance.id}_{timestamp}.pdf"
            filepath = os.path.join(pdf_dir, filename)
            
            # PDF-Dokument erstellen
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Story sammeln
            story = []
            
            # Titel
            story.append(Paragraph("MÄNGELBERICHT", title_style))
            story.append(Spacer(1, 12))
            
            # Projekt-Info
            story.append(Paragraph(f"<b>Projekt:</b> {acceptance.project.title if acceptance.project else 'N/A'}", styles['Normal']))
            story.append(Paragraph(f"<b>Gewerk:</b> {acceptance.milestone.title if acceptance.milestone else 'N/A'}", styles['Normal']))
            story.append(Paragraph(f"<b>Abnahme-Nr.:</b> A-{acceptance.id}", styles['Normal']))
            story.append(Paragraph(f"<b>Datum:</b> {datetime.now().strftime('%d.%m.%Y')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Mängel-Tabelle
            defect_data = [['Nr.', 'Titel', 'Schweregrad', 'Ort/Raum', 'Beschreibung', 'Status']]
            
            for i, defect in enumerate(acceptance.defects, 1):
                severity_text = {
                    'MINOR': 'Geringfügig',
                    'MAJOR': 'Erheblich',
                    'CRITICAL': 'Kritisch'
                }.get(defect.severity.value if defect.severity else 'MINOR', 'Geringfügig')
                
                status_text = 'Behoben' if defect.resolved else 'Offen'
                location = f"{defect.location or ''} {defect.room or ''}".strip() or 'N/A'
                
                defect_data.append([
                    str(i),
                    defect.title or 'N/A',
                    severity_text,
                    location,
                    defect.description or 'N/A',
                    status_text
                ])
            
            defect_table = Table(defect_data, colWidths=[1*cm, 3.5*cm, 2*cm, 2.5*cm, 5*cm, 2*cm])
            defect_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(defect_table)
            
            # PDF generieren
            doc.build(story)
            
            print(f"✅ Mängelbericht erstellt: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Fehler bei Mängelbericht-Generierung: {e}")
            return None