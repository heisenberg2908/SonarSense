"""
Report generation module for SonarSense
Generates PDF and CSV reports with waveform plots and predictions
"""
import os
import io
import base64
from datetime import datetime
from typing import Dict, Optional
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
import csv

class ReportGenerator:
    """Generate reports for sonar classification results"""
    
    def __init__(self, output_dir='reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_waveform_plot(self, time_data: np.ndarray, amplitude_data: np.ndarray) -> str:
        """Generate waveform plot and return as base64 image"""
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(time_data, amplitude_data, linewidth=0.5, color='#2563eb')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Sonar Signal Waveform')
        ax.grid(True, alpha=0.3)
        
       
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64
    
    def generate_frequency_plot(self, freq_data: np.ndarray, magnitude_data: np.ndarray) -> str:
        """Generate frequency spectrum plot and return as base64 image"""
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(freq_data, magnitude_data, linewidth=0.5, color='#7c3aed')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Magnitude')
        ax.set_title('Frequency Spectrum')
        ax.set_xlim(0, 8000)  
        ax.grid(True, alpha=0.3)
        
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64
    
    def generate_pdf_report(self, result_data: Dict, result_id: int) -> str:
        """
        Generate PDF report for a classification result
        
        Args:
            result_data: Dictionary containing prediction results and metadata
            result_id: Unique result ID
        
        Returns:
            Path to generated PDF file
        """
        filename = f"sonar_report_{result_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
       
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        
        story.append(Paragraph("SonarSense Classification Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        
        story.append(Paragraph("Report Information", heading_style))
        
        report_info = [
            ['Report ID:', str(result_id)],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Analysis Time:', result_data.get('timestamp', 'N/A')],
        ]
        
        table = Table(report_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4b5563')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3 * inch))
        
        
        story.append(Paragraph("Classification Results", heading_style))
        
        prediction = result_data.get('label', result_data.get('prediction', 'Unknown'))
        confidence = result_data.get('confidence', 0)
        
        results_info = [
            ['Detected Object:', prediction],
            ['Confidence Score:', f"{confidence * 100:.2f}%"],
            ['Classification:', 'High Confidence' if confidence > 0.8 else 'Medium Confidence' if confidence > 0.6 else 'Low Confidence'],
        ]
        
        table = Table(results_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4b5563')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 14),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#059669')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fdf4')),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3 * inch))
        
        
        if 'waveform_data' in result_data and result_data['waveform_data']:
            story.append(Paragraph("Signal Waveform", heading_style))
            
            waveform_data = result_data['waveform_data']
            if 'time' in waveform_data and 'amplitude' in waveform_data:
                time = np.array(waveform_data['time'])
                amplitude = np.array(waveform_data['amplitude'])
                
                img_base64 = self.generate_waveform_plot(time, amplitude)
                img_data = base64.b64decode(img_base64)
                img = Image(io.BytesIO(img_data), width=6*inch, height=2.4*inch)
                story.append(img)
                story.append(Spacer(1, 0.2 * inch))
        
       
        if 'frequency_data' in result_data and result_data['frequency_data']:
            story.append(Paragraph("Frequency Spectrum", heading_style))
            
            freq_data = result_data['frequency_data']
            if 'frequency' in freq_data and 'magnitude' in freq_data:
                frequency = np.array(freq_data['frequency'])
                magnitude = np.array(freq_data['magnitude'])
                
                img_base64 = self.generate_frequency_plot(frequency, magnitude)
                img_data = base64.b64decode(img_base64)
                img = Image(io.BytesIO(img_data), width=6*inch, height=2.4*inch)
                story.append(img)
                story.append(Spacer(1, 0.2 * inch))
       
        if 'user_meta' in result_data and result_data['user_meta']:
            story.append(Paragraph("Additional Metadata", heading_style))
            
            meta_info = [[k, str(v)] for k, v in result_data['user_meta'].items()]
            if meta_info:
                table = Table(meta_info, colWidths=[2*inch, 4*inch])
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4b5563')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(table)
        
       
        story.append(Spacer(1, 0.5 * inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("SonarSense © 2024 | AI-Powered Sonar Object Detection", footer_style))
        
        doc.build(story)
        
        return filepath
    
    def generate_csv_report(self, results: list, filename: Optional[str] = None) -> str:
        """
        Generate CSV report for multiple results
        
        Args:
            results: List of result dictionaries
            filename: Optional custom filename
        
        Returns:
            Path to generated CSV file
        """
        if filename is None:
            filename = f"sonar_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['id', 'prediction', 'confidence', 'timestamp', 'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'id': result.get('id', ''),
                    'prediction': result.get('prediction', result.get('label', '')),
                    'confidence': result.get('confidence', 0),
                    'timestamp': result.get('timestamp', ''),
                    'created_at': result.get('created_at', '')
                })
        
        return filepath
