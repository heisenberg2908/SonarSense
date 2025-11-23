"""
Database helper for storing predictions and analytics
"""
import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3

class Database:
    """Simple SQLite database for storing predictions"""
    
    def __init__(self, db_path='sonar_predictions.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_meta TEXT,
                label TEXT NOT NULL,
                confidence REAL NOT NULL,
                probabilities TEXT NOT NULL,
                waveform_data TEXT,
                frequency_data TEXT,
                features TEXT,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized at {self.db_path}")
    
    def save_prediction(self, result: Dict) -> int:
        """Save a prediction result to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO results (user_meta, label, confidence, probabilities, 
                               waveform_data, frequency_data, features, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            json.dumps(result.get('user_meta', {})),
            result['prediction'],
            result['confidence'],
            json.dumps(result['probabilities']),
            json.dumps(result.get('waveform_data', {})),
            json.dumps(result.get('frequency_data', {})),
            json.dumps(result.get('features', [])),
            result['timestamp']
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_result(self, result_id: int) -> Optional[Dict]:
        """Get a single result by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM results WHERE id = ?', (result_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        return {
            'id': row['id'],
            'user_meta': json.loads(row['user_meta']),
            'label': row['label'],
            'confidence': row['confidence'],
            'probabilities': json.loads(row['probabilities']),
            'waveform_data': json.loads(row['waveform_data']) if row['waveform_data'] else {},
            'frequency_data': json.loads(row['frequency_data']) if row['frequency_data'] else {},
            'features': json.loads(row['features']) if row['features'] else [],
            'timestamp': row['timestamp'],
            'created_at': row['created_at']
        }
    
    def get_predictions(self, limit: int = 100) -> List[Dict]:
        """Get recent predictions from the database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM results
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        predictions = []
        
        for row in rows:
            predictions.append({
                'id': row['id'],
                'user_meta': json.loads(row['user_meta']),
                'prediction': row['label'],
                'confidence': row['confidence'],
                'probabilities': json.loads(row['probabilities']),
                'timestamp': row['timestamp'],
                'created_at': row['created_at']
            })
        
        conn.close()
        return predictions
    
    def get_statistics(self) -> Dict:
        """Get prediction statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        
        cursor.execute('SELECT COUNT(*) FROM results')
        total = cursor.fetchone()[0]
        
        
        cursor.execute('SELECT AVG(confidence) FROM results')
        avg_confidence = cursor.fetchone()[0] or 0
        
        
        cursor.execute('''
            SELECT label, COUNT(*) as count
            FROM results
            GROUP BY label
        ''')
        distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_predictions': total,
            'average_confidence': round(avg_confidence, 4),
            'prediction_distribution': distribution
        }
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get prediction history"""
        return self.get_predictions(limit=limit)
    
    def clear_predictions(self):
        """Clear all predictions from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM results')
        conn.commit()
        conn.close()