"""
Database models and initialization
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import sys
from pathlib import Path

# Add config to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "config"))

try:
    from settings import DATABASE_URL
except ImportError:
    DATABASE_URL = "sqlite+aiosqlite:///./data/omni_healer.db"

Base = declarative_base()


class ProxmoxNode(Base):
    """Proxmox node information"""
    __tablename__ = "proxmox_nodes"
    
    id = Column(Integer, primary_key=True)
    node_name = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default="unknown")
    last_scan = Column(DateTime, default=datetime.utcnow)
    
    vms = relationship("VirtualMachine", back_populates="node")
    containers = relationship("Container", back_populates="node")


class VirtualMachine(Base):
    """Virtual Machine information"""
    __tablename__ = "virtual_machines"
    
    id = Column(Integer, primary_key=True)
    vmid = Column(Integer, nullable=False)
    name = Column(String(100))
    node_id = Column(Integer, ForeignKey("proxmox_nodes.id"))
    status = Column(String(20), default="unknown")
    has_docker = Column(Boolean, default=False)
    last_scan = Column(DateTime, default=datetime.utcnow)
    
    node = relationship("ProxmoxNode", back_populates="vms")
    docker_containers = relationship("DockerContainer", back_populates="vm")
    errors = relationship("ErrorLog", back_populates="vm")


class Container(Base):
    """LXC Container information"""
    __tablename__ = "containers"
    
    id = Column(Integer, primary_key=True)
    ctid = Column(Integer, nullable=False)
    name = Column(String(100))
    node_id = Column(Integer, ForeignKey("proxmox_nodes.id"))
    status = Column(String(20), default="unknown")
    has_docker = Column(Boolean, default=False)
    last_scan = Column(DateTime, default=datetime.utcnow)
    
    node = relationship("ProxmoxNode", back_populates="containers")
    docker_containers = relationship("DockerContainer", back_populates="container")
    errors = relationship("ErrorLog", back_populates="container")


class DockerContainer(Base):
    """Docker container inside VM or LXC"""
    __tablename__ = "docker_containers"
    
    id = Column(Integer, primary_key=True)
    container_id = Column(String(100), nullable=False)
    name = Column(String(100))
    image = Column(String(200))
    status = Column(String(20))
    vm_id = Column(Integer, ForeignKey("virtual_machines.id"), nullable=True)
    container_id_fk = Column(Integer, ForeignKey("containers.id"), nullable=True)
    last_scan = Column(DateTime, default=datetime.utcnow)
    
    vm = relationship("VirtualMachine", back_populates="docker_containers")
    container = relationship("Container", back_populates="docker_containers")


class ErrorLog(Base):
    """Error logs from VMs, Containers, or Docker"""
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True)
    source_type = Column(String(20), nullable=False)  # vm, container, docker
    source_id = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=False)
    severity = Column(String(20), default="error")  # info, warning, error, critical
    timestamp = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    ai_analysis = Column(JSON, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    
    vm = relationship("VirtualMachine", back_populates="errors")
    container = relationship("Container", back_populates="errors")


class AICommand(Base):
    """AI-suggested commands for healing"""
    __tablename__ = "ai_commands"
    
    id = Column(Integer, primary_key=True)
    error_log_id = Column(Integer, ForeignKey("error_logs.id"))
    command = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")  # pending, approved, rejected, executed, failed
    auto_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)
    
    error_log = relationship("ErrorLog")


async def init_db():
    """Initialize database tables"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def get_session() -> AsyncSession:
    """Get database session"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
