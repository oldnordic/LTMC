#!/bin/bash

# Deploy LTMC Pipeline to Jenkins
set -e

JENKINS_URL="http://192.168.1.119:8080"
JOB_NAME="ltmc-mcp-server"

echo "🚀 Deploying LTMC Pipeline to Jenkins..."

# Create or update Jenkins job
if curl -s -f "${JENKINS_URL}/job/${JOB_NAME}/config.xml" >/dev/null 2>&1; then
    echo "🔄 Updating existing Jenkins job: ${JOB_NAME}"
    curl -X POST "${JENKINS_URL}/job/${JOB_NAME}/config.xml" \
         --data-binary "@jenkins-job-config.xml" \
         -H "Content-Type: text/xml"
else
    echo "✨ Creating new Jenkins job: ${JOB_NAME}"
    curl -X POST "${JENKINS_URL}/createItem?name=${JOB_NAME}" \
         --data-binary "@jenkins-job-config.xml" \
         -H "Content-Type: text/xml"
fi

echo "✅ Jenkins job deployed successfully!"
echo "🔗 Job URL: ${JENKINS_URL}/job/${JOB_NAME}/"

