import aiosqlite
from .config import Config

class DatabaseManager:
    def __init__(self):
        self.db_url = Config.DATABASE_URL
        self.db_path = self.db_url.replace("sqlite+aiosqlite:///", "")
    
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create proposals table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id INTEGER UNIQUE,
                    summary TEXT,
                    root_cause TEXT,
                    commands TEXT,
                    confidence TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP
                )
            ''')
            
            # Create logs table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT,
                    vm_id INTEGER,
                    vm_type TEXT,
                    log_content TEXT,
                    error_detected BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create execution history table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id INTEGER,
                    command TEXT,
                    success BOOLEAN,
                    output TEXT,
                    error TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    async def save_proposal(self, proposal):
        """Save a fix proposal to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO proposals (proposal_id, summary, root_cause, commands, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                proposal['proposal_id'],
                proposal['summary'],
                proposal['root_cause'],
                str(proposal['commands']),
                proposal['confidence']
            ))
            await db.commit()
            return proposal['proposal_id']
    
    async def update_proposal_status(self, proposal_id, status):
        """Update proposal status (pending, approved, rejected, executed)"""
        async with aiosqlite.connect(self.db_path) as db:
            if status == 'executed':
                await db.execute('''
                    UPDATE proposals SET status = ?, executed_at = CURRENT_TIMESTAMP
                    WHERE proposal_id = ?
                ''', (status, proposal_id))
            else:
                await db.execute('''
                    UPDATE proposals SET status = ? WHERE proposal_id = ?
                ''', (status, proposal_id))
            await db.commit()
    
    async def get_proposals(self, status=None):
        """Get all proposals, optionally filtered by status"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                cursor = await db.execute(
                    'SELECT * FROM proposals WHERE status = ? ORDER BY created_at DESC',
                    (status,)
                )
            else:
                cursor = await db.execute(
                    'SELECT * FROM proposals ORDER BY created_at DESC'
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def save_log(self, node_id, vm_id, vm_type, log_content, error_detected=False):
        """Save a log entry"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO logs (node_id, vm_id, vm_type, log_content, error_detected)
                VALUES (?, ?, ?, ?, ?)
            ''', (node_id, vm_id, vm_type, log_content, error_detected))
            await db.commit()
    
    async def get_error_logs(self, limit=100):
        """Get recent error logs"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM logs WHERE error_detected = TRUE
                ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def save_execution_result(self, proposal_id, command, success, output="", error=""):
        """Save command execution result"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO execution_history (proposal_id, command, success, output, error)
                VALUES (?, ?, ?, ?, ?)
            ''', (proposal_id, command, success, output, error))
            await db.commit()
    
    async def get_execution_history(self, proposal_id=None):
        """Get execution history, optionally filtered by proposal_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if proposal_id:
                cursor = await db.execute(
                    'SELECT * FROM execution_history WHERE proposal_id = ? ORDER BY executed_at DESC',
                    (proposal_id,)
                )
            else:
                cursor = await db.execute(
                    'SELECT * FROM execution_history ORDER BY executed_at DESC'
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]