from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

TICKETS_DIR = Path("tickets")


def save_incident(incident: dict[str, Any]) -> dict[str, Any]:
    ticket_file = TICKETS_DIR / f"{incident['id']}.json"
    with open(ticket_file, "w", encoding="utf-8") as file:
        json.dump(incident, file, indent=2)
    return incident


@app.route("/")
def index() -> str:
    """Render the dashboard HTML."""
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/incidents", methods=["GET"])
def get_incidents() -> dict[str, Any]:
    """List all incidents from the tickets directory."""
    incidents = []
    if TICKETS_DIR.exists():
        for ticket_file in sorted(TICKETS_DIR.glob("*.json"), reverse=True):
            try:
                with open(ticket_file, "r", encoding="utf-8") as f:
                    incident = json.load(f)
                    incident.setdefault("status", "open")
                    incidents.append(incident)
            except Exception as e:
                print(f"Error reading {ticket_file}: {e}")
    return jsonify(incidents)


@app.route("/api/incidents/<incident_id>", methods=["GET"])
def get_incident(incident_id: str) -> dict[str, Any]:
    """Retrieve a specific incident by ID."""
    ticket_file = TICKETS_DIR / f"{incident_id}.json"
    if ticket_file.exists():
        try:
            with open(ticket_file, "r", encoding="utf-8") as f:
                incident = json.load(f)
                incident.setdefault("status", "open")
                return jsonify(incident)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Incident not found"}), 404


@app.route("/api/incidents/<incident_id>/close", methods=["POST"])
def close_incident(incident_id: str) -> dict[str, Any]:
    ticket_file = TICKETS_DIR / f"{incident_id}.json"
    if not ticket_file.exists():
        return jsonify({"error": "Incident not found"}), 404

    try:
        with open(ticket_file, "r", encoding="utf-8") as f:
            incident = json.load(f)

        incident["status"] = "closed"
        save_incident(incident)
        return jsonify(incident)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/incidents/<incident_id>/reopen", methods=["POST"])
def reopen_incident(incident_id: str) -> dict[str, Any]:
    ticket_file = TICKETS_DIR / f"{incident_id}.json"
    if not ticket_file.exists():
        return jsonify({"error": "Incident not found"}), 404

    try:
        with open(ticket_file, "r", encoding="utf-8") as f:
            incident = json.load(f)

        incident["status"] = "open"
        save_incident(incident)
        return jsonify(incident)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Incident Agent Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
        }
        .incidents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        .incident-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }
        .incident-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .incident-id {
            font-size: 12px;
            color: #999;
            margin-bottom: 8px;
            font-weight: 500;
        }
        .incident-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }
        .incident-description {
            font-size: 14px;
            color: #666;
            margin-bottom: 12px;
            line-height: 1.5;
        }
        .incident-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 12px;
            border-top: 1px solid #f0f0f0;
        }
        .severity-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .severity-p1 {
            background: #ffebee;
            color: #c62828;
        }
        .severity-p2 {
            background: #fff3e0;
            color: #e65100;
        }
        .severity-p3 {
            background: #f3e5f5;
            color: #6a1b9a;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            background: #e8f5e9;
            color: #2e7d32;
        }
        .kb-badge {
            display: inline-block;
            margin-left: 8px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            background: #ffeb3b;
            color: #3e2723;
            letter-spacing: 0.02em;
        }
        .status-closed {
            background: #f5f5f5;
            color: #424242;
        }
        .incident-closed {
            opacity: 0.75;
            border: 1px solid #dcdcdc;
        }
        .close-btn {
            background: #d32f2f;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }
        .close-btn:hover {
            background: #b71c1c;
        }
        .reopen-btn {
            background: #2e7d32;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }
        .reopen-btn:hover {
            background: #1b5e20;
        }
        .status-filter {
            margin-left: 12px;
            padding: 10px 12px;
            border-radius: 6px;
            border: 1px solid #ccc;
            font-size: 14px;
            background: white;
            color: #333;
        }
        .status-filter:focus {
            outline: none;
            border-color: #667eea;
        }
        .header-controls {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 16px;
        }
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }
        .close-btn:hover {
            background: #b71c1c;
        }
        .empty-state {
            background: white;
            border-radius: 8px;
            padding: 60px 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        .empty-state-text {
            color: #666;
            font-size: 16px;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            animation: fadeIn 0.2s;
        }
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 8px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            animation: slideIn 0.3s;
        }
        .modal-header {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
        }
        .modal-close {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            color: #999;
        }
        .modal-close:hover {
            color: #333;
        }
        .modal-section {
            margin-bottom: 20px;
        }
        .modal-label {
            font-size: 12px;
            font-weight: 600;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .modal-value {
            font-size: 14px;
            color: #333;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
            word-break: break-word;
            white-space: pre-wrap;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }
        .refresh-btn:hover {
            background: #764ba2;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚨 AI Incident Agent Dashboard</h1>
            <p class="subtitle">Real-time monitoring and incident management</p>
            <div>
                <button class="refresh-btn" onclick="loadIncidents()">↻ Refresh</button>
                <select id="statusFilter" class="status-filter" onchange="loadIncidents()">
                    <option value="all">All statuses</option>
                    <option value="open">Open</option>
                    <option value="closed">Closed</option>
                </select>
            </div>
        </header>
        <div id="incidents-container" class="incidents-grid"></div>
    </div>

    <div id="incidentModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <div id="modalBody"></div>
        </div>
    </div>

    <script>
        async function loadIncidents() {
            try {
                const response = await fetch('/api/incidents');
                const incidents = await response.json();
                const container = document.getElementById('incidents-container');
                
                if (incidents.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state" style="grid-column: 1 / -1;">
                            <div class="empty-state-icon">📭</div>
                            <div class="empty-state-text">No incidents yet. All systems nominal!</div>
                        </div>
                    `;
                    return;
                }
                
                const selectedStatus = document.getElementById('statusFilter').value;
                const filteredIncidents = selectedStatus === 'all'
                    ? incidents
                    : incidents.filter(incident => incident.status === selectedStatus);

                if (filteredIncidents.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state" style="grid-column: 1 / -1;">
                            <div class="empty-state-icon">📭</div>
                            <div class="empty-state-text">No incidents match the selected filter.</div>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = filteredIncidents.map(incident => `
                    <div class="incident-card ${incident.status === 'closed' ? 'incident-closed' : ''}" onclick="viewIncident('${incident.id}')">
                        <div class="incident-id">${incident.id}</div>
                        <div class="incident-title">
                            ${incident.title}
                            ${incident.analysis && incident.analysis.source === 'knowledge_base' ? `<span class="kb-badge">KB</span>` : ''}
                        </div>
                        <div class="incident-description">${incident.description}</div>
                        <div class="incident-meta">
                            <span class="severity-badge severity-${incident.severity.toLowerCase()}">${incident.severity}</span>
                            <span class="status-badge ${incident.status === 'closed' ? 'status-closed' : ''}">${incident.status}</span>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading incidents:', error);
                document.getElementById('incidents-container').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-text">Error loading incidents</div>
                    </div>
                `;
            }
        }

        async function viewIncident(id) {
            try {
                const response = await fetch(`/api/incidents/${id}`);
                const incident = await response.json();
                const modalBody = document.getElementById('modalBody');
                
                const analysis = incident.analysis || {};
                const raw = incident.raw || {};
                
                modalBody.innerHTML = `
                    <div class="modal-header">${incident.title}</div>
                    <div class="modal-section">
                        <div class="modal-label">ID</div>
                        <div class="modal-value">${incident.id}</div>
                    </div>
                    <div class="modal-section">
                        <div class="modal-label">Status</div>
                        <div class="modal-value">${incident.status}</div>
                    </div>
                    <div class="modal-section">
                        <div class="modal-label">Severity</div>
                        <div class="modal-value">${incident.severity}</div>
                    </div>
                    <div class="modal-section">
                        <div class="modal-label">Description</div>
                        <div class="modal-value">${incident.description}</div>
                    </div>
                    <div class="modal-section">
                        <div class="modal-label">Root Cause</div>
                        <div class="modal-value">${incident.root_cause || analysis.summary || 'Not available'}</div>
                    </div>
                    <div class="modal-section">
                        <div class="modal-label">Analysis Source</div>
                        <div class="modal-value">${incident.analysis_source || analysis.source || 'ai'}</div>
                    </div>
                    ${analysis.knowledge_base_entry ? `
                        <div class="modal-section">
                            <div class="modal-label">Knowledge Base Entry</div>
                            <div class="modal-value">${analysis.knowledge_base_entry}</div>
                        </div>
                    ` : ''}
                    <div class="modal-section">
                        <div class="modal-label">Resolution</div>
                        <div class="modal-value">${incident.resolution || analysis.recommendation || 'Not available'}</div>
                    </div>
                    <div class="modal-section">
                        <div class="modal-label">Owner</div>
                        <div class="modal-value">${incident.owner || 'Not available'}</div>
                    </div>
                    ${analysis.knowledge_base ? `
                        ${analysis.knowledge_base.error_id ? `
                            <div class="modal-section">
                                <div class="modal-label">Error ID</div>
                                <div class="modal-value">${analysis.knowledge_base.error_id}</div>
                            </div>
                        ` : ''}
                        ${analysis.knowledge_base.error_description ? `
                            <div class="modal-section">
                                <div class="modal-label">Error Description</div>
                                <div class="modal-value">${analysis.knowledge_base.error_description}</div>
                            </div>
                        ` : ''}
                        ${analysis.knowledge_base.root_cause ? `
                            <div class="modal-section">
                                <div class="modal-label">Root Cause</div>
                                <div class="modal-value">${analysis.knowledge_base.root_cause}</div>
                            </div>
                        ` : ''}
                        ${analysis.knowledge_base.resolution ? `
                            <div class="modal-section">
                                <div class="modal-label">Resolution</div>
                                <div class="modal-value">${analysis.knowledge_base.resolution}</div>
                            </div>
                        ` : ''}
                        ${analysis.knowledge_base.owner ? `
                            <div class="modal-section">
                                <div class="modal-label">Owner</div>
                                <div class="modal-value">${analysis.knowledge_base.owner}</div>
                            </div>
                        ` : ''}
                        ${analysis.knowledge_base.last_updated ? `
                            <div class="modal-section">
                                <div class="modal-label">Last Updated</div>
                                <div class="modal-value">${analysis.knowledge_base.last_updated}</div>
                            </div>
                        ` : ''}
                    ` : ''}
                    ${analysis.summary ? `
                        <div class="modal-section">
                            <div class="modal-label">Analysis Summary</div>
                            <div class="modal-value">${analysis.summary}</div>
                        </div>
                    ` : ''}
                    ${analysis.recommendation ? `
                        <div class="modal-section">
                            <div class="modal-label">Recommendation</div>
                            <div class="modal-value">${analysis.recommendation}</div>
                        </div>
                    ` : ''}
                    ${raw.message ? `
                        <div class="modal-section">
                            <div class="modal-label">Raw Log Entry</div>
                            <div class="modal-value">${JSON.stringify(raw, null, 2)}</div>
                        </div>
                    ` : ''}
                    ${incident.status !== 'closed' ? `
                        <button class="close-btn" onclick="event.stopPropagation(); closeIncident('${incident.id}')">Close Ticket</button>
                    ` : `
                        <button class="reopen-btn" onclick="event.stopPropagation(); reopenIncident('${incident.id}')">Reopen Ticket</button>
                    `}
                `;
                
                document.getElementById('incidentModal').style.display = 'block';
            } catch (error) {
                console.error('Error viewing incident:', error);
            }
        }

        async function closeIncident(id) {
            try {
                const response = await fetch(`/api/incidents/${id}/close`, {
                    method: 'POST',
                });

                if (!response.ok) {
                    throw new Error('Failed to close incident');
                }

                await loadIncidents();
                closeModal();
            } catch (error) {
                console.error('Error closing incident:', error);
                alert('Unable to close incident. Check the console for details.');
            }
        }

        async function reopenIncident(id) {
            try {
                const response = await fetch(`/api/incidents/${id}/reopen`, {
                    method: 'POST',
                });

                if (!response.ok) {
                    throw new Error('Failed to reopen incident');
                }

                await loadIncidents();
                closeModal();
            } catch (error) {
                console.error('Error reopening incident:', error);
                alert('Unable to reopen incident. Check the console for details.');
            }
        }

        function closeModal() {
            document.getElementById('incidentModal').style.display = 'none';
        }

        window.onclick = function(event) {
            const modal = document.getElementById('incidentModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }

        // Load incidents on page load and refresh every 5 seconds
        loadIncidents();
        setInterval(loadIncidents, 5000);
    </script>
</body>
</html>
"""


def run(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    """Run the Flask web server."""
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run(debug=True)
