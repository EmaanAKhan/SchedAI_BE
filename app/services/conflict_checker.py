from datetime import timedelta
from app.models import Appointment

def check_conflicts(host_user_id, start_time, end_time, exclude_id=None):
    query = Appointment.query.filter(
        Appointment.host_user_id == host_user_id,
        Appointment.status == 'confirmed',
        Appointment.start_time < end_time,
        Appointment.end_time > start_time
    )
    if exclude_id:
        query = query.filter(Appointment.id != exclude_id)

    overlapping = query.all()
    if overlapping:
        return {'conflict': True, 'type': 'double_booking'}

    # check 3+ back to back
    day_start = start_time.replace(hour=0, minute=0, second=0)
    day_end = day_start + timedelta(days=1)
    day_appts = Appointment.query.filter(
        Appointment.host_user_id == host_user_id,
        Appointment.status == 'confirmed',
        Appointment.start_time >= day_start,
        Appointment.start_time < day_end
    ).order_by(Appointment.start_time).all()

    if len(day_appts) >= 2:
        back_to_back = 0
        for i in range(len(day_appts) - 1):
            gap = (day_appts[i+1].start_time - day_appts[i].end_time).total_seconds() / 60
            if gap <= 5:
                back_to_back += 1
                if back_to_back >= 2:
                    return {'conflict': True, 'type': 'back_to_back'}
            else:
                back_to_back = 0

    # check focus block clash
    focus_clash = Appointment.query.filter(
        Appointment.host_user_id == host_user_id,
        Appointment.type == 'focus',
        Appointment.status == 'confirmed',
        Appointment.start_time < end_time,
        Appointment.end_time > start_time
    ).first()
    if focus_clash:
        return {'conflict': True, 'type': 'focus_clash'}

    return {'conflict': False}