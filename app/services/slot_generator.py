from datetime import datetime, timedelta, date
from app.models import AvailabilityRule, Appointment

def generate_slots(user_id, target_date):
    day_of_week = target_date.weekday()  # 0=Mon
    rules = AvailabilityRule.query.filter_by(
        user_id=user_id,
        day_of_week=day_of_week,
        is_bookable=True
    ).all()

    if not rules:
        return []

    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    existing = Appointment.query.filter(
        Appointment.host_user_id == user_id,
        Appointment.start_time >= day_start,
        Appointment.start_time < day_end,
        Appointment.status == 'confirmed'
    ).all()

    slots = []
    for rule in rules:
        current = datetime.combine(target_date, rule.start_time)
        end = datetime.combine(target_date, rule.end_time)
        while current + timedelta(minutes=30) <= end:
            slot_end = current + timedelta(minutes=30)
            conflict = any(
                not (slot_end <= a.start_time or current >= a.end_time + timedelta(minutes=rule.buffer_minutes))
                for a in existing
            )
            if not conflict:
                slots.append({
                    'start': current.isoformat(),
                    'end': slot_end.isoformat()
                })
            current += timedelta(minutes=30)

    return slots