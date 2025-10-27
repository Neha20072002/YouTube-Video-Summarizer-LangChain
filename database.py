import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

class SummaryDatabase:
    """Database manager for storing and retrieving YouTube video summaries"""
    
    def __init__(self, db_path: str = "summaries.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    summary_text TEXT NOT NULL,
                    summary_length TEXT,
                    summary_tone TEXT,
                    model_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    word_count INTEGER,
                    video_duration TEXT,
                    video_channel TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def save_summary(self, url: str, title: str, summary_text: str, 
                    summary_length: str = "Medium", summary_tone: str = "Professional",
                    model_used: str = "mistralai/Mistral-7B-Instruct-v0.3",
                    video_duration: str = None, video_channel: str = None) -> bool:
        """Save a new summary to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            word_count = len(summary_text.split())
            
            cursor.execute('''
                INSERT INTO summaries (url, title, summary_text, summary_length, 
                                    summary_tone, model_used, word_count, video_duration, video_channel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (url, title, summary_text, summary_length, summary_tone, 
                  model_used, word_count, video_duration, video_channel))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving summary: {e}")
            return False
    
    def get_all_summaries(self) -> List[Tuple]:
        """Retrieve all summaries from the database ordered by creation date"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM summaries ORDER BY created_at DESC')
            summaries = cursor.fetchall()
            conn.close()
            return summaries
        except Exception as e:
            print(f"Error retrieving summaries: {e}")
            return []
    
    def get_summary_by_id(self, summary_id: int) -> Optional[Tuple]:
        """Retrieve a specific summary by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM summaries WHERE id = ?', (summary_id,))
            summary = cursor.fetchone()
            conn.close()
            return summary
        except Exception as e:
            print(f"Error retrieving summary by ID: {e}")
            return None
    
    def search_summaries(self, query: str) -> List[Tuple]:
        """Search summaries by URL, title, or content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM summaries 
                WHERE url LIKE ? OR title LIKE ? OR summary_text LIKE ?
                ORDER BY created_at DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            summaries = cursor.fetchall()
            conn.close()
            return summaries
        except Exception as e:
            print(f"Error searching summaries: {e}")
            return []
    
    def delete_summary(self, summary_id: int) -> bool:
        """Delete a specific summary by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM summaries WHERE id = ?', (summary_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting summary: {e}")
            return False
    
    def clear_all_summaries(self) -> bool:
        """Clear all summaries from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM summaries')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing summaries: {e}")
            return False
    
    def get_summary_count(self) -> int:
        """Get the total number of summaries in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM summaries')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"Error getting summary count: {e}")
            return 0
    
    def get_recent_summaries(self, limit: int = 5) -> List[Tuple]:
        """Get the most recent summaries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM summaries ORDER BY created_at DESC LIMIT ?', (limit,))
            summaries = cursor.fetchall()
            conn.close()
            return summaries
        except Exception as e:
            print(f"Error getting recent summaries: {e}")
            return []


class ExportManager:
    """Manager for exporting summaries in different formats"""
    
    @staticmethod
    def export_to_markdown(summaries: List[Tuple]) -> str:
        """Export summaries to Markdown format"""
        if not summaries:
            return "# No Summaries Found\n\nNo summaries available for export."
        
        markdown_content = "# YouTube Video Summaries\n\n"
        markdown_content += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        markdown_content += f"*Total summaries: {len(summaries)}*\n\n---\n\n"
        
        for summary in summaries:
            id, url, title, summary_text, summary_length, summary_tone, model_used, created_at, word_count, video_duration, video_channel = summary
            
            markdown_content += f"## {title or 'Untitled'}\n\n"
            markdown_content += f"**URL:** [{url}]({url})\n\n"
            markdown_content += f"**Date:** {created_at}\n\n"
            markdown_content += f"**Length:** {summary_length}\n\n"
            markdown_content += f"**Tone:** {summary_tone}\n\n"
            markdown_content += f"**Word Count:** {word_count}\n\n"
            if video_duration:
                markdown_content += f"**Duration:** {video_duration}\n\n"
            if video_channel:
                markdown_content += f"**Channel:** {video_channel}\n\n"
            markdown_content += f"**Model:** {model_used}\n\n"
            markdown_content += f"### Summary\n\n{summary_text}\n\n---\n\n"
        
        return markdown_content
    
    @staticmethod
    def export_to_json(summaries: List[Tuple]) -> str:
        """Export summaries to JSON format"""
        if not summaries:
            return json.dumps({"summaries": [], "export_date": datetime.now().isoformat()}, indent=2)
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_summaries": len(summaries),
            "summaries": []
        }
        
        for summary in summaries:
            id, url, title, summary_text, summary_length, summary_tone, model_used, created_at, word_count, video_duration, video_channel = summary
            
            summary_data = {
                "id": id,
                "url": url,
                "title": title,
                "summary_text": summary_text,
                "summary_length": summary_length,
                "summary_tone": summary_tone,
                "model_used": model_used,
                "created_at": created_at,
                "word_count": word_count,
                "video_duration": video_duration,
                "video_channel": video_channel
            }
            export_data["summaries"].append(summary_data)
        
        return json.dumps(export_data, indent=2, default=str)
    
    @staticmethod
    def export_to_csv(summaries: List[Tuple]) -> str:
        """Export summaries to CSV format without pandas dependency"""
        if not summaries:
            return "No summaries available for export."
        
        # CSV header
        csv_content = "ID,URL,Title,Summary,Length,Tone,Model,Created At,Word Count,Duration,Channel\n"
        
        # Convert tuples to CSV rows
        for summary in summaries:
            id, url, title, summary_text, summary_length, summary_tone, model_used, created_at, word_count, video_duration, video_channel = summary
            
            # Escape CSV values (handle commas and quotes)
            def escape_csv_value(value):
                if value is None:
                    return ""
                value_str = str(value)
                if ',' in value_str or '"' in value_str or '\n' in value_str:
                    return '"' + value_str.replace('"', '""') + '"'
                return value_str
            
            csv_content += f"{id},{escape_csv_value(url)},{escape_csv_value(title)},{escape_csv_value(summary_text)},{escape_csv_value(summary_length)},{escape_csv_value(summary_tone)},{escape_csv_value(model_used)},{escape_csv_value(created_at)},{word_count},{escape_csv_value(video_duration)},{escape_csv_value(video_channel)}\n"
        
        return csv_content
    
    @staticmethod
    def save_export_file(content: str, filename: str, format_type: str) -> bool:
        """Save exported content to a file"""
        try:
            # Create exports directory if it doesn't exist
            os.makedirs("exports", exist_ok=True)
            
            # Add timestamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_with_timestamp = f"{filename}_{timestamp}.{format_type.lower()}"
            filepath = os.path.join("exports", filename_with_timestamp)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, filepath
        except Exception as e:
            print(f"Error saving export file: {e}")
            return False, None
