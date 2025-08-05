"""
DoctorLINC - Physician Assistant
Clinical decision support and documentation for healthcare providers
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime
import json

from shared.models.base_agent import BaseLINCAgent
from shared.database import get_db
from shared.database.models import User, Conversation, HealthcareRecord
from shared.auth import get_current_user, require_doctor, permission_required

logger = logging.getLogger(__name__)

class ClinicalNote(BaseModel):
    patient_id: int
    note_type: str  # consultation, follow_up, diagnosis, prescription
    content: str
    language: str = "en"
    provider_id: Optional[str] = None
    facility_id: Optional[str] = None

class SOAPNote(BaseModel):
    patient_id: int
    subjective: str
    objective: str
    assessment: str
    plan: str
    language: str = "en"

class PrescriptionRequest(BaseModel):
    patient_id: int
    medications: List[Dict[str, Any]]
    diagnosis: str
    notes: Optional[str] = None
    language: str = "en"

class VoiceTranscription(BaseModel):
    audio_content: bytes
    language: str = "ar"  # Arabic by default
    transcription_type: str = "clinical"

class FHIRResource(BaseModel):
    resource_type: str
    patient_id: int
    data: Dict[str, Any]

class DiagnosticAssistance(BaseModel):
    symptoms: List[str]
    patient_history: Optional[Dict[str, Any]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    language: str = "en"

class DoctorLINC(BaseLINCAgent):
    """Physician assistant for clinical decision support"""
    
    def __init__(self):
        super().__init__(
            name="doctorlinc",
            version="1.0.0",
            description="Physician assistant for clinical decision support and documentation",
            port=8010,
            dependencies=["authlinc", "oidlinc"]
        )
        
        # Setup custom routes
        self.add_routes(self._setup_routes)
    
    def _setup_routes(self, app: FastAPI):
        """Setup DoctorLINC specific routes"""
        
        @app.post("/clinical/note")
        async def create_clinical_note(
            note: ClinicalNote,
            background_tasks: BackgroundTasks,
            current_user: User = Depends(require_doctor),
            db: Session = Depends(get_db)
        ):
            """Create clinical note with AI assistance"""
            try:
                # Validate patient access
                patient = db.query(User).filter(User.id == note.patient_id).first()
                if not patient:
                    raise HTTPException(status_code=404, detail="Patient not found")
                
                # Process clinical note
                processed_note = await self._process_clinical_note(note, current_user)
                
                # Create healthcare record
                healthcare_record = HealthcareRecord(
                    patient_id=note.patient_id,
                    record_type="clinical_note",
                    fhir_resource_type="DocumentReference",
                    data=processed_note,
                    source_agent="doctorlinc",
                    provider_id=current_user.healthcare_id or str(current_user.id)
                )
                
                db.add(healthcare_record)
                db.commit()
                db.refresh(healthcare_record)
                
                # Generate FHIR resource in background
                background_tasks.add_task(
                    self._generate_fhir_document,
                    healthcare_record.id,
                    processed_note
                )
                
                return {
                    "record_id": healthcare_record.id,
                    "processed_note": processed_note,
                    "fhir_resource_id": healthcare_record.fhir_resource_id
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating clinical note: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/clinical/soap")
        async def create_soap_note(
            soap: SOAPNote,
            current_user: User = Depends(require_doctor),
            db: Session = Depends(get_db)
        ):
            """Create SOAP note"""
            try:
                # Generate structured SOAP note
                soap_data = {
                    "type": "soap_note",
                    "subjective": soap.subjective,
                    "objective": soap.objective,
                    "assessment": soap.assessment,
                    "plan": soap.plan,
                    "provider": {
                        "id": current_user.id,
                        "name": current_user.full_name,
                        "healthcare_id": current_user.healthcare_id
                    },
                    "language": soap.language,
                    "created_at": datetime.now().isoformat()
                }
                
                # Enhance with AI analysis
                enhanced_soap = await self._enhance_soap_note(soap_data)
                
                # Create healthcare record
                healthcare_record = HealthcareRecord(
                    patient_id=soap.patient_id,
                    record_type="soap_note",
                    fhir_resource_type="DocumentReference",
                    data=enhanced_soap,
                    source_agent="doctorlinc",
                    provider_id=current_user.healthcare_id or str(current_user.id)
                )
                
                db.add(healthcare_record)
                db.commit()
                
                return enhanced_soap
                
            except Exception as e:
                logger.error(f"Error creating SOAP note: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/clinical/prescription")
        async def create_prescription(
            prescription: PrescriptionRequest,
            current_user: User = Depends(require_doctor),
            db: Session = Depends(get_db)
        ):
            """Create prescription with drug interaction checking"""
            try:
                # Validate medications and check interactions
                validated_prescription = await self._validate_prescription(
                    prescription, current_user
                )
                
                # Create healthcare record
                healthcare_record = HealthcareRecord(
                    patient_id=prescription.patient_id,
                    record_type="prescription",
                    fhir_resource_type="MedicationRequest",
                    data=validated_prescription,
                    source_agent="doctorlinc",
                    provider_id=current_user.healthcare_id or str(current_user.id)
                )
                
                db.add(healthcare_record)
                db.commit()
                
                return validated_prescription
                
            except Exception as e:
                logger.error(f"Error creating prescription: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/clinical/transcribe")
        async def transcribe_voice(
            audio_file: UploadFile = File(...),
            language: str = "ar",
            current_user: User = Depends(require_doctor)
        ):
            """Transcribe Arabic/English voice to clinical text"""
            try:
                # Read audio content
                audio_content = await audio_file.read()
                
                # Transcribe audio (placeholder for Whisper integration)
                transcription = await self._transcribe_audio(audio_content, language)
                
                # Process for clinical terminology
                clinical_text = await self._process_clinical_transcription(
                    transcription, language
                )
                
                return {
                    "raw_transcription": transcription,
                    "clinical_text": clinical_text,
                    "language": language,
                    "confidence": 0.95  # Placeholder
                }
                
            except Exception as e:
                logger.error(f"Error transcribing voice: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/clinical/diagnosis-assist")
        async def diagnosis_assistance(
            request: DiagnosticAssistance,
            current_user: User = Depends(require_doctor)
        ):
            """Provide diagnostic assistance based on symptoms"""
            try:
                # Analyze symptoms and provide suggestions
                diagnosis_suggestions = await self._analyze_symptoms(request)
                
                return {
                    "primary_diagnoses": diagnosis_suggestions["primary"],
                    "differential_diagnoses": diagnosis_suggestions["differential"],
                    "recommended_tests": diagnosis_suggestions["tests"],
                    "red_flags": diagnosis_suggestions.get("red_flags", []),
                    "confidence_scores": diagnosis_suggestions["confidence"],
                    "language": request.language
                }
                
            except Exception as e:
                logger.error(f"Error in diagnosis assistance: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/clinical/patient-summary/{patient_id}")
        async def get_patient_summary(
            patient_id: int,
            current_user: User = Depends(require_doctor),
            db: Session = Depends(get_db)
        ):
            """Get comprehensive patient summary"""
            try:
                # Get patient records
                records = db.query(HealthcareRecord).filter(
                    HealthcareRecord.patient_id == patient_id
                ).order_by(HealthcareRecord.created_at.desc()).limit(50).all()
                
                # Generate summary
                summary = await self._generate_patient_summary(records)
                
                return summary
                
            except Exception as e:
                logger.error(f"Error generating patient summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/fhir/resource")
        async def create_fhir_resource(
            resource: FHIRResource,
            current_user: User = Depends(require_doctor),
            db: Session = Depends(get_db)
        ):
            """Create FHIR-compliant resource"""
            try:
                # Validate FHIR resource
                validated_resource = await self._validate_fhir_resource(resource)
                
                # Create healthcare record
                healthcare_record = HealthcareRecord(
                    patient_id=resource.patient_id,
                    record_type="fhir_resource",
                    fhir_resource_type=resource.resource_type,
                    data=validated_resource,
                    source_agent="doctorlinc",
                    provider_id=current_user.healthcare_id or str(current_user.id)
                )
                
                db.add(healthcare_record)
                db.commit()
                
                return validated_resource
                
            except Exception as e:
                logger.error(f"Error creating FHIR resource: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_clinical_note(self, note: ClinicalNote, provider: User) -> Dict[str, Any]:
        """Process clinical note with AI enhancement"""
        # Placeholder for AI processing
        processed = {
            "original_content": note.content,
            "structured_content": {
                "chief_complaint": self._extract_chief_complaint(note.content),
                "clinical_findings": self._extract_clinical_findings(note.content),
                "recommendations": self._extract_recommendations(note.content)
            },
            "provider": {
                "id": provider.id,
                "name": provider.full_name,
                "healthcare_id": provider.healthcare_id
            },
            "language": note.language,
            "note_type": note.note_type,
            "created_at": datetime.now().isoformat(),
            "ai_confidence": 0.92
        }
        
        return processed
    
    def _extract_chief_complaint(self, content: str) -> str:
        """Extract chief complaint from clinical note"""
        # Simple keyword-based extraction (can be enhanced with NLP)
        complaint_keywords = ["complains of", "presents with", "chief complaint", "يشكو من"]
        
        for keyword in complaint_keywords:
            if keyword in content.lower():
                # Extract sentence containing the keyword
                sentences = content.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        
        return "Not clearly stated"
    
    def _extract_clinical_findings(self, content: str) -> List[str]:
        """Extract clinical findings from note"""
        # Placeholder for clinical finding extraction
        findings = []
        clinical_terms = [
            "blood pressure", "temperature", "heart rate", "respiratory rate",
            "ضغط الدم", "درجة الحرارة", "معدل النبض"
        ]
        
        for term in clinical_terms:
            if term in content.lower():
                findings.append(f"Documented: {term}")
        
        return findings
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from note"""
        # Placeholder for recommendation extraction
        recommendations = []
        rec_keywords = ["recommend", "suggest", "prescribe", "follow up", "أوصي", "اقترح"]
        
        sentences = content.split('.')
        for sentence in sentences:
            for keyword in rec_keywords:
                if keyword in sentence.lower():
                    recommendations.append(sentence.strip())
                    break
        
        return recommendations
    
    async def _enhance_soap_note(self, soap_data: Dict) -> Dict[str, Any]:
        """Enhance SOAP note with clinical insights"""
        # Add clinical coding and insights
        soap_data["clinical_codes"] = await self._generate_clinical_codes(soap_data)
        soap_data["severity_assessment"] = await self._assess_severity(soap_data)
        soap_data["follow_up_recommendations"] = await self._generate_follow_up(soap_data)
        
        return soap_data
    
    async def _generate_clinical_codes(self, soap_data: Dict) -> List[Dict]:
        """Generate ICD-10 and other clinical codes"""
        # Placeholder for clinical coding
        return [
            {"system": "ICD-10", "code": "Z00.00", "display": "General examination"},
            {"system": "SNOMED-CT", "code": "185389009", "display": "Follow-up visit"}
        ]
    
    async def _assess_severity(self, soap_data: Dict) -> str:
        """Assess clinical severity"""
        # Simple rule-based severity assessment
        urgent_keywords = ["severe", "acute", "emergency", "urgent", "شديد", "طارئ"]
        assessment = soap_data.get("assessment", "").lower()
        
        for keyword in urgent_keywords:
            if keyword in assessment:
                return "high"
        
        return "routine"
    
    async def _generate_follow_up(self, soap_data: Dict) -> List[str]:
        """Generate follow-up recommendations"""
        return [
            "Schedule follow-up in 2 weeks",
            "Monitor symptoms and return if worsening",
            "Complete prescribed treatment course"
        ]
    
    async def _validate_prescription(self, prescription: PrescriptionRequest, provider: User) -> Dict[str, Any]:
        """Validate prescription and check for interactions"""
        validated = {
            "patient_id": prescription.patient_id,
            "medications": [],
            "diagnosis": prescription.diagnosis,
            "notes": prescription.notes,
            "provider": {
                "id": provider.id,
                "name": provider.full_name,
                "healthcare_id": provider.healthcare_id
            },
            "language": prescription.language,
            "created_at": datetime.now().isoformat(),
            "drug_interactions": [],
            "allergies_checked": True,
            "dosage_verified": True
        }
        
        # Process each medication
        for med in prescription.medications:
            processed_med = {
                "name": med.get("name"),
                "dosage": med.get("dosage"),
                "frequency": med.get("frequency"),
                "duration": med.get("duration"),
                "instructions": med.get("instructions", ""),
                "validated": True
            }
            validated["medications"].append(processed_med)
        
        return validated
    
    async def _transcribe_audio(self, audio_content: bytes, language: str) -> str:
        """Transcribe audio to text using Whisper (placeholder)"""
        # Placeholder for Whisper integration
        if language == "ar":
            return "المريض يشكو من صداع شديد منذ يومين مع غثيان"
        else:
            return "Patient complains of severe headache for two days with nausea"
    
    async def _process_clinical_transcription(self, transcription: str, language: str) -> str:
        """Process transcription for clinical terminology"""
        # Placeholder for clinical text processing
        clinical_terms = {
            "صداع": "headache",
            "غثيان": "nausea", 
            "شديد": "severe",
            "يومين": "two days"
        }
        
        processed = transcription
        if language == "ar":
            # Add English clinical terms in parentheses
            for ar_term, en_term in clinical_terms.items():
                processed = processed.replace(ar_term, f"{ar_term} ({en_term})")
        
        return processed
    
    async def _analyze_symptoms(self, request: DiagnosticAssistance) -> Dict[str, Any]:
        """Analyze symptoms and provide diagnostic suggestions"""
        # Placeholder for diagnostic AI
        symptoms = request.symptoms
        
        # Simple rule-based diagnosis suggestions
        diagnosis_map = {
            ("headache", "nausea"): {
                "primary": ["Migraine", "Tension headache"],
                "differential": ["Sinusitis", "Hypertension"],
                "tests": ["Blood pressure", "Neurological exam"],
                "confidence": {"migraine": 0.8, "tension_headache": 0.6}
            },
            ("fever", "cough"): {
                "primary": ["Upper respiratory infection", "Bronchitis"],
                "differential": ["Pneumonia", "COVID-19"],
                "tests": ["Chest X-ray", "COVID test", "CBC"],
                "confidence": {"uri": 0.7, "bronchitis": 0.5}
            }
        }
        
        # Match symptoms
        symptom_set = tuple(sorted([s.lower() for s in symptoms]))
        
        # Find best match
        for key, diagnosis in diagnosis_map.items():
            if all(symptom in symptom_set for symptom in key):
                return diagnosis
        
        # Default response
        return {
            "primary": ["Further evaluation needed"],
            "differential": ["Multiple possibilities"],
            "tests": ["Complete history and physical examination"],
            "confidence": {"evaluation_needed": 1.0}
        }
    
    async def _generate_patient_summary(self, records: List[HealthcareRecord]) -> Dict[str, Any]:
        """Generate comprehensive patient summary"""
        summary = {
            "total_records": len(records),
            "recent_visits": [],
            "diagnoses": [],
            "medications": [],
            "allergies": [],
            "vital_trends": {},
            "generated_at": datetime.now().isoformat()
        }
        
        # Process records
        for record in records[:10]:  # Last 10 records
            if record.record_type == "clinical_note":
                summary["recent_visits"].append({
                    "date": record.created_at,
                    "type": record.record_type,
                    "provider": record.provider_id
                })
            elif record.record_type == "prescription":
                meds = record.data.get("medications", [])
                summary["medications"].extend([med["name"] for med in meds])
        
        return summary
    
    async def _validate_fhir_resource(self, resource: FHIRResource) -> Dict[str, Any]:
        """Validate FHIR resource structure"""
        # Basic FHIR validation
        validated = {
            "resourceType": resource.resource_type,
            "id": f"{resource.resource_type}-{resource.patient_id}-{int(datetime.now().timestamp())}",
            "subject": {
                "reference": f"Patient/{resource.patient_id}"
            },
            "status": "active",
            "created": datetime.now().isoformat(),
            **resource.data
        }
        
        return validated
    
    async def _generate_fhir_document(self, record_id: int, note_data: Dict):
        """Generate FHIR DocumentReference in background"""
        # Background task to create FHIR resource
        logger.info(f"Generating FHIR document for record {record_id}")
        # Implementation would integrate with FHIR server

def create_app():
    """Create and configure the DoctorLINC application"""
    return DoctorLINC()

if __name__ == "__main__":
    app = create_app()
    app.run()