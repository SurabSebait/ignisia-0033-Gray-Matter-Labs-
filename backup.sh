#!/bin/bash
# Backup and Restore Script for Chroma Vector Database

BACKUP_DIR="./backups"
CHROMA_DB_DIR="./chroma_db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create backup directory
mkdir -p $BACKUP_DIR

case "$1" in
    backup)
        echo -e "${YELLOW}📦 Creating backup...${NC}"
        BACKUP_FILE="$BACKUP_DIR/chroma_db_backup_$TIMESTAMP.tar.gz"
        
        if [ -d "$CHROMA_DB_DIR" ]; then
            tar -czf "$BACKUP_FILE" "$CHROMA_DB_DIR"
            echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
            echo "Size: $(du -h $BACKUP_FILE | cut -f1)"
        else
            echo -e "${RED}✗ Chroma database not found${NC}"
            exit 1
        fi
        ;;
        
    restore)
        if [ -z "$2" ]; then
            echo "Usage: $0 restore <backup_file>"
            echo ""
            echo "Available backups:"
            ls -lh $BACKUP_DIR/*.tar.gz 2>/dev/null || echo "No backups found"
            exit 1
        fi
        
        BACKUP_FILE="$2"
        
        if [ ! -f "$BACKUP_FILE" ]; then
            echo -e "${RED}✗ Backup file not found: $BACKUP_FILE${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}♻️  Restoring from backup...${NC}"
        echo "⚠️  This will overwrite existing data!"
        read -p "Continue? (yes/no) " confirm
        
        if [ "$confirm" = "yes" ]; then
            sudo supervisorctl stop fastapi-rag
            rm -rf "$CHROMA_DB_DIR"
            tar -xzf "$BACKUP_FILE"
            sudo supervisorctl start fastapi-rag
            echo -e "${GREEN}✓ Restore complete${NC}"
        else
            echo "Restore cancelled"
        fi
        ;;
        
    list)
        echo -e "${YELLOW}📋 Available backups:${NC}"
        if [ -z "$(ls -A $BACKUP_DIR)" ]; then
            echo "No backups found in $BACKUP_DIR"
        else
            ls -lh $BACKUP_DIR/
        fi
        ;;
        
    *)
        echo "FastAPI RAG - Backup/Restore Script"
        echo "Usage: $0 {backup|restore|list}"
        echo ""
        echo "Examples:"
        echo "  $0 backup              # Create backup"
        echo "  $0 list                # List all backups"
        echo "  $0 restore <file>      # Restore from backup"
        exit 1
        ;;
esac
