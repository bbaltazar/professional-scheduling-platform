/**
 * Authentication Module
 * Handles professional login, registration, and verification flows
 */

import { showResponse, validatePhone } from './utils.js';

// Track verification type (login or registration)
let currentVerificationType = 'login';

/**
 * Proceed with email - send verification code
 */
async function proceedWithEmail() {
    const email = document.getElementById('userEmail').value;

    if (!email) {
        showResponse('verificationResponse', 'Please enter your email address', 'error');
        return;
    }

    // Set verification type to login
    currentVerificationType = 'login';

    // Send verification code
    await sendVerificationCode(email, 'login');
}

/**
 * Show registration section
 */
function showSignUp() {
    const registrationSection = document.getElementById('registrationSection');
    if (registrationSection) {
        registrationSection.style.display = 'block';
        // Scroll to registration section
        registrationSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Register new user
 */
async function registerUser() {
    const email = document.getElementById('userEmail').value;
    const name = document.getElementById('regName').value;
    const bio = document.getElementById('regBio').value;
    const phone = document.getElementById('regPhone').value;

    if (!email) {
        showResponse('verificationResponse', 'Please enter your email address', 'error');
        return;
    }

    if (!name) {
        showResponse('verificationResponse', 'Please enter your professional name', 'error');
        return;
    }

    // Validate phone if provided
    if (phone) {
        const phoneValidation = validatePhone(phone);
        if (!phoneValidation.valid) {
            showResponse('verificationResponse', phoneValidation.error, 'error');
            return;
        }
    }

    // Set verification type to registration
    currentVerificationType = 'registration';

    // Send verification code with registration data
    await sendVerificationCode(email, 'registration', {
        name,
        bio,
        phone
    });
}

/**
 * Send verification code
 */
async function sendVerificationCode(email, verificationType, registrationData = null) {
    const requestData = {
        email: email,
        verification_type: verificationType
    };

    // Add registration data if this is a registration
    if (verificationType === 'registration' && registrationData) {
        requestData.name = registrationData.name;
        if (registrationData.bio) {
            requestData.bio = registrationData.bio;
        }
        if (registrationData.phone) {
            const phoneValidation = validatePhone(registrationData.phone);
            if (phoneValidation.valid) {
                requestData.phone = phoneValidation.normalized;
            }
        }
    }

    try {
        const response = await fetch('/verification/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (response.ok) {
            showResponse('verificationResponse', `✓ ${result.message}`, 'success');
            // Show verification code input section
            const codeSection = document.getElementById('codeSection');
            if (codeSection) {
                codeSection.style.display = 'block';
                // Focus on verification code input
                const codeInput = document.getElementById('verificationCode');
                if (codeInput) {
                    codeInput.focus();
                }
            }
        } else {
            showResponse('verificationResponse', `Failed to send code: ${result.detail}`, 'error');
        }
    } catch (error) {
        showResponse('verificationResponse', `Connection error: ${error.message}`, 'error');
    }
}

/**
 * Verify the entered code
 */
async function verifyCode() {
    const code = document.getElementById('verificationCode').value;
    const email = document.getElementById('userEmail').value;

    if (!code || code.length !== 6) {
        showResponse('verificationResponse', 'Please enter a 6-digit verification code', 'error');
        return;
    }

    const requestData = {
        code: code,
        email: email,
        verification_type: currentVerificationType
    };

    // Add registration data if this is a registration
    if (currentVerificationType === 'registration') {
        const name = document.getElementById('regName').value;
        const bio = document.getElementById('regBio').value;
        const phone = document.getElementById('regPhone').value;

        if (!name) {
            showResponse('verificationResponse', 'Please enter your name for registration', 'error');
            return;
        }

        requestData.name = name;
        if (bio) {
            requestData.bio = bio;
        }
        if (phone) {
            const phoneValidation = validatePhone(phone);
            if (phoneValidation.valid) {
                requestData.specialist_phone = phoneValidation.normalized;
            }
        }
    }

    try {
        const response = await fetch('/verification/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (response.ok && result.verified) {
            showResponse('verificationResponse', '✓ Verification successful! Redirecting to dashboard...', 'success');

            // Redirect to professional dashboard - server will set the cookie
            setTimeout(() => {
                window.location.href = '/professional';
            }, 1500);
        } else {
            showResponse('verificationResponse', `Verification failed: ${result.detail || 'Invalid code'}`, 'error');
        }
    } catch (error) {
        showResponse('verificationResponse', `Connection error: ${error.message}`, 'error');
    }
}

/**
 * Hide login section (helper for when authenticated)
 */
function hideLogin() {
    const loginSection = document.querySelector('.not-authenticated-section');
    if (loginSection) {
        loginSection.style.display = 'none';
    }
}

// Expose functions to window for onclick handlers
window.proceedWithEmail = proceedWithEmail;
window.showSignUp = showSignUp;
window.registerUser = registerUser;
window.verifyCode = verifyCode;
window.hideLogin = hideLogin;

// Export for ES6 module imports
export {
    proceedWithEmail,
    showSignUp,
    registerUser,
    verifyCode,
    hideLogin,
    sendVerificationCode
};
