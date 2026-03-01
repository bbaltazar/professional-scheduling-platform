"""
Terminal-based customer communication simulator for cancelled appointments.
Simulates SMS/email conversations in the terminal until real Twilio integration.
"""
from typing import Optional, List, Tuple
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from dateutil.rrule import rrulestr
from google import genai
import os

# Import database models at module level
try:
    from .database import CalendarEvent, Booking, ServiceDB, ClientProfile
except ImportError:
    from database import CalendarEvent, Booking, ServiceDB, ClientProfile


class TerminalCustomerChat:
    """Simulate customer conversations in terminal for cancelled appointments."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize Gemini with new google.genai package
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                self.model_name = 'models/gemini-2.5-flash'
                self.has_ai = True
            except Exception as e:
                self.has_ai = False
        else:
            self.has_ai = False
    
    def format_datetime(self, date, time_obj) -> str:
        """Format date and time in a friendly way."""
        dt = datetime.combine(date, time_obj)
        return dt.strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")
    
    def get_next_available_slots(
        self, 
        specialist_id: int, 
        service_duration: int,
        from_date: datetime,
        limit: int = 3
    ) -> List[Tuple[datetime, time, time]]:
        """
        Find next available time slots after the cancelled appointment.
        Returns list of (date, start_time, end_time) tuples.
        """
        # Get all active availability events for this specialist
        availability_events = self.db.query(CalendarEvent).filter(
            CalendarEvent.specialist_id == specialist_id,
            CalendarEvent.event_type == "availability",
            CalendarEvent.is_active == True
        ).all()
        
        if not availability_events:
            return []
        
        # Generate availability instances for next 14 days
        end_search_date = from_date + timedelta(days=14)
        available_slots = []
        
        for event in availability_events:
            if not event.recurrence_rule:
                continue
            
            try:
                rrule = rrulestr(event.recurrence_rule, dtstart=from_date.date())
                dates = list(rrule.between(from_date.date(), end_search_date.date(), inc=True))
                
                for date in dates:
                    # Check if there's already a booking at this time
                    existing_booking = self.db.query(Booking).filter(
                        Booking.specialist_id == specialist_id,
                        Booking.date == date,
                        Booking.start_time == event.start_time,
                        Booking.status.in_(["confirmed", "completed"])
                    ).first()
                    
                    if not existing_booking:
                        # Calculate end time
                        dt = datetime.combine(date, event.start_time)
                        end_dt = dt + timedelta(minutes=service_duration)
                        available_slots.append((date, event.start_time, end_dt.time()))
                    
                    if len(available_slots) >= limit:
                        break
                        
            except Exception as e:
                print(f"Error parsing recurrence rule: {e}")
                continue
            
            if len(available_slots) >= limit:
                break
        
        return available_slots[:limit]
    
    def get_same_time_next_week(
        self,
        specialist_id: int,
        cancelled_date: datetime,
        cancelled_time: time,
        service_duration: int
    ) -> Optional[Tuple[datetime, time, time]]:
        """Check if same time slot is available next week."""
        next_week_date = cancelled_date + timedelta(days=7)
        
        # Check if there's a booking at this time
        existing_booking = self.db.query(Booking).filter(
            Booking.specialist_id == specialist_id,
            Booking.date == next_week_date,
            Booking.start_time == cancelled_time,
            Booking.status.in_(["confirmed", "completed"])
        ).first()
        
        if not existing_booking:
            # Calculate end time
            dt = datetime.combine(next_week_date, cancelled_time)
            end_dt = dt + timedelta(minutes=service_duration)
            return (next_week_date, cancelled_time, end_dt.time())
        
        return None
    
    def start_cancellation_conversation(
        self,
        booking_id: int,
        specialist_name: str,
        cancellation_reason: Optional[str] = None
    ):
        """
        Start a terminal-based conversation with the customer about cancellation.
        This simulates what would happen via SMS/email.
        """
        # Get booking details
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            print(f"❌ ERROR: Booking {booking_id} not found")
            return
        
        # Get service details
        service = self.db.query(ServiceDB).filter(ServiceDB.id == booking.service_id).first()
        service_name = service.name if service else "appointment"
        service_duration = service.duration if service else 60
        
        # Get client name from booking (Booking table already has all client info)
        client_name = booking.client_name or "Valued Client"
        
        # Format appointment details
        appt_datetime = self.format_datetime(booking.date, booking.start_time)
        
        # Print conversation header
        print("\n" + "="*80)
        print("📱 TERMINAL CUSTOMER CHAT SIMULATOR")
        print("="*80)
        print(f"\n👤 Customer: {client_name}")
        print(f"📧 Email: {booking.client_email}")
        if booking.client_phone:
            print(f"📞 Phone: {booking.client_phone}")
        print(f"\n📅 Cancelled Appointment:")
        print(f"   Service: {service_name}")
        print(f"   Date/Time: {appt_datetime}")
        print(f"   Professional: {specialist_name}")
        if cancellation_reason:
            print(f"   Reason: {cancellation_reason}")
        print("\n" + "-"*80)
        
        # Get alternative time slots
        from_date = datetime.now()
        next_available = self.get_next_available_slots(
            booking.specialist_id,
            service_duration,
            from_date,
            limit=3
        )
        
        same_time_next_week = self.get_same_time_next_week(
            booking.specialist_id,
            booking.date,
            booking.start_time,
            service_duration
        )
        
        # Start conversation - build draft message
        draft_message = f"Hey {client_name}, "
        
        if cancellation_reason:
            draft_message += f"I'm so sorry but {cancellation_reason.lower()} and I need to reschedule our {service_name} on {appt_datetime}. "
        else:
            draft_message += f"I'm so sorry but something came up and I need to reschedule our {service_name} on {appt_datetime}. "
        
        # Build list of all available times
        all_times = []
        if same_time_next_week:
            all_times.append(self.format_datetime(same_time_next_week[0], same_time_next_week[1]))
        if next_available:
            for date, start_time, end_time in next_available:
                all_times.append(self.format_datetime(date, start_time))
        
        # Build grammatically clean message
        if len(all_times) == 1:
            draft_message += f" I have {all_times[0]} open if that works for you."
        elif len(all_times) > 1:
            draft_message += " I have "
            for i, slot_time in enumerate(all_times):
                if i == 0:
                    draft_message += slot_time
                elif i == len(all_times) - 1:
                    draft_message += f", or {slot_time}"
                else:
                    draft_message += f", {slot_time}"
            draft_message += " available."
        else:
            draft_message += " Let me know what days work best for you."
        
        # Self-booking option
        specialist_id = booking.specialist_id
        booking_url = f"http://127.0.0.1:8000/consumer/book/{specialist_id}"
        draft_message += f" Or you can browse my calendar here: {booking_url}\n\n{specialist_name}"
        
        # Polish message with AI if available
        final_message = draft_message
        if self.has_ai:
            try:
                polished = self._polish_message_with_ai(draft_message, specialist_name, client_name)
                if polished:
                    final_message = polished
            except Exception:
                pass
        
        # Print the final message
        print(f"\n💬 FROM {specialist_name.upper()}:")
        print(final_message)
        
        print("\n" + "-"*80)
        print("\n💬 AWAITING CUSTOMER RESPONSE...")
        print("   (In production, this would be sent via SMS/Email and wait for reply)")
        print("\n" + "="*80 + "\n")
        
        # Log for tracking
        return {
            "booking_id": booking_id,
            "customer_name": client_name,
            "customer_email": booking.client_email,
            "customer_phone": booking.client_phone,
            "cancelled_datetime": appt_datetime,
            "service_name": service_name,
            "alternatives_offered": len(next_available) + (1 if same_time_next_week else 0),
            "booking_url": booking_url,
            "conversation_sent_at": datetime.now().isoformat()
        }
    
    def _polish_message_with_ai(self, draft_message: str, specialist_name: str, client_name: str) -> Optional[str]:
        """Use AI to polish the message for grammatical fluidity and natural flow."""
        try:
            prompt = f"""You are a professional message editor. Rewrite this cancellation message to be grammatically perfect and naturally flowing, like a real text message from {specialist_name} to {client_name}.

Requirements:
- Keep the same friendly, apologetic tone
- Maintain all the key information (reason, times, booking link)
- Make it flow naturally as one cohesive message
- Keep it concise and conversational
- Don't add extra pleasantries or formality
- Don't use emojis
- Sign off with just the name

Original message:
{draft_message}

Rewritten message:"""

            # Use new google.genai API
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                polished = response.text.strip()
            except Exception:
                return None
            
            # Basic validation - make sure it's not too different in length
            if len(polished) > len(draft_message) * 2 or len(polished) < len(draft_message) * 0.5:
                return None
                
            return polished
            
        except Exception:
            return None


def simulate_cancellation_chat(
    db: Session,
    booking_id: int,
    specialist_name: str,
    cancellation_reason: Optional[str] = None
):
    """
    Helper function to start a cancellation conversation.
    
    Usage in your endpoint:
        from .customer_chat import simulate_cancellation_chat
        
        # When cancelling a booking
        booking.status = "cancelled"
        db.commit()
        
        # Simulate customer conversation
        simulate_cancellation_chat(
            db=db,
            booking_id=booking.id,
            specialist_name=current_specialist.name,
            cancellation_reason="Unexpected scheduling conflict"
        )
    """
    chat = TerminalCustomerChat(db)
    return chat.start_cancellation_conversation(
        booking_id=booking_id,
        specialist_name=specialist_name,
        cancellation_reason=cancellation_reason
    )
