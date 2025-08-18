#!/bin/bash

# Setup Local Git Repository on Jenkins Server
set -e

echo "📁 Setting up local Git repository for LTMC..."

# SSH to Jenkins server and create Git repository
ssh feanor@192.168.1.119 << 'REMOTE_SCRIPT'
    # Create Git repositories directory
    mkdir -p /home/feanor/git-repos
    cd /home/feanor/git-repos
    
    # Initialize bare Git repository for LTMC
    if [ ! -d "ltmc.git" ]; then
        git init --bare ltmc.git
        echo "✅ Created bare Git repository: ltmc.git"
    else
        echo "📁 Git repository already exists: ltmc.git"
    fi
    
    # Set permissions
    chmod -R 755 ltmc.git
    
    echo "✅ Local Git repository ready at: feanor@192.168.1.119:/home/feanor/git-repos/ltmc.git"
REMOTE_SCRIPT

echo "✅ Local Git repository setup completed"

