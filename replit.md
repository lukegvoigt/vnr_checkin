# Teacher Appreciation Dinner Event App

## Overview
This is an event check-in system for the Teacher Appreciation Dinner. It includes:
- QR code scanning for attendee check-in
- Manual name/code lookup
- Attendee list management with year filtering
- Sponsor portal for ticket distribution

## Project Structure
- `app.py` - Main Streamlit application with check-in and attendee list functionality
- `pages/sponsor.py` - Sponsor portal for ticket distribution
- `db_info.py` - Database setup and management utilities
- `add_new_entries.py` - Script for adding new attendees
- `backup_2025_attendees.py` - Backup script for 2025 data
- `attendees_backup_2025.csv` - Backup of 2025 attendee data

## Database Tables
- `attendees` - Main attendee table with year column (2025 for old, 2026 for new)
- `sponsors` - Sponsor information (username, password, company_name, sponsor_level, total_seats)
- `sponsor_tickets` - Individual tickets for sponsors to distribute

## Event Details (2026)
- Event: Teacher Appreciation Dinner
- Date: Thursday, February 5th, 2026
- Venue: Rainwater Conference Center, 1 Meeting Pl, Valdosta, GA 31601
- Doors Open: 5:30 PM
- Dinner: 6:00 PM
- End: 9:00 PM
- Keynote Speaker: Gerry Brooks

## Recent Changes
- January 2026: Added year column to attendees table
- January 2026: Created sponsor portal with ticket distribution
- January 2026: Backed up 2025 data to attendees_backup_2025.csv

## Notes
- Email integration: Gmail connected via Google Workspace. Sponsors can now email tickets directly to recipients through the sponsor portal.

## User Preferences
- Non-technical user - use simple language
- Event organizer for Rotary Teacher Appreciation Dinner
