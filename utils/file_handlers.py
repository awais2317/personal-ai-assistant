import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import mimetypes
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

def secure_filename(filename: str) -> str:
    """Make a filename safe for use on the filesystem"""
    import re
    
    # Remove path separators
    filename = os.path.basename(filename)
    
    # Replace unsafe characters with underscores
    filename = re.sub(r'[^\w\s.-]', '_', filename)
    
    # Remove multiple spaces and underscores
    filename = re.sub(r'[\s_]+', '_', filename)
    
    # Remove leading/trailing dots and underscores
    filename = filename.strip('._')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed_file'
    
    return filename

class FileHandler:
    """Handle file upload, validation, and management"""
    
    def __init__(self):
        self.upload_folder = Path(settings.UPLOAD_FOLDER)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        self.max_file_size = settings.MAX_FILE_SIZE
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def validate_file_size(self, file_size: int) -> bool:
        """Check if file size is within limits"""
        return file_size <= self.max_file_size
    
    def save_uploaded_file(self, file, custom_filename: str = None) -> Dict[str, Any]:
        """
        Save an uploaded file to the upload directory
        
        Args:
            file: File object from web upload
            custom_filename: Optional custom filename
            
        Returns:
            Dictionary with file information
        """
        try:
            if not file or not file.filename:
                return {
                    'success': False,
                    'error': 'No file provided'
                }
            
            # Validate file extension
            if not self.is_allowed_file(file.filename):
                return {
                    'success': False,
                    'error': f'File type not allowed. Allowed types: {", ".join(self.allowed_extensions)}'
                }
            
            # Generate secure filename
            original_filename = file.filename
            if custom_filename:
                # Keep original extension
                extension = Path(original_filename).suffix
                filename = secure_filename(custom_filename + extension)
            else:
                filename = secure_filename(original_filename)
            
            # Ensure unique filename
            file_path = self.upload_folder / filename
            counter = 1
            while file_path.exists():
                name_part = Path(filename).stem
                extension = Path(filename).suffix
                filename = f"{name_part}_{counter}{extension}"
                file_path = self.upload_folder / filename
                counter += 1
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file info
            file_info = self.get_file_info(str(file_path))
            file_info.update({
                'success': True,
                'original_filename': original_filename,
                'saved_filename': filename,
                'file_path': str(file_path)
            })
            
            logger.info(f"File saved successfully: {filename}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'error': 'File not found'}
            
            stat = file_path.stat()
            
            return {
                'filename': file_path.name,
                'size': stat.st_size,
                'size_human': self._format_file_size(stat.st_size),
                'extension': file_path.suffix.lower().lstrip('.'),
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'path': str(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {'error': str(e)}
    
    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """List all files in the upload directory"""
        try:
            files = []
            
            for file_path in self.upload_folder.iterdir():
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    if 'error' not in file_info:
                        files.append(file_info)
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file from the upload directory"""
        try:
            file_path = self.upload_folder / secure_filename(filename)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'File not found'
                }
            
            file_path.unlink()
            
            return {
                'success': True,
                'message': f'File {filename} deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_path(self, filename: str) -> Optional[str]:
        """Get the full path to an uploaded file"""
        try:
            file_path = self.upload_folder / secure_filename(filename)
            if file_path.exists():
                return str(file_path)
            return None
            
        except Exception as e:
            logger.error(f"Error getting file path for {filename}: {str(e)}")
            return None
    
    def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up files older than specified days"""
        try:
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            deleted_files = []
            errors = []
            
            for file_path in self.upload_folder.iterdir():
                if file_path.is_file():
                    try:
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            deleted_files.append(file_path.name)
                    except Exception as e:
                        errors.append(f"Error deleting {file_path.name}: {str(e)}")
            
            return {
                'success': True,
                'deleted_files': deleted_files,
                'deleted_count': len(deleted_files),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            file_types = {}
            
            for file_path in self.upload_folder.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    total_size += size
                    file_count += 1
                    
                    extension = file_path.suffix.lower().lstrip('.')
                    if extension in file_types:
                        file_types[extension] += 1
                    else:
                        file_types[extension] = 1
            
            return {
                'total_files': file_count,
                'total_size': total_size,
                'total_size_human': self._format_file_size(total_size),
                'file_types': file_types,
                'upload_folder': str(self.upload_folder),
                'max_file_size': self._format_file_size(self.max_file_size),
                'allowed_extensions': list(self.allowed_extensions)
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {'error': str(e)}

# Global file handler instance
file_handler = FileHandler()
