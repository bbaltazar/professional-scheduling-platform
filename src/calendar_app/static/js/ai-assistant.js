// AI Assistant for drafting professional messages
// Handles modal interactions and API calls to Gemini

let currentBookingId = null;

// Open the draft message modal
window.openDraftMessageModal = function(bookingId) {
    currentBookingId = bookingId;
    const modal = document.getElementById('draftMessageModal');
    
    // Reset form
    document.getElementById('messageType').value = 'reschedule';
    document.getElementById('messageReason').value = '';
    document.getElementById('messageAlternatives').value = '';
    
    // Hide generated message
    document.getElementById('generatedMessageContainer').style.display = 'none';
    document.getElementById('draftMessageError').style.display = 'none';
    document.getElementById('draftMessageLoading').style.display = 'none';
    
    // Show reason/alternatives for reschedule (default)
    updateMessageTypeFields();
    
    modal.classList.add('active');
};

// Close the draft message modal
window.closeDraftMessageModal = function() {
    const modal = document.getElementById('draftMessageModal');
    modal.classList.remove('active');
    currentBookingId = null;
};

// Update form fields based on message type
window.updateMessageTypeFields = function() {
    const messageType = document.getElementById('messageType').value;
    const reasonGroup = document.getElementById('reasonGroup');
    const alternativesGroup = document.getElementById('alternativesGroup');
    
    if (messageType === 'reschedule') {
        reasonGroup.style.display = 'block';
        alternativesGroup.style.display = 'block';
    } else {
        reasonGroup.style.display = 'none';
        alternativesGroup.style.display = 'none';
    }
};

// Add event listener for message type changes
document.addEventListener('DOMContentLoaded', function() {
    const messageTypeSelect = document.getElementById('messageType');
    if (messageTypeSelect) {
        messageTypeSelect.addEventListener('change', updateMessageTypeFields);
    }
});

// Generate AI message
window.generateMessage = async function() {
    if (!currentBookingId) {
        console.error('No booking ID set');
        return;
    }
    
    const messageType = document.getElementById('messageType').value;
    const reason = document.getElementById('messageReason').value.trim();
    const alternativesText = document.getElementById('messageAlternatives').value.trim();
    
    // Parse alternatives (one per line)
    const alternatives = alternativesText
        ? alternativesText.split('\n').map(line => line.trim()).filter(line => line.length > 0)
        : null;
    
    // Show loading state
    document.getElementById('draftMessageLoading').style.display = 'block';
    document.getElementById('generatedMessageContainer').style.display = 'none';
    document.getElementById('draftMessageError').style.display = 'none';
    document.getElementById('generateMessageBtn').disabled = true;
    
    try {
        const specialistId = parseInt(localStorage.getItem('specialistId'));
        const token = localStorage.getItem('authToken');
        
        if (!specialistId || !token) {
            throw new Error('Authentication required');
        }
        
        const requestBody = {
            booking_id: currentBookingId,
            message_type: messageType
        };
        
        if (messageType === 'reschedule') {
            if (reason) requestBody.reason = reason;
            if (alternatives && alternatives.length > 0) {
                requestBody.suggested_alternatives = alternatives;
            }
        }
        
        const response = await fetch(`/specialist/${specialistId}/draft-message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to generate message');
        }
        
        const data = await response.json();
        
        // Display the generated message
        document.getElementById('generatedSubject').textContent = data.subject;
        document.getElementById('generatedMessage').textContent = data.message;
        document.getElementById('generatedMessageContainer').style.display = 'block';
        
    } catch (error) {
        console.error('Error generating message:', error);
        const errorDiv = document.getElementById('draftMessageError');
        errorDiv.textContent = error.message || 'Failed to generate message. Please try again.';
        errorDiv.style.display = 'block';
    } finally {
        document.getElementById('draftMessageLoading').style.display = 'none';
        document.getElementById('generateMessageBtn').disabled = false;
    }
};

// Regenerate message (same function, just reset and call generate again)
window.regenerateMessage = function() {
    generateMessage();
};

// Copy message to clipboard
window.copyMessageToClipboard = function() {
    const subject = document.getElementById('generatedSubject').textContent;
    const message = document.getElementById('generatedMessage').textContent;
    
    const fullText = `Subject: ${subject}\n\n${message}`;
    
    navigator.clipboard.writeText(fullText).then(() => {
        // Show success feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        btn.style.background = 'rgba(34, 197, 94, 0.2)';
        btn.style.borderColor = 'rgba(34, 197, 94, 0.3)';
        btn.style.color = '#22c55e';
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
            btn.style.borderColor = '';
            btn.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
};

// Close modal on outside click
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('draftMessageModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeDraftMessageModal();
            }
        });
    }
});
