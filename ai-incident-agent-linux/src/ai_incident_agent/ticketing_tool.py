from __future__ import annotations

import argparse
from .ticketing import Ticketing


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a ticket file for an incident.")
    parser.add_argument("--title", required=True, help="Incident title")
    parser.add_argument("--description", required=True, help="Incident description")
    parser.add_argument("--severity", default="P2", help="Incident severity")
    parser.add_argument("--ticket-dir", default="tickets", help="Directory to save ticket files")
    args = parser.parse_args()

    tool = Ticketing("file", {"ticket_dir": args.ticket_dir})
    incident = {
        "title": args.title,
        "description": args.description,
        "severity": args.severity,
    }
    ticket = tool.create_ticket(incident)
    print(f"Created ticket {ticket['id']} at {ticket.get('file_path')}")


if __name__ == "__main__":
    main()
