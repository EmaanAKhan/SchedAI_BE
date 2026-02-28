from app import db
from app.models import Waitlist, Appointment
from app.services.slot_generator import generate_slots
from datetime import datetime, date, timedelta
import requests
import os

def check_waitlist(host_user_id):
    waiting = Waitlist.query.filter_by(host_user_id=host_user_id, status='waiting').all()
    booked = []
    for entry in waiting:
        # get free slots in their preferred window
        target_date = entry.preferred_start.date()
        slots = generate_slots(host_user_id, target_date)
        for slot in slots:
            slot_start = datetime.fromisoformat(slot['start'])
            slot_end = datetime.fromisoformat(slot['end'])
            if slot_start >= entry.preferred_start and slot_end <= entry.preferred_end:
                # book it
                appt = Appointment(
                    host_user_id=host_user_id,
                    guest_name=entry.guest_name,
                    guest_email=entry.guest_email,
                    title=f"Meeting with {entry.guest_name}",
                    reason=entry.guest_reason,
                    start_time=slot_start,
                    end_time=slot_end,
                    type='external',
                    status='confirmed'
                )
                db.session.add(appt)
                entry.status = 'booked'
                db.session.commit()
                # notify n8n
                try:
                    requests.post(os.getenv('N8N_WEBHOOK_URL', ''), json={
                        'guest_name': entry.guest_name,
                        'guest_email': entry.guest_email,
                        'start_time': slot_start.isoformat(),
                        'end_time': slot_end.isoformat()
                    }, timeout=3)
                except:
                    pass
                booked.append(entry.guest_name)
                break
    return booked