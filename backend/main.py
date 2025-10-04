from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import unquote
from pathlib import Path
import shutil
import os
import uuid
import json

from obfuscate import obfuscate_code
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

app = FastAPI(title="LLVM Obfuscation API")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory in backend folder
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def generate_pdf_report(json_report_path, pdf_output_path):
    """Generate a PDF report from the JSON obfuscation report"""
    
    # Load JSON report
    with open(json_report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.darkblue
    )
    
    # Story to hold PDF content
    story = []
    
    # Title
    story.append(Paragraph("LLVM Obfuscation Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata section
    story.append(Paragraph("Metadata", heading_style))
    metadata = report_data.get('metadata', {})
    metadata_data = [
        ["Timestamp", metadata.get('timestamp', 'N/A')],
        ["Input File", metadata.get('input_file', 'N/A')],
        ["Output File", metadata.get('output_file', 'N/A')],
        ["Obfuscation Level", metadata.get('obfuscation_level', 'N/A')],
        ["Security Rating", metadata.get('security_rating', 'N/A')]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[1.5*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Metrics section
    story.append(Paragraph("Obfuscation Metrics", heading_style))
    metrics = report_data.get('metrics', {})
    metrics_data = [
        ["Metric", "Value"],
        ["Strings Encrypted", metrics.get('strings_encrypted', 0)],
        ["Functions Renamed", metrics.get('functions_renamed', 0)],
        ["Globals Renamed", metrics.get('globals_renamed', 0)],
        ["Bogus Instructions", metrics.get('bogus_instr_count', 0)],
        ["Control Flow Obfuscated", "Yes" if metrics.get('control_flow_obfuscated', 0) else "No"],
        ["Opaque Predicates", metrics.get('opaque_predicates_added', 0)],
        ["Anti-Debugging Checks", metrics.get('anti_debugging_checks', 0)],
        ["Basic Blocks Split", metrics.get('basic_blocks_split', 0)]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Timing section
    story.append(Paragraph("Timing Information", heading_style))
    timing = report_data.get('timing', {})
    timing_data = [
        ["Total Duration", timing.get('total_duration', 'N/A')],
        ["Average Pass Time", timing.get('average_pass_time', 'N/A')],
        ["Slowest Pass", timing.get('slowest_pass', 'N/A')],
        ["Fastest Pass", timing.get('fastest_pass', 'N/A')]
    ]
    
    timing_table = Table(timing_data, colWidths=[2*inch, 3*inch])
    timing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(timing_table)
    story.append(Spacer(1, 0.2*inch))
    
    # File Sizes section
    story.append(Paragraph("File Sizes", heading_style))
    file_sizes = report_data.get('file_sizes', {})
    file_sizes_data = [
        ["File Type", "Size (bytes)"],
        ["Input Size", file_sizes.get('input_size', 0)],
        ["Output Size", file_sizes.get('output_size', 0)],
        ["Largest BC", file_sizes.get('largest_bc', 0)],
        ["Smallest BC", file_sizes.get('smallest_bc', 0)],
        ["Largest LL", file_sizes.get('largest_ll', 0)],
        ["Smallest LL", file_sizes.get('smallest_ll', 0)]
    ]
    
    file_sizes_table = Table(file_sizes_data, colWidths=[2*inch, 1.5*inch])
    file_sizes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(file_sizes_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Summary section
    story.append(Paragraph("Summary", heading_style))
    summary = report_data.get('summary', {})
    
    # Key Achievements
    story.append(Paragraph("Key Achievements", subheading_style))
    achievements = summary.get('key_achievements', [])
    for achievement in achievements:
        story.append(Paragraph(f"• {achievement}", styles['Normal']))
    
    story.append(Spacer(1, 0.1*inch))
    
    # Recommendations
    story.append(Paragraph("Recommendations", subheading_style))
    recommendations = summary.get('recommendations', [])
    if recommendations:
        for recommendation in recommendations:
            story.append(Paragraph(f"• {recommendation}", styles['Normal']))
    else:
        story.append(Paragraph("No recommendations", styles['Normal']))
    
    story.append(Spacer(1, 0.1*inch))
    
    # Final Stats
    final_stats = [
        ["Total Passes Applied", summary.get('total_passes_applied', 0)],
        ["Obfuscation Effectiveness", summary.get('obfuscation_effectiveness', 'N/A')]
    ]
    
    final_stats_table = Table(final_stats, colWidths=[2*inch, 2*inch])
    final_stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(final_stats_table)
    
    # Build PDF
    doc.build(story)
    return True

@app.post("/obfuscate")
async def obfuscate(
    uploaded_file: UploadFile = File(...),
    techniques: str = Form("[]")
):
    try:
        # Validate file type
        if not uploaded_file.filename.lower().endswith(('.c', '.cpp')):
            return JSONResponse({
                "error": "Only C/C++ files are supported",
                "success": False
            }, status_code=400)

        # Parse selected techniques
        try:
            selected_techniques = json.loads(techniques)
        except:
            selected_techniques = []

        # Generate unique filename to avoid conflicts
        file_extension = Path(uploaded_file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Save uploaded file to backend/uploads
        input_path = UPLOAD_DIR / unique_filename
        with open(input_path, "wb") as f:
            shutil.copyfileobj(uploaded_file.file, f)

        print(f"Processing: {uploaded_file.filename}")
        print(f"Selected techniques: {selected_techniques}")
        
        # Run obfuscation pipeline with selected techniques
        result = obfuscate_code(str(input_path), selected_techniques)

        # Clean up uploaded file
        input_path.unlink(missing_ok=True)

        # Return results
        return JSONResponse({
            "message": "Obfuscation successful!",
            "exe": result["exe"],
            "ll": result["llvm_ir"],
            "report": result["report"],
            "advanced_report": result.get("advanced_report"),
            "metrics": result.get("metrics", {}),
            "success": True
        })

    except Exception as e:
        print(f"Error: {e}")
        # Clean up on error
        if 'input_path' in locals():
            input_path.unlink(missing_ok=True)
            
        return JSONResponse({
            "error": str(e),
            "success": False
        }, status_code=500)

@app.get("/download")
async def download_file(path: str):
    try:
        decoded_path = unquote(path)
        file_path = Path(decoded_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {decoded_path}")
            
        filename = file_path.name
        
        # Set appropriate media types
        if filename.endswith('.exe'):
            media_type = 'application/vnd.microsoft.portable-executable'
        elif filename.endswith('.ll'):
            media_type = 'text/plain'
        elif filename.endswith('.json'):
            media_type = 'application/json'
        elif filename.endswith('.pdf'):
            media_type = 'application/pdf'
        else:
            media_type = 'application/octet-stream'
            
        return FileResponse(
            str(file_path), 
            filename=filename,
            media_type=media_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate-pdf")
async def generate_pdf():
    """Generate PDF report from the latest obfuscation report"""
    try:
        # Look for the latest report.json in the current directory
        report_path = Path("report.json")
        
        if not report_path.exists():
            # Try to find any JSON report file
            json_files = list(Path(".").glob("*.json"))
            if not json_files:
                raise HTTPException(
                    status_code=404, 
                    detail="No obfuscation report found. Please run obfuscation first."
                )
            report_path = json_files[0]
        
        # Generate PDF
        pdf_filename = "obfuscation_report.pdf"
        pdf_path = Path(pdf_filename)
        
        success = generate_pdf_report(str(report_path), str(pdf_path))
        
        if success and pdf_path.exists():
            return JSONResponse({
                "message": "PDF report generated successfully",
                "pdf_path": str(pdf_path),
                "success": True
            })
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate PDF report"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "LLVM Obfuscation API is running"}

@app.get("/")
async def root():
    return {"message": "LLVM Obfuscation API", "status": "running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)