"""
Interactive sandbox for testing AI customer conversations.
Allows testing the full conversational flow without triggering actual cancellations.
"""
from typing import Optional, List
from datetime import datetime, timedelta, time, date as date_type
from sqlalchemy.orm import Session
from google import genai
import os

try:
    from .database import CalendarEvent, Booking, ServiceDB, Specialist
except ImportError:
    from database import CalendarEvent, Booking, ServiceDB, Specialist


class SandboxChat:
    """Interactive conversation sandbox for testing customer interactions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.conversation_history = []
        
        # Initialize Gemini with new google.genai package
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                self.model_name = 'models/gemini-2.5-flash'
                self.has_ai = True
            except Exception as e:
                print(f"Warning: Could not initialize Gemini: {e}")
                self.has_ai = False
        else:
            self.has_ai = False
    
    def format_datetime(self, date: date_type, time_obj: time) -> str:
        """Format date and time in a friendly way."""
        dt = datetime.combine(date, time_obj)
        return dt.strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")
    
    def get_available_slots(self, specialist_id: int, service_duration: int, limit: int = 3) -> List[tuple]:
        """Get next available appointment slots."""
        from_date = datetime.now().date()
        available_slots = []
        
        # Get active availability events
        events = self.db.query(CalendarEvent).filter(
            CalendarEvent.specialist_id == specialist_id,
            CalendarEvent.event_type == "availability",
            CalendarEvent.is_active == True
        ).all()
        
        for event in events:
            if not event.recurrence_rule:
                continue
                
            try:
                from dateutil.rrule import rrulestr
                rrule_obj = rrulestr(event.recurrence_rule, dtstart=from_date)
                dates = list(rrule_obj.between(from_date, from_date + timedelta(days=30), inc=True))
                
                for date in dates:
                    # Check if there's already a booking
                    existing_booking = self.db.query(Booking).filter(
                        Booking.specialist_id == specialist_id,
                        Booking.date == date,
                        Booking.start_time == event.start_time,
                        Booking.status.in_(["confirmed", "completed"])
                    ).first()
                    
                    if not existing_booking:
                        dt = datetime.combine(date, event.start_time)
                        end_dt = dt + timedelta(minutes=service_duration)
                        available_slots.append((date, event.start_time, end_dt.time()))
                    
                    if len(available_slots) >= limit:
                        break
            except Exception as e:
                continue
            
            if len(available_slots) >= limit:
                break
        
        return available_slots[:limit]
    
    def start_conversation(
        self,
        booking_id: int,
        specialist_name: str,
        cancellation_reason: Optional[str] = None
    ) -> dict:
        """
        Start a cancellation conversation and return the initial message.
        Returns conversation context for continuing the chat.
        """
        # Get booking details
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return {"error": "Booking not found"}
        
        service = self.db.query(ServiceDB).filter(ServiceDB.id == booking.service_id).first()
        service_name = service.name if service else "appointment"
        service_duration = service.duration if service else 60
        
        client_name = booking.client_name or "Valued Client"
        appt_datetime = self.format_datetime(booking.date, booking.start_time)
        
        # Get available slots
        available_slots = self.get_available_slots(booking.specialist_id, service_duration, limit=3)
        
        # Build initial message - conversational and natural
        message = f"Hey {client_name}, "
        
        if cancellation_reason:
            message += f"I'm so sorry but {cancellation_reason.lower()} and I need to reschedule our {service_name} on {appt_datetime}. "
        else:
            message += f"I'm so sorry but something came up and I need to reschedule our {service_name} on {appt_datetime}. "
        
        if available_slots:
            # Mention times naturally in the flow
            if len(available_slots) == 1:
                slot_datetime = self.format_datetime(available_slots[0][0], available_slots[0][1])
                message += f"I have {slot_datetime} open if that works for you?"
            else:
                message += "I have "
                for i, (date, start_time, end_time) in enumerate(available_slots):
                    slot_datetime = self.format_datetime(date, start_time)
                    if i == 0:
                        message += slot_datetime
                    elif i == len(available_slots) - 1:
                        message += f", or {slot_datetime}"
                    else:
                        message += f", {slot_datetime}"
                message += " available."
        else:
            message += "Let me know what days work best for you."
        
        specialist_id = booking.specialist_id
        booking_url = f"http://127.0.0.1:8000/consumer/book/{specialist_id}"
        
        # Build draft message
        if available_slots:
            if len(available_slots) == 1:
                slot_datetime = self.format_datetime(available_slots[0][0], available_slots[0][1])
                message += f" I have {slot_datetime} open if that works for you."
            else:
                message += " I have "
                for i, (date, start_time, end_time) in enumerate(available_slots):
                    slot_datetime = self.format_datetime(date, start_time)
                    if i == 0:
                        message += slot_datetime
                    elif i == len(available_slots) - 1:
                        message += f", or {slot_datetime}"
                    else:
                        message += f", {slot_datetime}"
                message += " available."
        else:
            message += " Let me know what days work best for you."
        
        message += f" Or you can browse my calendar here: {booking_url}\n\n{specialist_name}"
        
        # Use Gemini to polish the message
        if self.has_ai:
            print(f"🤖 Polishing message with AI...")
            try:
                polished = self._polish_message_with_ai(message, specialist_name, client_name)
                if polished:
                    print(f"✅ AI polish successful")
                    message = polished
                else:
                    print(f"⚠️ AI returned empty response, using draft")
            except Exception as e:
                print(f"❌ AI polishing failed: {e}")
        
        # Store conversation context
        context = {
            "booking_id": booking_id,
            "specialist_id": booking.specialist_id,
            "specialist_name": specialist_name,
            "client_name": client_name,
            "service_name": service_name,
            "service_duration": service_duration,
            "cancelled_date": booking.date.isoformat(),
            "cancelled_time": booking.start_time.isoformat(),
            "available_slots": [
                {
                    "date": slot[0].isoformat(),
                    "start_time": slot[1].isoformat(),
                    "end_time": slot[2].isoformat(),
                    "formatted": self.format_datetime(slot[0], slot[1])
                }
                for slot in available_slots
            ]
        }
        
        self.conversation_history = [
            {"role": "assistant", "content": message}
        ]
        
        return {
            "message": message,
            "context": context,
            "has_ai": self.has_ai
        }
    
    def continue_conversation(
        self,
        customer_message: str,
        context: dict
    ) -> dict:
        """
        Continue the conversation based on customer's response.
        Uses AI if available, otherwise provides simple responses.
        """
        self.conversation_history.append({"role": "user", "content": customer_message})
        
        if not self.has_ai:
            # Fallback responses without AI
            response = self._generate_fallback_response(customer_message, context)
        else:
            # Use AI to generate response
            response = self._generate_ai_response(customer_message, context)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return {
            "message": response,
            "conversation_history": self.conversation_history
        }
    
    def _generate_fallback_response(self, customer_message: str, context: dict) -> str:
        """Generate a simple response without AI."""
        msg_lower = customer_message.lower()
        
        # Check for slot selection
        for i, slot in enumerate(context["available_slots"], 1):
            if str(i) in customer_message or slot["formatted"].lower() in msg_lower:
                return (
                    f"Perfect! I'll book you for {slot['formatted']}. "
                    f"You should receive a confirmation shortly. "
                    f"Looking forward to seeing you then!\n\n- {context['specialist_name']}"
                )
        
        # Check for questions about availability
        if any(word in msg_lower for word in ["when", "available", "time", "schedule", "book"]):
            return (
                f"Great question! The times I listed are my next openings, "
                f"but feel free to check my full calendar at the link I shared. "
                f"Just let me know what works best for you!\n\n- {context['specialist_name']}"
            )
        
        # Default friendly response
        return (
            f"Thanks for getting back to me! I want to make sure we find a time that works for you. "
            f"Any of those times work, or would you like to suggest something else?\n\n- {context['specialist_name']}"
        )
    
    def _generate_ai_response(self, customer_message: str, context: dict) -> str:
        """Generate AI-powered response."""
        # Build context for AI
        available_times = "\n".join([slot["formatted"] for slot in context["available_slots"]])
        
        system_prompt = f"""You are {context['specialist_name']}, a professional service provider having a friendly, natural conversation with a customer whose appointment was cancelled.

Context:
- Customer name: {context['client_name']}
- Service: {context['service_name']}
- Cancelled appointment: {context['cancelled_date']} at {context['cancelled_time']}
- Available alternative times:
{available_times}

Your personality: Warm, professional, accommodating, conversational. Keep responses brief (2-4 sentences max). 
You want to help them reschedule quickly and make them feel valued.

If they select a time, confirm it enthusiastically and mention they'll get a confirmation.
If they ask questions, answer helpfully and keep the conversation flowing.
If they seem hesitant, be understanding and offer to work around their schedule.

Sign off with just your first name (no dash needed)."""

        try:
            # Build conversation for AI
            messages = [{"role": "system", "content": system_prompt}]
            for msg in self.conversation_history[-5:]:  # Last 5 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": customer_message})
            
            # Generate response
            chat = self.model.start_chat(history=[])
            full_prompt = system_prompt + "\n\nCustomer: " + customer_message + "\n\nYou:"
            response = chat.send_message(full_prompt)
            
            return response.text.strip()
            
        except Exception as e:
            print(f"AI generation error: {e}")
            # Fallback to simple response
            return self._generate_fallback_response(customer_message, context)
    
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

            print(f"📝 Sending to Gemini for polishing...")
            
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                polished = response.text.strip()
            except Exception as e:
                print(f"❌ Gemini failed: {e}")
                return None
            
            print(f"📝 Received polished version ({len(polished)} chars vs {len(draft_message)} original)")
            
            # Basic validation - make sure it's not too different in length
            if len(polished) > len(draft_message) * 2:
                print(f"⚠️ Polished message too long ({len(polished)} > {len(draft_message) * 2}), using draft")
                return None
            if len(polished) < len(draft_message) * 0.5:
                print(f"⚠️ Polished message too short ({len(polished)} < {len(draft_message) * 0.5}), using draft")
                return None
                
            return polished
            
        except Exception as e:
            print(f"❌ Error in _polish_message_with_ai: {e}")
            return None
