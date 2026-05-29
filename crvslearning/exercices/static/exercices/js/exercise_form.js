// Configuration globale de SweetAlert2
const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    width: '400px',
    padding: '1rem',
    customClass: {
        popup: 'custom-swal-popup',
        title: 'custom-swal-title',
        htmlContainer: 'custom-swal-html'
    },
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
    }
});

// Style personnalisé pour les alertes
const style = document.createElement('style');
style.textContent = `
    .custom-swal-popup {
        background: #1a1a1f;
        border: 1px solid #0072ce;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .custom-swal-title {
        color: #f5f5f7;
        font-size: 1.1rem;
    }
    .custom-swal-html {
        color: #d1d1d1;
    }
    .swal2-timer-progress-bar {
        background: #0072ce;
    }
`;
document.head.appendChild(style);

// Gestion des erreurs de formulaire
function showError(message) {
    Toast.fire({
        icon: 'error',
        title: message
    });
}

// Gestion des succès
function showSuccess(message) {
    Toast.fire({
        icon: 'success',
        title: message
    });
}

// Validation du formulaire
function validateForm() {
    const form = document.getElementById('exercise-form');
    const question = form.querySelector('[name="question"]').value.trim();
    const choices = form.querySelectorAll('[name$="-text"]');
    let hasCorrectAnswer = false;
    let hasEmptyChoice = false;
    
    // Vérifier si au moins une réponse est cochée comme correcte
    form.querySelectorAll('[id$="-is_correct"]').forEach(checkbox => {
        if (checkbox.checked) hasCorrectAnswer = true;
    });
    
    // Vérifier les champs vides
    choices.forEach(choice => {
        if (choice.value.trim() === '') hasEmptyChoice = true;
    });
    
    if (!question) {
        showError('Veuillez saisir une question');
        return false;
    }
    
    if (hasEmptyChoice) {
        showError('Veuillez remplir tous les champs de réponse');
        return false;
    }
    
    if (!hasCorrectAnswer) {
        showError('Veuillez sélectionner au moins une réponse correcte');
        return false;
    }
    
    return true;
}
