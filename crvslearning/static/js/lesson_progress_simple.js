/**
 * Version simplifiée pour diagnostic - Suivi de progression des leçons
 */

console.log('🚀 lesson_progress_simple.js chargé');

// Test simple : bouton de test manuel
function createTestButton() {
    console.log('🎯 Création bouton de test');
    
    // Créer un bouton de test
    const testBtn = document.createElement('button');
    testBtn.id = 'test-mark-completed';
    testBtn.className = 'btn btn-danger btn-sm mt-2';
    testBtn.innerHTML = '🔥 TEST MARQUER TERMINÉ';
    testBtn.style.position = 'fixed';
    testBtn.style.top = '10px';
    testBtn.style.right = '10px';
    testBtn.style.zIndex = '9999';
    
    testBtn.addEventListener('click', function() {
        console.log('🔥 CLICK SUR BOUTON DE TEST');
        markLessonCompletedTest();
    });
    
    document.body.appendChild(testBtn);
    console.log('✅ Bouton de test ajouté');
}

// Fonction de test pour marquer une leçon comme terminée
function markLessonCompletedTest() {
    console.log('🎯 DÉBUT TEST MARQUAGE LEÇON');
    
    // Récupérer l'ID de la leçon depuis le body
    const lessonId = document.body.dataset.lessonId;
    console.log('📋 lessonId:', lessonId);
    
    if (!lessonId) {
        console.log('❌ Pas de lessonId trouvé');
        return;
    }
    
    // Mettre à jour la playlist immédiatement
    updatePlaylistTest(lessonId);
    
    // Envoyer la requête au serveur
    fetch(`/courses/progress/lesson/${lessonId}/mark-completed/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken || getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('📝 Réponse du serveur:', data);
        if (data.success) {
            console.log('✅ Leçon marquée comme terminée avec succès !');
            showNotification('Leçon terminée (TEST) !', 'success');
        }
    })
    .catch(error => {
        console.error('❌ Erreur:', error);
    });
}

// Fonction test pour mettre à jour la playlist
function updatePlaylistTest(lessonId) {
    console.log('🔄 MISE À JOUR PLAYLIST TEST - leçon', lessonId);
    
    // Chercher spécifiquement l'item dans la playlist (pas le body)
    const playlistItem = document.querySelector(`.playlist-item[data-lesson-id="${lessonId}"]`);
    console.log('🔍 Item playlist trouvé:', playlistItem);
    
    if (playlistItem) {
        console.log('✅ MISE À JOUR IMMÉDIATE');
        
        // Changer l'icône
        const icon = playlistItem.querySelector('.bi-play-circle');
        if (icon) {
            icon.classList.remove('bi-play-circle', 'text-primary');
            icon.classList.add('bi-check-circle-fill', 'text-success');
            console.log('✅ ICÔNE CHANGÉE EN VERTE !');
        }
        
        // Changer le statut
        const status = playlistItem.querySelector('.lesson-status, .lesson-badge');
        if (status) {
            status.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
            status.className = 'lesson-status badge badge-success';
            console.log('✅ STATUT CHANGÉ !');
        }
        
        // Ajouter classe completed
        playlistItem.classList.add('completed');
        playlistItem.classList.remove('current');
        console.log('✅ CLASSES MODIFIÉES !');
        
        console.log('🎉 PLAYLIST MISE À JOUR AVEC SUCCÈS !');
        
        // Cacher le bouton de test APRÈS succès
        const testBtn = document.getElementById('test-mark-completed');
        if (testBtn) {
            testBtn.style.display = 'none';
            console.log('✅ Bouton de test caché après succès');
        }
        
    } else {
        console.log('❌ Item playlist non trouvé');
        console.log('🔍 Recherche de tous les .playlist-item[data-lesson-id]...');
        const allItems = document.querySelectorAll('.playlist-item[data-lesson-id]');
        console.log('📋 Items playlist trouvés:', allItems.length);
        allItems.forEach((item, index) => {
            console.log(`Item ${index}: data-lesson-id="${item.dataset.lessonId}"`, item);
        });
        
        // Alternative : chercher tous les data-lesson-id sauf le body
        console.log('🔍 Recherche de tous les data-lesson-id (sauf body)...');
        const allElements = document.querySelectorAll('[data-lesson-id]');
        console.log('📋 Tous les éléments trouvés:', allElements.length);
        allElements.forEach((item, index) => {
            if (item.tagName !== 'BODY') {
                console.log(`Élément ${index}: ${item.tagName} - data-lesson-id="${item.dataset.lessonId}"`);
            }
        });
    }
}

// Fonction pour getCookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Fonction pour afficher une notification
function showNotification(message, type = 'info') {
    console.log('📢 Notification:', message, type);
    
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: type === 'success' ? 'success' : 'info',
            title: message,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    } else {
        alert(message);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM chargé - Initialisation test');
    
    // Vérifier les éléments
    const lessonId = document.body.dataset.lessonId;
    const courseId = document.body.dataset.courseId;
    const videoElement = document.getElementById('lesson-video');
    
    console.log('📋 Éléments trouvés:');
    console.log('- lessonId:', lessonId);
    console.log('- courseId:', courseId);
    console.log('- videoElement:', videoElement);
    console.log('- csrfToken:', window.csrfToken);
    
    // Créer le bouton de test
    if (lessonId) {
        createTestButton();
    } else {
        console.log('❌ Pas de lessonId, pas de bouton de test');
    }
});

console.log('✅ lesson_progress_simple.js prêt');
