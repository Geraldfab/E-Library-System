// E-Library System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(20px)';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Password visibility toggle
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(function(input) {
        const wrapper = input.parentElement;
        const toggleBtn = document.createElement('i');
        toggleBtn.className = 'fas fa-eye password-toggle';
        toggleBtn.style.cssText = 'position: absolute; right: 15px; top: 50%; transform: translateY(-50%); cursor: pointer; color: #a0aec0;';
        
        toggleBtn.addEventListener('click', function() {
            if (input.type === 'password') {
                input.type = 'text';
                toggleBtn.className = 'fas fa-eye-slash password-toggle';
            } else {
                input.type = 'password';
                toggleBtn.className = 'fas fa-eye password-toggle';
            }
        });
        
        if (wrapper.classList.contains('input-wrapper')) {
            wrapper.style.position = 'relative';
            wrapper.appendChild(toggleBtn);
        }
    });

    // Confirm password validation
    const signupForm = document.querySelector('form[action*="signup"]');
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');
            
            if (password && confirmPassword) {
                if (password.value !== confirmPassword.value) {
                    e.preventDefault();
                    alert('Passwords do not match!');
                    confirmPassword.focus();
                }
            }
        });
    }
});

// Smooth scroll to sections
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        }
    });
});

// Form validation visual feedback
const formInputs = document.querySelectorAll('input, textarea, select');
formInputs.forEach(function(input) {
    input.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
});