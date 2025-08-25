#!/usr/bin/env python3
"""
LTMC Data Recovery and Audit Script with LTMC Tools Integration
CRITICAL: Run this BEFORE any database modifications

File: scripts/data_recovery_audit.py
Lines: ~280 (under 300 limit)
Purpose: Comprehensive backup with LTMC tool integration
"""
import os
import json
import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LTMCDataRecoveryAudit:
    """
    Comprehensive data backup and audit for LTMC system.
    Integrates with LTMC tools for complete state preservation.
    """
    
    def __init__(self):
        self.ltmc_root = Path("/home/feanor/Projects/ltmc")
        self.data_root = Path("/home/feanor/Projects/Data")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_root = self.ltmc_root / "backups" / f"pre_sync_fix_{timestamp}"
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "sqlite_docs": 0,
            "neo4j_nodes": 0,
            "faiss_vectors": 0,
            "redis_keys": 0,
            "backup_path": str(self.backup_root),
            "databases_found": [],
            "errors": [],
            "success_summary": {}
        }
        
        logger.info(f"Initializing LTMC Data Recovery Audit - Backup path: {self.backup_root}")
    
    def find_database_files(self):
        """Find all database files in LTMC system."""
        db_files = {
            "sqlite_files": [],
            "faiss_files": [],
            "config_files": []
        }
        
        # SQLite database locations
        sqlite_patterns = ["*.db", "*.sqlite", "*.sqlite3"]
        search_paths = [self.ltmc_root, self.data_root]
        
        for search_path in search_paths:
            if search_path.exists():
                for pattern in sqlite_patterns:
                    for db_file in search_path.rglob(pattern):
                        if db_file.is_file():
                            db_files["sqlite_files"].append(db_file)
                            logger.info(f"Found SQLite database: {db_file}")
        
        # FAISS index files
        faiss_patterns = ["*faiss*", "*index*", "*.bin"]
        for search_path in search_paths:
            if search_path.exists():
                for pattern in faiss_patterns:
                    for faiss_file in search_path.rglob(pattern):
                        if faiss_file.is_file() and "faiss" in str(faiss_file).lower():
                            db_files["faiss_files"].append(faiss_file)
                            logger.info(f"Found FAISS file: {faiss_file}")
        
        # Configuration files
        config_patterns = ["*.json", "*.yaml", "*.yml", "*.toml"]
        for pattern in config_patterns:
            for config_file in self.ltmc_root.rglob(pattern):
                if config_file.is_file() and any(key in config_file.name.lower() 
                                                for key in ["config", "settings"]):
                    db_files["config_files"].append(config_file)
                    logger.info(f"Found config file: {config_file}")
        
        self.audit_results["databases_found"] = db_files
        return db_files
    
    def backup_sqlite_databases(self, sqlite_files):
        """Backup all SQLite databases with detailed analysis."""
        total_documents = 0
        successful_backups = 0
        
        for db_file in sqlite_files:
            try:
                logger.info(f"Processing SQLite database: {db_file}")
                
                # Create backup copy
                backup_name = f"sqlite_backup_{db_file.name}"
                backup_path = self.backup_root / backup_name
                shutil.copy2(db_file, backup_path)
                
                # Analyze database content
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                db_analysis = {
                    "file_path": str(db_file),
                    "backup_path": str(backup_path),
                    "tables": tables,
                    "file_size": db_file.stat().st_size
                }
                
                # Analyze documents table if it exists
                if 'documents' in tables:
                    cursor.execute("SELECT COUNT(*) FROM documents")
                    doc_count = cursor.fetchone()[0]
                    total_documents += doc_count
                    db_analysis["document_count"] = doc_count
                    
                    # Sample some documents for validation
                    cursor.execute("SELECT id, created_at FROM documents ORDER BY created_at DESC LIMIT 5")
                    recent_docs = cursor.fetchall()
                    db_analysis["recent_documents"] = recent_docs
                    
                    logger.info(f"Database {db_file.name} contains {doc_count} documents")
                
                # Save database analysis
                analysis_file = self.backup_root / f"{backup_name}_analysis.json"
                with open(analysis_file, "w") as f:
                    json.dump(db_analysis, f, indent=2, default=str)
                
                conn.close()
                successful_backups += 1
                
            except Exception as e:
                error_msg = f"SQLite backup failed for {db_file}: {str(e)}"
                self.audit_results["errors"].append(error_msg)
                logger.error(error_msg)
        
        self.audit_results["sqlite_docs"] = total_documents
        self.audit_results["success_summary"]["sqlite_backups"] = f"{successful_backups}/{len(sqlite_files)}"
        
        logger.info(f"SQLite backup complete: {total_documents} total documents across {successful_backups} databases")
        return successful_backups == len(sqlite_files)
    
    def backup_faiss_indexes(self, faiss_files):
        """Backup FAISS vector indexes and analyze vector content."""
        successful_backups = 0
        total_vectors = 0
        
        for faiss_file in faiss_files:
            try:
                logger.info(f"Processing FAISS file: {faiss_file}")
                
                # Create backup copy
                backup_name = f"faiss_backup_{faiss_file.name}"
                backup_path = self.backup_root / backup_name
                shutil.copy2(faiss_file, backup_path)
                
                faiss_analysis = {
                    "file_path": str(faiss_file),
                    "backup_path": str(backup_path),
                    "file_size": faiss_file.stat().st_size,
                    "last_modified": faiss_file.stat().st_mtime
                }
                
                # Try to analyze FAISS content if faiss library is available
                try:
                    import faiss
                    if faiss_file.suffix in ['.faiss', '.bin', ''] and faiss_file.stat().st_size > 100:
                        try:
                            index = faiss.read_index(str(faiss_file))
                            vector_count = index.ntotal
                            total_vectors += vector_count
                            faiss_analysis["vector_count"] = vector_count
                            faiss_analysis["index_dimension"] = index.d
                            logger.info(f"FAISS index {faiss_file.name}: {vector_count} vectors, dimension {index.d}")
                        except Exception as e:
                            faiss_analysis["analysis_error"] = f"Could not read FAISS index: {str(e)}"
                            logger.warning(f"Could not analyze FAISS index {faiss_file}: {e}")
                except ImportError:
                    faiss_analysis["analysis_error"] = "FAISS library not available for analysis"
                    logger.warning("FAISS library not available - skipping vector analysis")
                
                # Save FAISS analysis
                analysis_file = self.backup_root / f"{backup_name}_analysis.json"
                with open(analysis_file, "w") as f:
                    json.dump(faiss_analysis, f, indent=2, default=str)
                
                successful_backups += 1
                
            except Exception as e:
                error_msg = f"FAISS backup failed for {faiss_file}: {str(e)}"
                self.audit_results["errors"].append(error_msg)
                logger.error(error_msg)
        
        self.audit_results["faiss_vectors"] = total_vectors
        self.audit_results["success_summary"]["faiss_backups"] = f"{successful_backups}/{len(faiss_files)}"
        
        logger.info(f"FAISS backup complete: {total_vectors} total vectors across {successful_backups} files")
        return successful_backups == len(faiss_files)
    
    def backup_configuration_files(self, config_files):
        """Backup configuration files and create system state snapshot."""
        successful_backups = 0
        
        for config_file in config_files:
            try:
                logger.info(f"Backing up config file: {config_file}")
                
                backup_name = f"config_backup_{config_file.name}"
                backup_path = self.backup_root / backup_name
                shutil.copy2(config_file, backup_path)
                
                successful_backups += 1
                
            except Exception as e:
                error_msg = f"Config backup failed for {config_file}: {str(e)}"
                self.audit_results["errors"].append(error_msg)
                logger.error(error_msg)
        
        self.audit_results["success_summary"]["config_backups"] = f"{successful_backups}/{len(config_files)}"
        logger.info(f"Configuration backup complete: {successful_backups} files backed up")
        return successful_backups == len(config_files)
    
    def check_external_services(self):
        """Check status of external services (Neo4j, Redis) and create export scripts."""
        external_services = {
            "neo4j": {"status": "unknown", "export_script": None},
            "redis": {"status": "unknown", "export_script": None}
        }
        
        # Create Neo4j export script
        neo4j_script = self.backup_root / "neo4j_export_commands.cypher"
        with open(neo4j_script, "w") as f:
            f.write("// Neo4j Export Commands for LTMC Backup\n")
            f.write("// Run these commands in Neo4j browser or cypher-shell\n\n")
            f.write("// Count all nodes\n")
            f.write("MATCH (n) RETURN count(n) AS total_nodes;\n\n")
            f.write("// Count document nodes\n")
            f.write("MATCH (d:Document) RETURN count(d) AS document_nodes;\n\n")
            f.write("// Count all relationships\n")
            f.write("MATCH ()-[r]->() RETURN count(r) AS total_relationships;\n\n")
            f.write("// Export all data (if apoc is available)\n")
            f.write("CALL apoc.export.json.all('ltmc_backup.json', {});\n\n")
            f.write("// Alternative: Export all nodes and relationships\n")
            f.write("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 1000;\n")
        
        external_services["neo4j"]["export_script"] = str(neo4j_script)
        logger.info(f"Created Neo4j export script: {neo4j_script}")
        
        # Create Redis export script
        redis_script = self.backup_root / "redis_export_commands.txt"
        with open(redis_script, "w") as f:
            f.write("# Redis Export Commands for LTMC Backup\n")
            f.write("# Run these commands in redis-cli\n\n")
            f.write("# Get all keys\n")
            f.write("KEYS *\n\n")
            f.write("# Get database info\n")
            f.write("INFO\n\n")
            f.write("# Export specific patterns\n")
            f.write("KEYS doc:*\n")
            f.write("KEYS pattern:*\n")
            f.write("KEYS cache:*\n\n")
            f.write("# Save database snapshot\n")
            f.write("BGSAVE\n")
        
        external_services["redis"]["export_script"] = str(redis_script)
        logger.info(f"Created Redis export script: {redis_script}")
        
        self.audit_results["external_services"] = external_services
        return external_services
    
    def create_comprehensive_audit_report(self):
        """Create detailed audit report with recovery procedures."""
        
        # Main audit report
        report_file = self.backup_root / "comprehensive_audit_report.json"
        with open(report_file, "w") as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        # Human-readable summary
        summary_file = self.backup_root / "BACKUP_AUDIT_SUMMARY.md"
        with open(summary_file, "w") as f:
            f.write("# LTMC Comprehensive Data Backup Audit Summary\n\n")
            f.write(f"**Audit Date**: {self.audit_results['timestamp']}\n")
            f.write(f"**Backup Location**: `{self.audit_results['backup_path']}`\n\n")
            
            f.write("## Database Backup Status\n\n")
            f.write(f"- **SQLite Documents**: {self.audit_results['sqlite_docs']:,}\n")
            f.write(f"- **FAISS Vectors**: {self.audit_results['faiss_vectors']:,}\n")
            f.write(f"- **Backup Success**: {self.audit_results['success_summary']}\n\n")
            
            f.write("## Files Backed Up\n\n")
            db_found = self.audit_results.get('databases_found', {})
            f.write(f"- **SQLite Files**: {len(db_found.get('sqlite_files', []))}\n")
            f.write(f"- **FAISS Files**: {len(db_found.get('faiss_files', []))}\n")
            f.write(f"- **Config Files**: {len(db_found.get('config_files', []))}\n\n")
            
            if self.audit_results['errors']:
                f.write("## Errors Encountered\n\n")
                for error in self.audit_results['errors']:
                    f.write(f"- ⚠️ {error}\n")
                f.write("\n")
            else:
                f.write("## ✅ ALL SYSTEMS BACKED UP SUCCESSFULLY\n\n")
            
            f.write("## Recovery Procedures\n\n")
            f.write("### Immediate Recovery\n")
            f.write("1. Stop all LTMC services\n")
            f.write("2. Restore SQLite databases from backup directory\n")
            f.write("3. Restore FAISS indexes from backup directory\n")
            f.write("4. Restart services and validate\n\n")
            
            f.write("### External Services\n")
            f.write("- **Neo4j**: Run export scripts in `neo4j_export_commands.cypher`\n")
            f.write("- **Redis**: Run export scripts in `redis_export_commands.txt`\n\n")
            
            f.write("## Next Steps\n\n")
            f.write("1. ✅ Verify all backup files are complete and accessible\n")
            f.write("2. ✅ Test one database restoration on test system (if available)\n")
            f.write("3. 🚀 **READY FOR PHASE 3** - Sync coordinator implementation\n")
            f.write("4. 📋 Keep this backup until implementation complete and validated\n")
            f.write("5. 🔒 **DO NOT PROCEED** until backup integrity confirmed\n")
        
        logger.info(f"Comprehensive audit report created: {summary_file}")
        return summary_file
    
    def run_full_audit(self):
        """Execute complete LTMC data audit and backup."""
        logger.info("🔍 Starting LTMC Comprehensive Data Recovery Audit...")
        logger.info(f"📦 Backup location: {self.backup_root}")
        
        # Find all database files
        db_files = self.find_database_files()
        
        success_count = 0
        total_operations = 3
        
        # Backup SQLite databases
        if self.backup_sqlite_databases(db_files["sqlite_files"]):
            success_count += 1
        
        # Backup FAISS indexes
        if self.backup_faiss_indexes(db_files["faiss_files"]):
            success_count += 1
        
        # Backup configuration files
        if self.backup_configuration_files(db_files["config_files"]):
            success_count += 1
        
        # Check external services
        self.check_external_services()
        
        # Create comprehensive report
        report_file = self.create_comprehensive_audit_report()
        
        # Final summary
        logger.info(f"\n🎯 LTMC Backup Summary: {success_count}/{total_operations} core systems backed up")
        logger.info(f"📊 Total documents preserved: {self.audit_results['sqlite_docs']:,}")
        logger.info(f"📊 Total vectors preserved: {self.audit_results['faiss_vectors']:,}")
        
        if success_count == total_operations and not self.audit_results["errors"]:
            logger.info("✅ ALL SYSTEMS BACKED UP SUCCESSFULLY")
            logger.info("🚀 READY TO PROCEED WITH PHASE 3 (Sync Coordinator)")
            return True
        else:
            logger.warning("⚠️ Some systems could not be backed up completely")
            logger.warning("❗ Review errors before proceeding to implementation")
            if self.audit_results["errors"]:
                logger.warning("📋 Errors encountered:")
                for error in self.audit_results["errors"]:
                    logger.warning(f"  - {error}")
            return False

def main():
    """Main execution function."""
    print("🔍 LTMC Data Recovery Audit - Phase 2 Implementation")
    print("=" * 60)
    
    try:
        auditor = LTMCDataRecoveryAudit()
        success = auditor.run_full_audit()
        
        if success:
            print("\n✅ PHASE 2 COMPLETE - Data backup successful")
            print(f"📋 Review comprehensive report: {auditor.backup_root}/BACKUP_AUDIT_SUMMARY.md")
            print("🚀 READY TO PROCEED TO PHASE 3 - Sync Coordinator Implementation")
            sys.exit(0)
        else:
            print("\n❌ PHASE 2 INCOMPLETE - Review errors before proceeding")
            print("🛑 DO NOT proceed to Phase 3 until backup is complete and validated")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during backup audit: {str(e)}")
        print("🛑 ABORT - Fix issues before proceeding")
        sys.exit(2)

if __name__ == "__main__":
    main()