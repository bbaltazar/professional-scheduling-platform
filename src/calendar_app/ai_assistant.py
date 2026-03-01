"""
AI Assistant for drafting professional messages to clients.
Uses Google Gemini for generating rescheduling and communication messages.
"""
import os
from typing import Optional
import google.generativeai as genai
from datetime import datetime


class AIAssistant:
    """AI assistant for generating professional client messages."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI assistant with Gemini API."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def draft_reschedule_message(
        self,
        client_name: str,
        service_name: str,
        current_date: str,
        current_time: str,
        professional_name: str,
        reason: Optional[str] = None,
        suggested_alternatives: Optional[list[str]] = None
    ) -> dict:
        """
        Draft a professional rescheduling message.
        
        Args:
            client_name: Name of the client
            service_name: Name of the service booked
            current_date: Current appointment date (YYYY-MM-DD)
            current_time: Current appointment time (HH:MM AM/PM)
            professional_name: Name of the professional
            reason: Optional reason for rescheduling
            suggested_alternatives: Optional list of alternative time slots
            
        Returns:
            dict with 'message' (str) and 'subject' (str) keys
        """
        prompt = f"""You are a professional assistant helping to draft a polite, professional message to reschedule an appointment.

Client Information:
- Client Name: {client_name}
- Service: {service_name}
- Current Appointment: {current_date} at {current_time}
- Professional Name: {professional_name}

{f'Reason for Rescheduling: {reason}' if reason else 'No specific reason provided - keep it professional and apologetic.'}

{f'Suggested Alternative Times: {", ".join(suggested_alternatives)}' if suggested_alternatives else 'No alternative times suggested yet - ask client for their availability.'}

Generate:
1. A professional, empathetic message apologizing for the need to reschedule
2. Keep it concise (2-3 short paragraphs)
3. Use a warm but professional tone
4. If alternatives provided, present them; otherwise ask for client's availability
5. Sign off with the professional's name

Format your response as:
SUBJECT: [email subject line]
---
[message body]

Do not include any greeting like "Dear [Name]" - just start with the message content."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Parse response
            if "---" in text:
                parts = text.split("---", 1)
                subject_line = parts[0].replace("SUBJECT:", "").strip()
                message_body = parts[1].strip()
            else:
                subject_line = f"Rescheduling Your {service_name} Appointment"
                message_body = text
            
            return {
                "subject": subject_line,
                "message": message_body
            }
        except Exception as e:
            # Fallback to template if API fails
            return self._fallback_message(
                client_name, service_name, current_date, 
                current_time, professional_name, reason, suggested_alternatives
            )
    
    async def draft_confirmation_message(
        self,
        client_name: str,
        service_name: str,
        appointment_date: str,
        appointment_time: str,
        professional_name: str,
        location: Optional[str] = None
    ) -> dict:
        """
        Draft an appointment confirmation message.
        
        Returns:
            dict with 'message' (str) and 'subject' (str) keys
        """
        prompt = f"""You are a professional assistant helping to draft a friendly appointment confirmation message.

Appointment Details:
- Client Name: {client_name}
- Service: {service_name}
- Date: {appointment_date}
- Time: {appointment_time}
- Professional: {professional_name}
{f'- Location: {location}' if location else ''}

Generate a brief, friendly confirmation message (1-2 short paragraphs) that:
1. Confirms the appointment details
2. Expresses enthusiasm about seeing them
3. Mentions they can reply if they need to reschedule
4. Sign off with the professional's name

Format your response as:
SUBJECT: [email subject line]
---
[message body]

Do not include greeting - just the message content."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            if "---" in text:
                parts = text.split("---", 1)
                subject_line = parts[0].replace("SUBJECT:", "").strip()
                message_body = parts[1].strip()
            else:
                subject_line = f"Appointment Confirmed - {service_name}"
                message_body = text
            
            return {
                "subject": subject_line,
                "message": message_body
            }
        except Exception as e:
            return {
                "subject": f"Appointment Confirmed - {service_name}",
                "message": f"Your {service_name} appointment is confirmed for {appointment_date} at {appointment_time}. Looking forward to seeing you!\n\n- {professional_name}"
            }
    
    def _fallback_message(
        self,
        client_name: str,
        service_name: str,
        current_date: str,
        current_time: str,
        professional_name: str,
        reason: Optional[str],
        suggested_alternatives: Optional[list[str]]
    ) -> dict:
        """Fallback template if AI generation fails."""
        message = f"I need to reschedule your {service_name} appointment currently scheduled for {current_date} at {current_time}. "
        
        if reason:
            message += f"{reason} "
        else:
            message += "I apologize for any inconvenience this may cause. "
        
        if suggested_alternatives:
            message += f"\n\nWould any of these alternative times work for you?\n"
            for alt in suggested_alternatives:
                message += f"• {alt}\n"
            message += "\nPlease let me know which works best."
        else:
            message += "\n\nCould you please let me know your availability so we can find a new time that works for you?"
        
        message += f"\n\nThank you for your understanding.\n\n- {professional_name}"
        
        return {
            "subject": f"Need to Reschedule - {service_name} Appointment",
            "message": message
        }


# Global instance
_assistant: Optional[AIAssistant] = None


def get_assistant() -> AIAssistant:
    """Get or create the global AI assistant instance."""
    global _assistant
    if _assistant is None:
        _assistant = AIAssistant()
    return _assistant
