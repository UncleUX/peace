console.log('Fichier course_form.js chargé avec succès!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM entièrement chargé');
    
    // Éléments du DOM
    const addCategoryBtn = document.getElementById('addCategoryBtn');
    const categoryForm = document.getElementById('addCategoryForm');
    const categorySelect = document.getElementById('id_category');
    const newCategoryName = document.getElementById('id_new_category_name');
    const newCategoryDescription = document.getElementById('id_new_category_description');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Initialisation de la modale Bootstrap
    const modalElement = document.getElementById('addCategoryModal');
    let categoryModal = null;
    
    if (modalElement) {
        categoryModal = new bootstrap.Modal(modalElement);
        console.log('Modale Bootstrap initialisée');
        
        // Gestionnaire d'événement pour l'ouverture de la modale
        modalElement.addEventListener('show.bs.modal', function () {
            // S'assurer que la modale est accessible lors de l'ouverture
            modalElement.removeAttribute('aria-hidden');
            modalElement.setAttribute('aria-modal', 'true');
        });

        // Gestionnaire d'événement pour la fermeture de la modale
        modalElement.addEventListener('hidden.bs.modal', function () {
            // Réinitialiser le formulaire
            if (categoryForm) categoryForm.reset();
            // S'assurer que la modale est correctement masquée
            modalElement.setAttribute('aria-hidden', 'true');
            modalElement.removeAttribute('aria-modal');
        });
    } else {
        console.error('Élément modal non trouvé');
    }
    
    // Gestionnaire de clic pour le bouton d'ajout de catégorie
    if (addCategoryBtn && categoryModal) {
        addCategoryBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Ouverture de la modale...');
            // Utiliser l'API Bootstrap pour afficher la modale
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.show();
                // S'assurer que l'élément modal est accessible
                modalElement.removeAttribute('aria-hidden');
                modalElement.setAttribute('aria-modal', 'true');
            }
        });
    }

    // Gestionnaire de soumission du formulaire de catégorie
    if (categoryForm) {
        categoryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Soumission du formulaire de catégorie');
            
            // Récupérer le bouton de soumission et désactiver pendant la requête
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Envoi en cours...';
            }
            
            // Cacher les messages d'erreur précédents
            const errorDiv = document.getElementById('categoryError');
            if (errorDiv) {
                errorDiv.classList.add('d-none');
            }
            
            // Créer un objet FormData à partir du formulaire
            const formData = new FormData(categoryForm);
            
            console.log('Données du formulaire:', Object.fromEntries(formData.entries()));
            
            // Envoyer la requête et rafraîchir la page immédiatement
            fetch(categoryForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken') || ''
                },
                body: formData
            })
            .then(() => {
                // Fermer la modale si elle est ouverte
                if (categoryModal) {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    }
                }
                // Rafraîchir la page
                window.location.reload();
            })
            .catch(error => {
                console.error('Erreur lors de la création de la catégorie:', error);
                // Réactiver le bouton en cas d'erreur
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
                // Afficher un message d'erreur simple
                alert('Erreur lors de la création de la catégorie. Veuillez réessayer.');
            });
        });
    }

    // Fonction utilitaire pour afficher un message d'erreur
    function showAlert(type, message) {
        console.error(`${type}: ${message}`);
        alert(message);
        return { show: function() {} }; // Pour maintenir la compatibilité avec le code existant
    }
});