import os
import logging
import msoffcrypto
import pypdf  
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from models.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

def process_document(uploaded_file, password=None):
    
    # Create unique temp filenames to avoid collisions
    temp_path = f"temp_{uploaded_file.name}"
    decrypted_temp_path = f"decrypted_{uploaded_file.name}"
    
    try:
        # Save uploaded file to disk temporarily
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        ms_office_file = file_extension in [".docx", ".xlsx", ".xls"]
        temp_path_for_loader = temp_path

        # Handle MS Office Decryption
        if ms_office_file and password:
            try:
                with msoffcrypto.OfficeFile(open(temp_path, "rb")) as office_file:
                    office_file.key = password.encode() 
                    with open(decrypted_temp_path, "wb") as f_decrypted:
                        office_file.decrypt(f_decrypted)
                temp_path_for_loader = decrypted_temp_path
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                raise ValueError("Decryption failed. Check password or file integrity.")

        # Load Documents
        docs = []
        if file_extension == ".pdf":
            try:
                # FIX: Check encryption status explicitly before loading
                reader = pypdf.PdfReader(temp_path_for_loader)
                
                if reader.is_encrypted:
                    # File IS encrypted: We need the password
                    if not password:
                        raise ValueError("This PDF is password protected. Please enter a password.")
                    loader = PyPDFLoader(temp_path_for_loader, password=password)
                else:
                    # File is NOT encrypted: Force password to None so it opens automatically
                    # This ignores any password the user might have typed by mistake
                    loader = PyPDFLoader(temp_path_for_loader, password=None)
                
                docs = loader.load()

            except Exception as e:
                # Keep the fallback just in case, but the logic above prevents most issues
                if "not an encrypted file" in str(e).lower() and password:
                    logger.warning("Password provided for non-encrypted PDF. Retrying without password.")
                    loader = PyPDFLoader(temp_path_for_loader, password=None)
                    docs = loader.load()
                else:
                    raise e

        elif file_extension == ".docx":
            loader = Docx2txtLoader(temp_path_for_loader)
            docs = loader.load()
        elif file_extension in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(temp_path_for_loader, mode="elements") 
            docs = loader.load()
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Check for Empty Content
        if not docs:
            raise ValueError("No content could be extracted from the document.")

        # Split Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""] 
        )
        splits = text_splitter.split_documents(docs)

        if not splits:
             raise ValueError("Document contains no text usable for analysis.")

        # Create Vector Store
        embeddings = get_embedding_model()
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
        
        return vectorstore.as_retriever()

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise e

    finally:
        # Cleanup temp files
        for path in [temp_path, decrypted_temp_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to remove temp file {path}: {cleanup_err}")