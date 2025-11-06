#!/bin/bash

# =============================================================================
# GCP Monitoring and Alerting Setup
# Creates monitoring dashboards and alert policies for production services
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-cmsupload-476323}"
SERVICE_NAME="cms-automation-backend"
REGION="us-east1"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-alerts@example.com}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# =============================================================================
# Create Notification Channel
# =============================================================================

log_info "Creating notification channel for email: ${NOTIFICATION_EMAIL}"

# Note: For actual implementation, you would create this via API or console
# This is a reference command
log_info "To create notification channel, run:"
echo "  gcloud alpha monitoring channels create \\"
echo "    --display-name='Production Alerts' \\"
echo "    --type=email \\"
echo "    --channel-labels=email_address=${NOTIFICATION_EMAIL} \\"
echo "    --project=${PROJECT_ID}"

# =============================================================================
# Alert Policy: High Error Rate
# =============================================================================

log_info "Creating alert policy for high error rate..."

cat > /tmp/alert-high-error-rate.json << EOF
{
  "displayName": "High Error Rate - ${SERVICE_NAME}",
  "conditions": [
    {
      "displayName": "Error rate > 5%",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.05,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ]
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "combiner": "OR",
  "enabled": true,
  "documentation": {
    "content": "Error rate for ${SERVICE_NAME} has exceeded 5% for 5 minutes.",
    "mimeType": "text/markdown"
  }
}
EOF

log_info "Alert policy saved to /tmp/alert-high-error-rate.json"
log_info "To create the alert, run:"
echo "  gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-high-error-rate.json --project=${PROJECT_ID}"

# =============================================================================
# Alert Policy: High Latency
# =============================================================================

log_info "Creating alert policy for high latency..."

cat > /tmp/alert-high-latency.json << EOF
{
  "displayName": "High Latency - ${SERVICE_NAME}",
  "conditions": [
    {
      "displayName": "P95 latency > 2 seconds",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 2000,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_DELTA",
            "crossSeriesReducer": "REDUCE_PERCENTILE_95"
          }
        ]
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "combiner": "OR",
  "enabled": true,
  "documentation": {
    "content": "P95 latency for ${SERVICE_NAME} has exceeded 2 seconds for 5 minutes.",
    "mimeType": "text/markdown"
  }
}
EOF

log_info "Alert policy saved to /tmp/alert-high-latency.json"

# =============================================================================
# Alert Policy: High Memory Usage
# =============================================================================

log_info "Creating alert policy for high memory usage..."

cat > /tmp/alert-high-memory.json << EOF
{
  "displayName": "High Memory Usage - ${SERVICE_NAME}",
  "conditions": [
    {
      "displayName": "Memory usage > 80%",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.8,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_MEAN"
          }
        ]
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "combiner": "OR",
  "enabled": true,
  "documentation": {
    "content": "Memory usage for ${SERVICE_NAME} has exceeded 80% for 5 minutes. Consider increasing memory allocation.",
    "mimeType": "text/markdown"
  }
}
EOF

log_info "Alert policy saved to /tmp/alert-high-memory.json"

# =============================================================================
# Alert Policy: Max Instances Reached
# =============================================================================

log_info "Creating alert policy for max instances..."

cat > /tmp/alert-max-instances.json << EOF
{
  "displayName": "Max Instances Reached - ${SERVICE_NAME}",
  "conditions": [
    {
      "displayName": "Instance count >= 10",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/container/instance_count\"",
        "comparison": "COMPARISON_GE",
        "thresholdValue": 10,
        "duration": "60s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_MAX"
          }
        ]
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "combiner": "OR",
  "enabled": true,
  "documentation": {
    "content": "${SERVICE_NAME} has reached maximum instances (10). Consider increasing max instances or optimizing performance.",
    "mimeType": "text/markdown"
  }
}
EOF

log_info "Alert policy saved to /tmp/alert-max-instances.json"

# =============================================================================
# Create Monitoring Dashboard
# =============================================================================

log_info "Creating monitoring dashboard..."

cat > /tmp/dashboard-${SERVICE_NAME}.json << EOF
{
  "displayName": "CMS Automation Production Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Count",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Requests/sec",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Errors/sec",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Latency (P50, P95, P99)",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_DELTA",
                    "crossSeriesReducer": "REDUCE_PERCENTILE_50",
                    "groupByFields": []
                  }
                }
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            }],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Latency (ms)",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Memory Utilization",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Utilization",
              "scale": "LINEAR"
            }
          }
        }
      },
      {
        "yPos": 8,
        "width": 12,
        "height": 4,
        "widget": {
          "title": "Instance Count",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/container/instance_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }],
            "timeshiftDuration": "0s",
            "yAxis": {
              "label": "Instances",
              "scale": "LINEAR"
            }
          }
        }
      }
    ]
  }
}
EOF

log_info "Dashboard configuration saved to /tmp/dashboard-${SERVICE_NAME}.json"
log_info "To create the dashboard, run:"
echo "  gcloud monitoring dashboards create --config-from-file=/tmp/dashboard-${SERVICE_NAME}.json --project=${PROJECT_ID}"

# =============================================================================
# Summary
# =============================================================================

log_success "Monitoring configuration files created!"
echo ""
log_info "========================================="
log_info "Next Steps"
log_info "========================================="
echo "1. Create notification channel:"
echo "   gcloud alpha monitoring channels create \\"
echo "     --display-name='Production Alerts' \\"
echo "     --type=email \\"
echo "     --channel-labels=email_address=${NOTIFICATION_EMAIL} \\"
echo "     --project=${PROJECT_ID}"
echo ""
echo "2. Get notification channel ID:"
echo "   gcloud alpha monitoring channels list --project=${PROJECT_ID}"
echo ""
echo "3. Update alert policies with notification channel ID"
echo ""
echo "4. Create alert policies:"
echo "   gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-high-error-rate.json --project=${PROJECT_ID}"
echo "   gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-high-latency.json --project=${PROJECT_ID}"
echo "   gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-high-memory.json --project=${PROJECT_ID}"
echo "   gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-max-instances.json --project=${PROJECT_ID}"
echo ""
echo "5. Create monitoring dashboard:"
echo "   gcloud monitoring dashboards create --config-from-file=/tmp/dashboard-${SERVICE_NAME}.json --project=${PROJECT_ID}"
echo ""
log_info "========================================="
log_info "View dashboards: https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
log_info "View alerts: https://console.cloud.google.com/monitoring/alerting?project=${PROJECT_ID}"
log_info "========================================="
