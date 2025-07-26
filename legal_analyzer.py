import streamlit as st
import pandas as pd
import re
import json
import hashlib
from datetime import datetime, timedelta
from io import BytesIO
import base64
from typing import Dict, List, Tuple, Any
import PyPDF2
import docx
import mammoth
import warnings
import sqlite3
import uuid
import google.generativeai as genai
from langdetect import detect
import os
warnings.filterwarnings('ignore')

# Configure Streamlit page
st.set_page_config(
    page_title="AI Legal Document Analyzer with Gemini",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for user management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = ""
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'current_language' not in st.session_state:
    st.session_state.current_language = 'en'
if 'gemini_configured' not in st.session_state:
    st.session_state.gemini_configured = False

# Supported languages
LANGUAGES = {
    'en': 'English',
    'es': 'Spanish (Español)',
    'fr': 'French (Français)',
    'de': 'German (Deutsch)',
    'it': 'Italian (Italiano)',
    'pt': 'Portuguese (Português)',
    'ru': 'Russian (Русский)',
    'zh': 'Chinese (中文)',
    'ja': 'Japanese (日本語)',
    'ko': 'Korean (한국어)',
    'ar': 'Arabic (العربية)',
    'hi': 'Hindi (हिन्दी)',
    'nl': 'Dutch (Nederlands)',
    'sv': 'Swedish (Svenska)',
    'no': 'Norwegian (Norsk)',
    'da': 'Danish (Dansk)',
    'fi': 'Finnish (Suomi)',
    'pl': 'Polish (Polski)',
    'tr': 'Turkish (Türkçe)',
    'he': 'Hebrew (עברית)'
}

# Translation dictionary for UI elements
TRANSLATIONS = {
    'en': {
        'title': 'AI Legal Document Analyzer with Gemini',
        'login': 'Login',
        'register': 'Register',
        'username': 'Username',
        'password': 'Password',
        'email': 'Email',
        'full_name': 'Full Name',
        'organization': 'Organization',
        'welcome': 'Welcome',
        'logout': 'Logout',
        'document_upload': 'Document Upload',
        'choose_document': 'Choose a legal document',
        'analysis_options': 'Analysis Options',
        'language_selection': 'Language Selection',
        'export_options': 'Export Options',
        'account_details': 'Account Details',
        'analysis_history': 'Analysis History',
        'document_summary': 'Document Summary',
        'parties_entities': 'Parties & Entities',
        'key_clauses': 'Key Clauses',
        'risks_obligations': 'Risks & Obligations',
        'important_dates': 'Important Dates',
        'document_text': 'Document Text',
        'text_input': 'Text Input',
        'paste_text': 'Paste your legal document text here...',
        'analyze_text': 'Analyze Text',
        'processing': 'Processing document...',
        'analyzing': 'Analyzing document with Gemini AI...',
        'download_report': 'Download Report',
        'words': 'Words',
        'characters': 'Characters',
        'sentences': 'Sentences',
        'file_type': 'File Type',
        'gemini_setup': 'Gemini AI Setup',
        'api_key': 'Google API Key',
        'configure_gemini': 'Configure Gemini',
        'gemini_status': 'Gemini Status'
    },
    'es': {
        'title': 'Analizador de Documentos Legales con Gemini IA',
        'login': 'Iniciar Sesión',
        'register': 'Registrarse',
        'username': 'Nombre de Usuario',
        'password': 'Contraseña',
        'email': 'Correo Electrónico',
        'full_name': 'Nombre Completo',
        'organization': 'Organización',
        'welcome': 'Bienvenido',
        'logout': 'Cerrar Sesión',
        'document_upload': 'Subir Documento',
        'choose_document': 'Elegir un documento legal',
        'analysis_options': 'Opciones de Análisis',
        'language_selection': 'Selección de Idioma',
        'export_options': 'Opciones de Exportación',
        'account_details': 'Detalles de la Cuenta',
        'analysis_history': 'Historial de Análisis',
        'document_summary': 'Resumen del Documento',
        'parties_entities': 'Partes y Entidades',
        'key_clauses': 'Cláusulas Clave',
        'risks_obligations': 'Riesgos y Obligaciones',
        'important_dates': 'Fechas Importantes',
        'document_text': 'Texto del Documento',
        'text_input': 'Entrada de Texto',
        'paste_text': 'Pega aquí el texto de tu documento legal...',
        'analyze_text': 'Analizar Texto',
        'processing': 'Procesando documento...',
        'analyzing': 'Analizando documento con Gemini IA...',
        'download_report': 'Descargar Informe',
        'words': 'Palabras',
        'characters': 'Caracteres',
        'sentences': 'Oraciones',
        'file_type': 'Tipo de Archivo',
        'gemini_setup': 'Configuración de Gemini IA',
        'api_key': 'Clave API de Google',
        'configure_gemini': 'Configurar Gemini',
        'gemini_status': 'Estado de Gemini'
    },
    'fr': {
        'title': 'Analyseur de Documents Juridiques avec Gemini IA',
        'login': 'Se Connecter',
        'register': "S'inscrire",
        'username': "Nom d'utilisateur",
        'password': 'Mot de passe',
        'email': 'Email',
        'full_name': 'Nom complet',
        'organization': 'Organisation',
        'welcome': 'Bienvenue',
        'logout': 'Se déconnecter',
        'document_upload': 'Télécharger un document',
        'choose_document': 'Choisir un document juridique',
        'analysis_options': "Options d'analyse",
        'language_selection': 'Sélection de langue',
        'export_options': "Options d'exportation",
        'account_details': 'Détails du compte',
        'analysis_history': "Historique d'analyse",
        'document_summary': 'Résumé du document',
        'parties_entities': 'Parties et entités',
        'key_clauses': 'Clauses clés',
        'risks_obligations': 'Risques et obligations',
        'important_dates': 'Dates importantes',
        'document_text': 'Texte du document',
        'text_input': 'Saisie de texte',
        'paste_text': 'Collez ici le texte de votre document juridique...',
        'analyze_text': 'Analyser le texte',
        'processing': 'Traitement du document...',
        'analyzing': 'Analyse du document avec Gemini IA...',
        'download_report': 'Télécharger le rapport',
        'words': 'Mots',
        'characters': 'Caractères',
        'sentences': 'Phrases',
        'file_type': 'Type de fichier',
        'gemini_setup': 'Configuration Gemini IA',
        'api_key': 'Clé API Google',
        'configure_gemini': 'Configurer Gemini',
        'gemini_status': 'Statut Gemini'
    }
}

def t(key):
    """Translation function"""
    current_lang = st.session_state.current_language
    return TRANSLATIONS.get(current_lang, TRANSLATIONS['en']).get(key, key)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f4e79;
        padding-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c5aa0;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-left: 4px solid #2c5aa0;
        padding-left: 1rem;
    }
    .insight-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
        margin: 1rem 0;
    }
    .entity-highlight {
        background-color: #ffffcc;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
    }
    .clause-highlight {
        background-color: #e6f3ff;
        padding: 4px 8px;
        border-radius: 5px;
        border-left: 3px solid #4dabf7;
        margin: 5px 0;
    }
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    .user-info {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .history-item {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 0.5rem;
    }
    .gemini-status {
        background: linear-gradient(45deg, #4285f4, #34a853);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .gemini-error {
        background: linear-gradient(45deg, #ea4335, #fbbc04);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class GeminiIntegration:
    """Google Gemini AI integration for multilingual legal document analysis"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        self.is_configured = False
        
        if api_key:
            self.configure_gemini(api_key)
    
    def configure_gemini(self, api_key):
        """Configure Gemini AI with API key"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.api_key = api_key
            self.is_configured = True
            return True, "Gemini AI configured successfully!"
        except Exception as e:
            self.is_configured = False
            return False, f"Failed to configure Gemini: {str(e)}"
    
    def detect_language(self, text):
        """Detect language using Gemini AI"""
        if not self.is_configured:
            # Fallback to langdetect
            try:
                return detect(text[:1000])
            except:
                return 'en'
        
        try:
            prompt = f"""
            Detect the primary language of the following text and return only the ISO 639-1 language code (e.g., 'en' for English, 'es' for Spanish, 'fr' for French):
            
            Text: {text[:500]}
            
            Language code:
            """
            
            response = self.model.generate_content(prompt)
            detected_lang = response.text.strip().lower()
            
            # Validate the response
            if detected_lang in LANGUAGES:
                return detected_lang
            else:
                # Fallback to langdetect
                return detect(text[:1000])
        except Exception as e:
            st.warning(f"Gemini language detection failed: {str(e)}")
            try:
                return detect(text[:1000])
            except:
                return 'en'
    
    def translate_text(self, text, target_lang, source_lang=None):
        """Translate text using Gemini AI"""
        if not self.is_configured:
            return text  # Return original text if Gemini not configured
        
        try:
            source_lang_name = LANGUAGES.get(source_lang, 'auto-detect') if source_lang else 'auto-detect'
            target_lang_name = LANGUAGES.get(target_lang, 'English')
            
            prompt = f"""
            Translate the following legal document text from {source_lang_name} to {target_lang_name}. 
            Preserve legal terminology and maintain the formal tone. Ensure accuracy of legal concepts:
            
            Text to translate: {text}
            
            Translation:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            st.warning(f"Gemini translation failed: {str(e)}")
            return text
    
    def analyze_legal_document(self, text, target_lang='en'):
        """Comprehensive legal document analysis using Gemini AI"""
        if not self.is_configured:
            return self._fallback_analysis(text)
        
        try:
            prompt = f"""
            Analyze the following legal document and provide a comprehensive analysis in {LANGUAGES.get(target_lang, 'English')}. 
            
            Please provide:
            1. Document type and purpose
            2. Key parties involved (names, organizations)
            3. Important dates and deadlines
            4. Financial terms and amounts
            5. Key legal clauses (termination, confidentiality, indemnity, payment, dispute resolution)
            6. Potential risks and liabilities
            7. Key obligations for each party
            8. Jurisdiction and governing law
            9. Document summary
            
            Format the response as JSON with the following structure:
            {{
                "document_type": "string",
                "parties": ["list of parties"],
                "dates": ["list of important dates"],
                "financial_terms": ["list of amounts and terms"],
                "clauses": {{
                    "termination": ["termination clauses"],
                    "confidentiality": ["confidentiality clauses"],
                    "indemnity": ["indemnity clauses"],
                    "payment": ["payment clauses"],
                    "dispute_resolution": ["dispute resolution clauses"]
                }},
                "risks": ["list of potential risks"],
                "obligations": ["list of key obligations"],
                "jurisdiction": "string",
                "summary": "comprehensive summary"
            }}
            
            Legal Document Text:
            {text}
            
            Analysis (JSON format):
            """
            
            response = self.model.generate_content(prompt)
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response.text)
                return analysis
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured text analysis
                return {
                    "document_type": "Legal Document",
                    "parties": [],
                    "dates": [],
                    "financial_terms": [],
                    "clauses": {
                        "termination": [],
                        "confidentiality": [],
                        "indemnity": [],
                        "payment": [],
                        "dispute_resolution": []
                    },
                    "risks": [],
                    "obligations": [],
                    "jurisdiction": "Not specified",
                    "summary": response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                }
                
        except Exception as e:
            st.error(f"Gemini analysis failed: {str(e)}")
            return self._fallback_analysis(text)
    
    def _fallback_analysis(self, text):
        """Fallback analysis when Gemini is not available"""
        return {
            "document_type": "Legal Document",
            "parties": [],
            "dates": [],
            "financial_terms": [],
            "clauses": {
                "termination": [],
                "confidentiality": [],
                "indemnity": [],
                "payment": [],
                "dispute_resolution": []
            },
            "risks": [],
            "obligations": [],
            "jurisdiction": "Analysis requires Gemini AI configuration",
            "summary": "Please configure Gemini AI for detailed analysis."
        }
    
    def extract_entities_advanced(self, text, target_lang='en'):
        """Advanced entity extraction using Gemini AI"""
        if not self.is_configured:
            return {"PERSONS": [], "ORGANIZATIONS": [], "DATES": [], "MONEY": [], "LOCATIONS": []}
        
        try:
            prompt = f"""
            Extract the following entities from the legal document text. Respond in {LANGUAGES.get(target_lang, 'English')}:
            
            1. PERSONS: Names of individuals
            2. ORGANIZATIONS: Company names, institutions
            3. DATES: All dates mentioned
            4. MONEY: Financial amounts, currencies
            5. LOCATIONS: Places, addresses, jurisdictions
            
            Format as JSON:
            {{
                "PERSONS": ["list of person names"],
                "ORGANIZATIONS": ["list of organizations"],
                "DATES": ["list of dates"],
                "MONEY": ["list of monetary amounts"],
                "LOCATIONS": ["list of locations"]
            }}
            
            Text: {text}
            
            Entities (JSON):
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                entities = json.loads(response.text)
                return entities
            except json.JSONDecodeError:
                return {"PERSONS": [], "ORGANIZATIONS": [], "DATES": [], "MONEY": [], "LOCATIONS": []}
                
        except Exception as e:
            st.warning(f"Gemini entity extraction failed: {str(e)}")
            return {"PERSONS": [], "ORGANIZATIONS": [], "DATES": [], "MONEY": [], "LOCATIONS": []}

class UserManager:
    """User management system with database integration"""
    
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for user management"""
        conn = sqlite3.connect('legal_analyzer_gemini.db')
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                full_name TEXT,
                organization TEXT,
                created_date TEXT,
                last_login TEXT,
                gemini_api_key TEXT
            )
        ''')
        
        # Analysis history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                document_name TEXT,
                analysis_date TEXT,
                document_type TEXT,
                word_count INTEGER,
                original_language TEXT,
                target_language TEXT,
                summary TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, email="", full_name="", organization=""):
        """Register a new user"""
        conn = sqlite3.connect('legal_analyzer_gemini.db')
        cursor = conn.cursor()
        
        try:
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            created_date = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO users (id, username, password_hash, email, full_name, organization, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, password_hash, email, full_name, organization, created_date))
            
            conn.commit()
            conn.close()
            return True, "User registered successfully!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Username already exists!"
        except Exception as e:
            conn.close()
            return False, f"Registration failed: {str(e)}"
    
    def login_user(self, username, password):
        """Authenticate user login"""
        conn = sqlite3.connect('legal_analyzer_gemini.db')
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, username, email, full_name, organization, gemini_api_key 
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute('''
                UPDATE users 
                SET last_login = ? 
                WHERE id = ?
            ''', (datetime.now().isoformat(), user[0]))
            conn.commit()
            conn.close()
            return True, user
        else:
            conn.close()
            return False, None
    
    def update_gemini_key(self, user_id, api_key):
        """Update user's Gemini API key"""
        conn = sqlite3.connect('legal_analyzer_gemini.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET gemini_api_key = ? 
            WHERE id = ?
        ''', (api_key, user_id))
        
        conn.commit()
        conn.close()
    
    def get_gemini_key(self, user_id):
        """Get user's Gemini API key"""
        conn = sqlite3.connect('legal_analyzer_gemini.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT gemini_api_key FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else None
    
    def save_analysis(self, user_id, document_name, document_type, word_count, original_lang, target_lang, summary):
        """Save analysis to history"""
        conn = sqlite3.connect('legal_analyzer_gemini.db')
        cursor = conn.cursor()
        
        analysis_id = str(uuid.uuid4())
        analysis_date = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO analysis_history (id, user_id, document_name, analysis_date, document_type, 
                                        word_count, original_language, target_language, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (analysis_id, user_id, document_name, analysis_date, document_type, 
              word_count, original_lang, target_lang, summary))
        
        conn.commit()
        conn.close()
    
    def get_user_history(self, user_id):
        """Get user's analysis history"""
        conn = sqlite3.connect('legal_analyzer_gemini.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT document_name, analysis_date, document_type, word_count, 
                   original_language, target_language, summary
            FROM analysis_history 
            WHERE user_id = ? 
            ORDER BY analysis_date DESC
            LIMIT 20
        ''', (user_id,))
        
        history = cursor.fetchall()
        conn.close()
        return history

class LegalDocumentAnalyzer:
    """Enhanced legal document analyzer with Gemini AI integration"""
    
    def __init__(self, gemini_integration=None):
        self.gemini = gemini_integration
        
        # Fallback patterns for basic analysis when Gemini is not available
        self.legal_patterns = {
            'termination_clauses': [
                r'terminat[ei](?:on|ng)', r'end(?:ing)?\s+(?:of\s+)?(?:this\s+)?(?:agreement|contract)',
                r'expir[ey](?:ation)?', r'breach\s+of\s+contract'
            ],
            'confidentiality_clauses': [
                r'confidential(?:ity)?', r'non-disclos(?:ure|e)', r'proprietary\s+information'
            ],
            'indemnity_clauses': [
                r'indemnif(?:y|ication)', r'hold\s+harmless', r'liability\s+(?:for\s+)?damages'
            ],
            'payment_clauses': [
                r'payment\s+terms?', r'invoice', r'compensation', r'fee(?:s)?'
            ],
            'dispute_resolution': [
                r'arbitration', r'mediation', r'dispute\s+resolution', r'governing\s+law'
            ]
        }
    
    def extract_text_from_pdf(self, file) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading DOCX: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, file) -> str:
        """Extract text from TXT file"""
        try:
            return str(file.read(), "utf-8")
        except Exception as e:
            st.error(f"Error reading TXT: {str(e)}")
            return ""
    
    def analyze_document(self, text, target_lang='en'):
        """Main document analysis function"""
        if self.gemini and self.gemini.is_configured:
            return self.gemini.analyze_legal_document(text, target_lang)
        else:
            return self._basic_analysis(text)
    
    def _basic_analysis(self, text):
        """Basic analysis when Gemini is not available"""
        # Basic entity extraction
        entities = self._extract_basic_entities(text)
        
        # Basic clause extraction
        clauses = {}
        for clause_type, patterns in self.legal_patterns.items():
            clauses[clause_type] = []
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    context = re.sub(r'\s+', ' ', context)
                    if context not in clauses[clause_type]:
                        clauses[clause_type].append(context)
        
        return {
            "document_type": "Legal Document",
            "parties": entities.get('PERSONS', []) + entities.get('ORGANIZATIONS', []),
            "dates": entities.get('DATES', []),
            "financial_terms": entities.get('MONEY', []),
            "clauses": clauses,
            "risks": ["Basic analysis - configure Gemini for detailed risk assessment"],
            "obligations": ["Basic analysis - configure Gemini for detailed obligation analysis"],
            "jurisdiction": "Not detected",
            "summary": f"Document contains {len(text.split())} words. Basic analysis performed."
        }
    
    def _extract_basic_entities(self, text):
        """Basic entity extraction fallback"""
        entities = {
            'PERSONS': [],
            'ORGANIZATIONS': [],
            'DATES': [],
            'MONEY': [],
            'LOCATIONS': []
        }
        
        # Basic patterns
        person_patterns = [r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b']
        org_patterns = [r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:Inc\.|LLC|Corp\.|Company|Corporation|Ltd\.)\b']
        date_patterns = [r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b']
        money_patterns = [r'\$[\d,]+(?:\.\d{2})?', r'€[\d,]+(?:\.\d{2})?', r'£[\d,]+(?:\.\d{2})?']
        
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            entities['PERSONS'].extend([m.strip() for m in matches if len(m.strip()) > 3])
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities['ORGANIZATIONS'].extend([m.strip() for m in matches])
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            entities['DATES'].extend(matches)
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text)
            entities['MONEY'].extend(matches)
        
        # Clean and deduplicate
        for key in entities:
            entities[key] = list(set([item for item in entities[key] if item.strip()]))
        
        return entities

def gemini_setup_page():
    """Gemini AI configuration page"""
    st.markdown(f'<h2 class="section-header">🤖 {t("gemini_setup")}</h2>', unsafe_allow_html=True)
    
    user_manager = UserManager()
    current_key = user_manager.get_gemini_key(st.session_state.user_id)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Configure Google Gemini AI
        
        To enable advanced multilingual analysis, please provide your Google API key:
        
        1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Create a new API key
        3. Copy and paste it below
        4. Click "Configure Gemini" to activate
        
        **Features enabled with Gemini:**
        - Advanced multilingual translation
        - Intelligent legal clause detection
        - Comprehensive risk analysis
        - Entity extraction with context
        - Document summarization
        """)
        
        api_key_input = st.text_input(
            f"{t('api_key')}:",
            value=current_key if current_key else "",
            type="password",
            help="Your Google API key for Gemini AI"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button(f"🔧 {t('configure_gemini')}", use_container_width=True):
                if api_key_input.strip():
                    gemini_integration = GeminiIntegration()
                    success, message = gemini_integration.configure_gemini(api_key_input.strip())
                    
                    if success:
                        user_manager.update_gemini_key(st.session_state.user_id, api_key_input.strip())
                        st.session_state.gemini_configured = True
                        st.session_state.gemini_integration = gemini_integration
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter a valid API key!")
        
        with col_btn2:
            if st.button("🧪 Test Configuration", use_container_width=True):
                if api_key_input.strip():
                    gemini_integration = GeminiIntegration()
                    success, message = gemini_integration.configure_gemini(api_key_input.strip())
                    
                    if success:
                        test_text = "This is a test contract between Company A and Company B dated January 1, 2024."
                        detected_lang = gemini_integration.detect_language(test_text)
                        st.success(f"✅ Gemini working! Detected language: {LANGUAGES.get(detected_lang, detected_lang)}")
                    else:
                        st.error(f"❌ Test failed: {message}")
                else:
                    st.error("Please enter an API key first!")
    
    with col2:
        # Status display
        if current_key:
            st.markdown('<div class="gemini-status">🟢 Gemini Configured</div>', unsafe_allow_html=True)
            
            # Initialize Gemini if key exists
            if 'gemini_integration' not in st.session_state:
                gemini_integration = GeminiIntegration(current_key)
                if gemini_integration.is_configured:
                    st.session_state.gemini_integration = gemini_integration
                    st.session_state.gemini_configured = True
        else:
            st.markdown('<div class="gemini-error">🔴 Gemini Not Configured</div>', unsafe_allow_html=True)
        
        st.markdown("### 📊 API Usage Tips")
        st.info("""
        **Free Tier Limits:**
        - 15 requests per minute
        - 1,500 requests per day
        - 1 million tokens per minute
        
        **Best Practices:**
        - Keep documents under 100KB
        - Use specific language codes
        - Monitor your usage
        """)

def login_page():
    """Display login/register page"""
    st.markdown(f'<h1 class="main-header">⚖️ {t("title")}</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs([t("login"), t("register")])
        
        user_manager = UserManager()
        
        with tab1:
            st.markdown(f"### {t('login')}")
            username = st.text_input(t("username"), key="login_username")
            password = st.text_input(t("password"), type="password", key="login_password")
            
            if st.button(t("login"), use_container_width=True):
                if username and password:
                    success, user_data = user_manager.login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = user_data[1]
                        st.session_state.user_id = user_data[0]
                        st.session_state.user_email = user_data[2] or ""
                        st.session_state.user_full_name = user_data[3] or ""
                        st.session_state.user_organization = user_data[4] or ""
                        
                        # Initialize Gemini if API key exists
                        gemini_key = user_data[5]
                        if gemini_key:
                            gemini_integration = GeminiIntegration(gemini_key)
                            if gemini_integration.is_configured:
                                st.session_state.gemini_integration = gemini_integration
                                st.session_state.gemini_configured = True
                        
                        st.success(f"{t('welcome')}, {username}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password!")
                else:
                    st.error("Please fill in all fields!")
        
        with tab2:
            st.markdown(f"### {t('register')}")
            reg_username = st.text_input(t("username"), key="reg_username")
            reg_password = st.text_input(t("password"), type="password", key="reg_password")
            reg_email = st.text_input(t("email"), key="reg_email")
            reg_full_name = st.text_input(t("full_name"), key="reg_full_name")
            reg_organization = st.text_input(t("organization"), key="reg_organization")
            
            if st.button(t("register"), use_container_width=True):
                if reg_username and reg_password:
                    success, message = user_manager.register_user(
                        reg_username, reg_password, reg_email, reg_full_name, reg_organization
                    )
                    if success:
                        st.success(message)
                        st.info("Please login with your new account!")
                    else:
                        st.error(message)
                else:
                    st.error("Username and password are required!")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    """Main application interface"""
    # Initialize components
    user_manager = UserManager()
    
    # Get Gemini integration from session state
    gemini_integration = st.session_state.get('gemini_integration', None)
    analyzer = LegalDocumentAnalyzer(gemini_integration)
    
    # Header with user info and language selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f'<h1 class="main-header">⚖️ {t("title")}</h1>', unsafe_allow_html=True)
    
    with col2:
        # Language selection
        selected_lang = st.selectbox(
            "🌐 Language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=list(LANGUAGES.keys()).index(st.session_state.current_language)
        )
        if selected_lang != st.session_state.current_language:
            st.session_state.current_language = selected_lang
            st.rerun()
    
    with col3:
        # User info and logout
        gemini_status = "🟢 Active" if st.session_state.get('gemini_configured', False) else "🔴 Not Configured"
        st.markdown(f'''
        <div class="user-info">
            <strong>{t("welcome")}, {st.session_state.username}!</strong><br>
            <small>{st.session_state.user_organization}</small><br>
            <small>Gemini: {gemini_status}</small>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button(t("logout")):
            for key in ['logged_in', 'username', 'user_id', 'user_email', 'user_full_name', 
                       'user_organization', 'gemini_integration', 'gemini_configured']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Navigation tabs
    main_tab1, main_tab2, main_tab3 = st.tabs(["📄 Document Analysis", "🤖 Gemini Setup", "📊 Dashboard"])
    
    with main_tab1:
        # Sidebar for file upload and options
        with st.sidebar:
            st.markdown(f"### 📁 {t('document_upload')}")
            
            # Input method selection
            input_method = st.radio(
                "Choose input method:",
                ["File Upload", "Text Input"]
            )
            
            uploaded_file = None
            text_input = ""
            
            if input_method == "File Upload":
                uploaded_file = st.file_uploader(
                    t("choose_document"),
                    type=['pdf', 'docx', 'txt'],
                    help="Upload PDF, DOCX, or TXT files"
                )
            else:
                text_input = st.text_area(
                    t("paste_text"),
                    height=200,
                    placeholder=t("paste_text")
                )
                
                if st.button(t("analyze_text")) and text_input.strip():
                    uploaded_file = "text_input"
            
            st.markdown(f"### ⚙️ {t('analysis_options')}")
            show_full_text = st.checkbox("Show Full Document Text", value=False)
            highlight_entities = st.checkbox("Highlight Entities in Text", value=True)
            use_gemini_translation = st.checkbox("Use Gemini Translation", 
                                                value=st.session_state.get('gemini_configured', False),
                                                disabled=not st.session_state.get('gemini_configured', False))
            
            st.markdown(f"### 🌐 {t('language_selection')}")
            detected_lang_placeholder = st.empty()
            target_translate_lang = st.selectbox(
                "Translate results to:",
                options=list(LANGUAGES.keys()),
                format_func=lambda x: LANGUAGES[x],
                index=0
            )
            
            st.markdown(f"### 📊 {t('export_options')}")
            export_format = st.selectbox("Export Format", ["JSON", "CSV", "TXT"])
            
            # Account details section
            st.markdown(f"### 👤 {t('account_details')}")
            with st.expander("View Account Info"):
                st.write(f"**Username:** {st.session_state.username}")
                st.write(f"**Email:** {st.session_state.get('user_email', 'N/A')}")
                st.write(f"**Full Name:** {st.session_state.get('user_full_name', 'N/A')}")
                st.write(f"**Organization:** {st.session_state.get('user_organization', 'N/A')}")
                st.write(f"**Gemini Status:** {'✅ Configured' if st.session_state.get('gemini_configured') else '❌ Not Configured'}")
        
        # Main content area
        if uploaded_file is not None or (input_method == "Text Input" and text_input.strip()):
            # Extract text based on input method
            if input_method == "Text Input":
                text = text_input.strip()
                file_name = f"Text_Input_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                file_extension = "txt"
            else:
                file_extension = uploaded_file.name.split('.')[-1].lower()
                file_name = uploaded_file.name
                
                with st.spinner(t("processing")):
                    if file_extension == 'pdf':
                        text = analyzer.extract_text_from_pdf(uploaded_file)
                    elif file_extension == 'docx':
                        text = analyzer.extract_text_from_docx(uploaded_file)
                    elif file_extension == 'txt':
                        text = analyzer.extract_text_from_txt(uploaded_file)
                    else:
                        st.error("Unsupported file format")
                        return
            
            if not text.strip():
                st.error("Could not extract text from the document. Please check if the file is valid.")
                return
            
            # Detect language
            if gemini_integration and gemini_integration.is_configured:
                original_lang = gemini_integration.detect_language(text)
            else:
                try:
                    original_lang = detect(text[:1000])
                except:
                    original_lang = 'en'
            
            detected_lang_placeholder.info(f"🌐 Detected language: {LANGUAGES.get(original_lang, 'Unknown')} ({original_lang})")
            
            # Display document info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<div class="metric-container"><h3>{len(text.split())}</h3><p>{t("words")}</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-container"><h3>{len(text)}</h3><p>{t("characters")}</p></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-container"><h3>{len(text.split("."))}</h3><p>{t("sentences")}</p></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="metric-container"><h3>{file_extension.upper()}</h3><p>{t("file_type")}</p></div>', unsafe_allow_html=True)
            
            # Perform analysis
            with st.spinner(t("analyzing")):
                analysis_result = analyzer.analyze_document(text, target_translate_lang)
                
                # Get entities using Gemini if available
                if gemini_integration and gemini_integration.is_configured:
                    entities = gemini_integration.extract_entities_advanced(text, target_translate_lang)
                else:
                    entities = analyzer._extract_basic_entities(text)
                
                # Translate text if needed and Gemini is available
                translated_text = text
                if use_gemini_translation and gemini_integration and gemini_integration.is_configured and target_translate_lang != original_lang:
                    with st.spinner(f"Translating to {LANGUAGES[target_translate_lang]}..."):
                        translated_text = gemini_integration.translate_text(text, target_translate_lang, original_lang)
            
            # Save analysis to history
            user_manager.save_analysis(
                st.session_state.user_id,
                file_name,
                analysis_result.get('document_type', 'Legal Document'),
                len(text.split()),
                original_lang,
                target_translate_lang,
                analysis_result.get('summary', 'Analysis completed')
            )
            
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                f"📋 {t('document_summary')}", 
                f"👥 {t('parties_entities')}", 
                f"📜 {t('key_clauses')}", 
                f"⚠️ {t('risks_obligations')}", 
                f"📅 {t('important_dates')}", 
                f"📄 {t('document_text')}"
            ])
            
            with tab1:
                st.markdown(f'<div class="section-header">{t("document_summary")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="insight-box">{analysis_result.get("summary", "No summary available")}</div>', unsafe_allow_html=True)
                
                # Quick insights
                st.markdown('<div class="section-header">Quick Insights</div>', unsafe_allow_html=True)
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                
                with insight_col1:
                    st.metric("Document Type", analysis_result.get('document_type', 'Unknown'))
                    st.metric("Entities Found", sum(len(v) for v in entities.values()))
                
                with insight_col2:
                    st.metric("Key Parties", len(analysis_result.get('parties', [])))
                    st.metric("Important Dates", len(analysis_result.get('dates', [])))
                
                with insight_col3:
                    st.metric("Risk Indicators", len(analysis_result.get('risks', [])))
                    st.metric("Obligations Found", len(analysis_result.get('obligations', [])))
                
                # Language and AI info
                st.markdown("### 🤖 Analysis Information")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.info(f"**Original:** {LANGUAGES.get(original_lang, 'Unknown')}")
                with col2:
                    st.info(f"**Target:** {LANGUAGES.get(target_translate_lang, 'English')}")
                with col3:
                    ai_status = "Gemini AI" if st.session_state.get('gemini_configured') else "Basic Analysis"
                    st.info(f"**AI Engine:** {ai_status}")
                with col4:
                    st.info(f"**Jurisdiction:** {analysis_result.get('jurisdiction', 'Not specified')}")
            
            with tab2:
                st.markdown(f'<div class="section-header">{t("parties_entities")}</div>', unsafe_allow_html=True)
                
                # Display parties from Gemini analysis
                if analysis_result.get('parties'):
                    st.markdown("**Key Parties (Gemini Analysis):**")
                    for i, party in enumerate(analysis_result['parties'][:10], 1):
                        st.markdown(f"{i}. {party}")
                    st.markdown("---")
                
                # Display detailed entities
                for entity_type, entity_list in entities.items():
                    if entity_list:
                        st.markdown(f"**{entity_type.replace('_', ' ').title()}:**")
                        for entity in entity_list[:15]:
                            st.markdown(f"• {entity}")
                        st.markdown("---")
            
            with tab3:
                st.markdown(f'<div class="section-header">{t("key_clauses")}</div>', unsafe_allow_html=True)
                
                clauses = analysis_result.get('clauses', {})
                for clause_type, clause_list in clauses.items():
                    if clause_list:
                        st.markdown(f"**{clause_type.replace('_', ' ').title()} Clauses:**")
                        for i, clause in enumerate(clause_list[:5], 1):
                            st.markdown(f'<div class="clause-highlight">{i}. {clause}</div>', unsafe_allow_html=True)
                        st.markdown("---")
            
            with tab4:
                st.markdown(f'<div class="section-header">{t("risks_obligations")}</div>', unsafe_allow_html=True)
                
                risk_col1, risk_col2 = st.columns(2)
                
                with risk_col1:
                    st.markdown("**⚠️ Potential Risks:**")
                    risks = analysis_result.get('risks', [])
                    if risks:
                        for i, risk in enumerate(risks[:10], 1):
                            st.markdown(f"{i}. {risk}")
                    else:
                        st.info("No specific risks identified.")
                
                with risk_col2:
                    st.markdown("**📋 Key Obligations:**")
                    obligations = analysis_result.get('obligations', [])
                    if obligations:
                        for i, obligation in enumerate(obligations[:10], 1):
                            st.markdown(f"{i}. {obligation}")
                    else:
                        st.info("No specific obligations identified.")
            
            with tab5:
                st.markdown(f'<div class="section-header">{t("important_dates")}</div>', unsafe_allow_html=True)
                
                dates = analysis_result.get('dates', []) or entities.get('DATES', [])
                
                if dates:
                    dates_df = pd.DataFrame({'Dates Found': dates})
                    st.dataframe(dates_df, use_container_width=True)
                    
                    # Date analysis
                    st.markdown("### 📊 Date Analysis")
                    current_date = datetime.now()
                    future_dates = []
                    past_dates = []
                    
                    for date_str in dates:
                        try:
                            # Simple date parsing (can be enhanced)
                            if '/' in date_str:
                                parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                            elif '-' in date_str:
                                parsed_date = datetime.strptime(date_str, '%m-%d-%Y')
                            else:
                                continue
                            
                            if parsed_date > current_date:
                                future_dates.append((date_str, parsed_date))
                            else:
                                past_dates.append((date_str, parsed_date))
                        except:
                            continue
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("📅 Future Dates", len(future_dates))
                        if future_dates:
                            st.write("**Upcoming Deadlines:**")
                            for date_str, date_obj in sorted(future_dates, key=lambda x: x[1])[:5]:
                                days_until = (date_obj - current_date).days
                                st.write(f"• {date_str} ({days_until} days)")
                    
                    with col2:
                        st.metric("📆 Past Dates", len(past_dates))
                        if past_dates:
                            st.write("**Historical Dates:**")
                            for date_str, date_obj in sorted(past_dates, key=lambda x: x[1], reverse=True)[:5]:
                                days_ago = (current_date - date_obj).days
                                st.write(f"• {date_str} ({days_ago} days ago)")
                else:
                    st.info("No specific dates were identified in the document.")
            
            with tab6:
                st.markdown(f'<div class="section-header">{t("document_text")}</div>', unsafe_allow_html=True)
                
                # Language options for text display
                text_col1, text_col2 = st.columns(2)
                with text_col1:
                    display_original = st.checkbox("Show Original Text", value=True)
                with text_col2:
                    display_translated = st.checkbox("Show Translated Text", 
                                                   value=False,
                                                   disabled=not (use_gemini_translation and original_lang != target_translate_lang))
                
                if show_full_text:
                    if display_original:
                        st.markdown("### 📄 Original Text")
                        if highlight_entities:
                            # Highlight entities in text
                            highlighted_text = text
                            for entity_type, entity_list in entities.items():
                                for entity in entity_list:
                                    if entity and len(entity) > 2:
                                        pattern = re.escape(entity)
                                        highlighted_text = re.sub(
                                            f'({pattern})', 
                                            r'<mark class="entity-highlight">\1</mark>', 
                                            highlighted_text, 
                                            flags=re.IGNORECASE
                                        )
                            st.markdown(highlighted_text, unsafe_allow_html=True)
                        else:
                            st.text_area("Original Document Text", text, height=400)
                    
                    if display_translated and translated_text != text:
                        st.markdown(f"### 🌐 Text in {LANGUAGES[target_translate_lang]}")
                        st.text_area("Translated Document Text", translated_text, height=400)
                        
                else:
                    st.info("Enable 'Show Full Document Text' in the sidebar to view the complete document.")
            
            # Export functionality
            st.markdown(f'<div class="section-header">📤 {t("export_options")}</div>', unsafe_allow_html=True)
            
            export_data = {
                'document_info': {
                    'name': file_name,
                    'original_language': original_lang,
                    'target_language': target_translate_lang,
                    'word_count': len(text.split()),
                    'character_count': len(text),
                    'analysis_date': datetime.now().isoformat(),
                    'ai_engine': 'Gemini AI' if st.session_state.get('gemini_configured') else 'Basic Analysis'
                },
                'analysis_result': analysis_result,
                'entities': entities,
                'user_info': {
                    'username': st.session_state.username,
                    'organization': st.session_state.get('user_organization', '')
                }
            }
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📄 {t('download_report')}"):
                    ai_engine = 'Gemini AI' if st.session_state.get('gemini_configured') else 'Basic Analysis'
                    report = f"""
LEGAL DOCUMENT ANALYSIS REPORT (Enhanced with {ai_engine})
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analyzed by: {st.session_state.username}
Organization: {st.session_state.get('user_organization', 'N/A')}
Document: {file_name}
Original Language: {LANGUAGES.get(original_lang, 'Unknown')}
Target Language: {LANGUAGES.get(target_translate_lang, 'English')}
AI Engine: {ai_engine}

DOCUMENT SUMMARY:
{analysis_result.get('summary', 'No summary available')}

DOCUMENT TYPE: {analysis_result.get('document_type', 'Unknown')}
JURISDICTION: {analysis_result.get('jurisdiction', 'Not specified')}

KEY PARTIES:
{chr(10).join([f"• {party}" for party in analysis_result.get('parties', [])])}

ENTITIES FOUND:
{chr(10).join([f"{k}: {', '.join(v[:10])}" for k, v in entities.items() if v])}

IMPORTANT DATES:
{chr(10).join([f"• {date}" for date in analysis_result.get('dates', [])])}

FINANCIAL TERMS:
{chr(10).join([f"• {term}" for term in analysis_result.get('financial_terms', [])])}

KEY CLAUSES:
{chr(10).join([f"{k.replace('_', ' ').title()}: {len(v)} found" for k, v in analysis_result.get('clauses', {}).items() if v])}

RISK ANALYSIS:
{chr(10).join([f"• {risk}" for risk in analysis_result.get('risks', [])])}

KEY OBLIGATIONS:
{chr(10).join([f"• {obligation}" for obligation in analysis_result.get('obligations', [])])}
                    """
                    st.download_button(
                        label=f"📄 {t('download_report')}",
                        data=report,
                        file_name=f"gemini_legal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            
            with col2:
                if st.button("📊 Download JSON Data"):
                    json_data = json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
                    st.download_button(
                        label="📊 Download JSON",
                        data=json_data,
                        file_name=f"gemini_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col3:
                if st.button("📈 Download CSV Summary"):
                    csv_data = []
                    csv_data.append(['Category', 'Count', 'Details'])
                    csv_data.append(['Document', 1, file_name])
                    csv_data.append(['Words', len(text.split()), ''])
                    csv_data.append(['Characters', len(text), ''])
                    csv_data.append(['Original Language', 1, LANGUAGES.get(original_lang, 'Unknown')])
                    csv_data.append(['AI Engine', 1, 'Gemini AI' if st.session_state.get('gemini_configured') else 'Basic'])
                    csv_data.append(['Document Type', 1, analysis_result.get('document_type', 'Unknown')])
                    csv_data.append(['Key Parties', len(analysis_result.get('parties', [])), ''])
                    csv_data.append(['Total Entities', sum(len(v) for v in entities.values()), ''])
                    csv_data.append(['Risk Indicators', len(analysis_result.get('risks', [])), ''])
                    csv_data.append(['Obligations', len(analysis_result.get('obligations', [])), ''])
                    
                    df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
                    csv_string = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📈 Download CSV",
                        data=csv_string,
                        file_name=f"gemini_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        else:
            st.info("👆 Please upload a legal document or paste text to begin analysis.")
            
            # Show example of what the tool can do
            st.markdown('<div class="section-header">🔍 Enhanced AI Legal Analysis Features</div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                **📋 Document Types:**
                - Employment Agreements
                - Service Contracts
                - Lease Agreements
                - Purchase Agreements
                - NDAs & Confidentiality
                - Terms of Service
                - Privacy Policies
                - License Agreements
                - Partnership Agreements
                - Merger & Acquisition
                """)
            
            with col2:
                st.markdown("""
                **🤖 Gemini AI Features:**
                - Advanced Language Detection
                - Context-Aware Translation
                - Intelligent Clause Analysis
                - Risk Assessment
                - Legal Entity Recognition
                - Contract Summarization
                - Obligation Mapping
                - Compliance Checking
                """)
            
            with col3:
                st.markdown("""
                **🌐 20+ Languages:**
                - English, Spanish, French
                - German, Italian, Portuguese
                - Russian, Chinese, Japanese
                - Korean, Arabic, Hindi
                - Dutch, Swedish, Norwegian
                - Danish, Finnish, Polish
                - Turkish, Hebrew
                - And more...
                """)
            
            with col4:
                st.markdown("""
                **📊 Analysis Features:**
                - Real-time Processing
                - Multi-format Support
                - Export Capabilities
                - Analysis History
                - User Profiles
                - Secure Data Storage
                - Progress Tracking
                - Custom Reports
                """)
            
            # Sample documents section with Gemini
            st.markdown('<div class="section-header">📚 Try Sample Documents (Gemini Enhanced)</div>', unsafe_allow_html=True)
            
            sample_texts = {
                "Employment Agreement (English)": """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into on January 15, 2024, between TechCorp Inc., a Delaware corporation ("Company"), and John Smith ("Employee").

1. POSITION AND DUTIES
Employee shall serve as Senior Software Developer and shall perform duties as assigned by the Company.

2. COMPENSATION
Employee shall receive an annual salary of $120,000, payable bi-weekly.

3. TERMINATION
Either party may terminate this agreement with 30 days written notice.

4. CONFIDENTIALITY
Employee agrees to maintain confidentiality of all proprietary information.

5. BENEFITS
Employee shall be entitled to health insurance, dental coverage, and 15 days of paid vacation annually.

6. NON-COMPETE
Employee agrees not to work for direct competitors for 12 months after termination.
                """,
                
                "Service Agreement (Spanish)": """
ACUERDO DE SERVICIOS PROFESIONALES

Este Acuerdo de Servicios ("Acuerdo") se celebra el 20 de febrero de 2024, entre Consultora López S.A. ("Proveedor") y Empresa Martinez Ltd. ("Cliente").

1. SERVICIOS
El Proveedor proporcionará servicios de consultoría legal especializada por un período de 6 meses.

2. COMPENSACIÓN
El Cliente pagará $50,000 USD por los servicios prestados, pagaderos en cuotas mensuales.

3. TERMINACIÓN
Cualquiera de las partes puede terminar este acuerdo con 15 días de aviso por escrito.

4. CONFIDENCIALIDAD
Ambas partes acuerdan mantener la confidencialidad de toda información compartida.

5. RESPONSABILIDADES
El Proveedor se compromete a cumplir con los más altos estándares profesionales.

6. JURISDICCIÓN
Este acuerdo se regirá por las leyes de España.
                """,
                
                "Purchase Agreement (French)": """
CONTRAT D'ACHAT IMMOBILIER

Ce Contrat d'Achat ("Contrat") est conclu le 10 mars 2024, entre Pierre Dubois ("Vendeur") et Marie Martin ("Acheteur").

1. PROPRIÉTÉ
Le Vendeur vend à l'Acheteur l'appartement situé au 123 Rue de la Paix, Paris.

2. PRIX
Le prix d'achat est de 850,000 EUR, payable selon les modalités convenues.

3. CONDITIONS
La vente est soumise à l'obtention d'un financement hypothécaire.

4. GARANTIES
Le Vendeur garantit que la propriété est libre de toute charge.

5. CLÔTURE
La clôture aura lieu le 15 avril 2024 chez le notaire.

6. JURIDICTION
Ce contrat est régi par le droit français.
                """,
                
                "NDA Agreement (German)": """
VERTRAULICHKEITSVEREINBARUNG

Diese Vertraulichkeitsvereinbarung ("Vereinbarung") wird am 25. März 2024 zwischen der TechGmbH ("Unternehmen") und Max Mustermann ("Empfänger") geschlossen.

1. VERTRAULICHE INFORMATIONEN
Alle vom Unternehmen bereitgestellten Informationen gelten als vertraulich.

2. VERPFLICHTUNGEN
Der Empfänger verpflichtet sich, alle vertraulichen Informationen zu schützen.

3. DAUER
Diese Vereinbarung gilt für einen Zeitraum von 5 Jahren.

4. HAFTUNG
Bei Verletzung der Vertraulichkeit können Schadensersatzansprüche geltend gemacht werden.

5. RÜCKGABE
Alle Unterlagen sind nach Beendigung zurückzugeben.

6. GERICHTSSTAND
Gerichtsstand ist München, Deutschland.
                """
            }
            
            selected_sample = st.selectbox("Choose a sample document:", list(sample_texts.keys()))
            
            col_sample1, col_sample2 = st.columns(2)
            
            with col_sample1:
                if st.button("📝 Analyze Sample with Basic Engine"):
                    st.session_state.sample_text = sample_texts[selected_sample]
                    st.session_state.analyze_sample = True
                    st.session_state.use_gemini_sample = False
                    st.rerun()
            
            with col_sample2:
                gemini_available = st.session_state.get('gemini_configured', False)
                if st.button("🤖 Analyze Sample with Gemini AI", disabled=not gemini_available):
                    if gemini_available:
                        st.session_state.sample_text = sample_texts[selected_sample]
                        st.session_state.analyze_sample = True
                        st.session_state.use_gemini_sample = True
                        st.rerun()
                    else:
                        st.error("Please configure Gemini AI first!")
            
            # Handle sample analysis
            if st.session_state.get('analyze_sample', False):
                st.session_state.analyze_sample = False
                text = st.session_state.get('sample_text', '')
                use_gemini = st.session_state.get('use_gemini_sample', False)
                
                if text:
                    st.markdown("### 📝 Sample Analysis Results")
                    
                    with st.spinner("Analyzing sample document..."):
                        if use_gemini and gemini_integration and gemini_integration.is_configured:
                            # Gemini analysis
                            original_lang = gemini_integration.detect_language(text)
                            analysis_result = gemini_integration.analyze_legal_document(text, 'en')
                            entities = gemini_integration.extract_entities_advanced(text, 'en')
                            ai_engine = "Gemini AI"
                        else:
                            # Basic analysis
                            try:
                                original_lang = detect(text[:1000])
                            except:
                                original_lang = 'en'
                            analysis_result = analyzer._basic_analysis(text)
                            entities = analyzer._extract_basic_entities(text)
                            ai_engine = "Basic Analysis"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Document Summary ({ai_engine}):**")
                        st.info(analysis_result.get('summary', 'No summary available'))
                        
                        st.markdown("**Key Parties:**")
                        parties = analysis_result.get('parties', [])
                        if parties:
                            for party in parties[:5]:
                                st.write(f"• {party}")
                        else:
                            st.write("None identified")
                    
                    with col2:
                        st.markdown("**Quick Stats:**")
                        st.metric("Language", LANGUAGES.get(original_lang, 'Unknown'))
                        st.metric("Entities", sum(len(v) for v in entities.values()))
                        st.metric("Document Type", analysis_result.get('document_type', 'Unknown'))
                        st.metric("AI Engine", ai_engine)
                        
                        st.markdown("**Risks & Obligations:**")
                        st.write(f"Risks: {len(analysis_result.get('risks', []))}")
                        st.write(f"Obligations: {len(analysis_result.get('obligations', []))}")
    
    with main_tab2:
        gemini_setup_page()
    
    with main_tab3:
        # Dashboard tab
        st.markdown('<div class="section-header">📊 User Dashboard</div>', unsafe_allow_html=True)
        
        # Analysis history
        st.markdown("### 📈 Analysis History")
        history = user_manager.get_user_history(st.session_state.user_id)
        
        if history:
            # Create a comprehensive history display
            history_df = pd.DataFrame(history, columns=[
                'Document Name', 'Analysis Date', 'Document Type', 'Word Count', 
                'Original Language', 'Target Language', 'Summary'
            ])
            
            # Format the dataframe
            history_df['Analysis Date'] = pd.to_datetime(history_df['Analysis Date']).dt.strftime('%Y-%m-%d %H:%M')
            history_df['Original Language'] = history_df['Original Language'].map(lambda x: LANGUAGES.get(x, x))
            history_df['Target Language'] = history_df['Target Language'].map(lambda x: LANGUAGES.get(x, x))
            
            st.dataframe(history_df, use_container_width=True, height=400)
            
            # Statistics
            st.markdown("### 📊 Usage Statistics")
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                st.metric("Total Analyses", len(history))
            
            with stats_col2:
                total_words = sum(row[3] for row in history if row[3])
                st.metric("Total Words Processed", f"{total_words:,}")
            
            with stats_col3:
                doc_types = [row[2] for row in history if row[2]]
                most_common_type = max(set(doc_types), key=doc_types.count) if doc_types else "N/A"
                st.metric("Most Common Doc Type", most_common_type)
            
            with stats_col4:
                languages = [row[4] for row in history if row[4]]
                most_common_lang = max(set(languages), key=languages.count) if languages else "N/A"
                lang_display = LANGUAGES.get(most_common_lang, most_common_lang)
                st.metric("Most Common Language", lang_display)
            
            # Download history
            if st.button("📥 Download Analysis History"):
                history_csv = history_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=history_csv,
                    file_name=f"analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No analysis history yet. Start by analyzing your first document!")
        
        # Account settings
        st.markdown("### ⚙️ Account Settings")
        with st.expander("Update Account Information"):
            col_set1, col_set2 = st.columns(2)
            
            with col_set1:
                new_email = st.text_input("Email", value=st.session_state.get('user_email', ''))
                new_full_name = st.text_input("Full Name", value=st.session_state.get('user_full_name', ''))
            
            with col_set2:
                new_organization = st.text_input("Organization", value=st.session_state.get('user_organization', ''))
                
            if st.button("💾 Save Changes"):
                st.success("Account information updated! (Note: This is a demo - changes are not actually saved)")

def main():
    """Main application entry point"""
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()