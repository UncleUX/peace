/**
 * Version AGRESSIVE - Force le rafraîchissement DOM immédiat
 */

console.log('🚀 lesson_progress_aggressive.js chargé');

// Fonction AGRESSIVE pour mettre à jour TOUT ce qui concerne la leçon
function forceUpdateAllLessonElements(lessonId) {
    console.log('🔥 MISE À JOUR AGRESSIVE de tous les éléments leçon', lessonId);
    
    // 1. Chercher TOUS les éléments possibles avec data-lesson-id
    const allElements = document.querySelectorAll('[data-lesson-id]');
    console.log(`📋 Total éléments avec data-lesson-id: ${allElements.length}`);
    
    let updatedCount = 0;
    
    allElements.forEach((element, index) => {
        if (element.dataset.lessonId === lessonId.toString()) {
            console.log(`🎯 Élément ${index}: ${element.tagName} - classes: ${element.className}`);
            
            // Mettre à jour les icônes play circle
            const playIcons = element.querySelectorAll('.bi-play-circle');
            playIcons.forEach(icon => {
                icon.classList.remove('bi-play-circle', 'text-primary');
                icon.classList.add('bi-check-circle-fill', 'text-success');
                console.log('✅ ICÔNE PLAY → CHECK');
                updatedCount++;
            });
            
            // Mettre à jour les statuts
            const statusElements = element.querySelectorAll('.lesson-status, .lesson-badge, .current-badge');
            statusElements.forEach(status => {
                status.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
                status.className = 'lesson-status badge badge-success';
                console.log('✅ STATUT MIS À JOUR');
                updatedCount++;
            });
            
            // Mettre à jour les classes
            element.classList.add('completed');
            element.classList.remove('current');
            console.log('✅ CLASSES MODIFIÉES');
            updatedCount++;
            
            // Si c'est un formulaire, le remplacer
            if (element.tagName === 'FORM') {
                const statusDiv = document.createElement('div');
                statusDiv.className = 'text-success fw-bold';
                statusDiv.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
                element.parentNode.replaceChild(statusDiv, element);
                console.log('✅ FORMULAIRE REMPLACÉ');
                updatedCount++;
            }
            
            // Si c'est un bouton, le désactiver
            if (element.tagName === 'BUTTON') {
                element.disabled = true;
                element.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
                element.className = 'btn btn-success btn-sm disabled';
                console.log('✅ BOUTON DÉSACTIVÉ');
                updatedCount++;
            }
        }
    });
    
    console.log(`🎉 ${updatedCount} éléments mis à jour avec succès !`);
    
    // 2. Forcer le re-rendu des éléments visibles
    setTimeout(() => {
        // Forcer le reflow
        document.body.offsetHeight;
        
        // Ajouter une animation de flash pour montrer la mise à jour
        const completedElements = document.querySelectorAll('.completed');
        completedElements.forEach(el => {
            el.style.transition = 'background-color 0.3s';
            el.style.backgroundColor = '#d4edda';
            setTimeout(() => {
                el.style.backgroundColor = '';
            }, 300);
        });
        
        console.log('✨ Animation de mise à jour appliquée');
    }, 100);
    
    return updatedCount;
}

// Test AGRESSIF immédiat
function createAggressiveTestButton() {
    console.log('🔥 Création bouton test AGRESSIF');
    
    const testBtn = document.createElement('button');
    testBtn.id = 'test-aggressive-update';
    testBtn.className = 'btn btn-warning btn-sm mt-2';
    testBtn.innerHTML = '🔥 TEST AGRESSIF';
    testBtn.style.position = 'fixed';
    testBtn.style.top = '60px';
    testBtn.style.right = '10px';
    testBtn.style.zIndex = '9999';
    
    testBtn.addEventListener('click', function() {
        console.log('🔥 CLICK TEST AGRESSIF');
        
        const lessonId = document.body.dataset.lessonId;
        if (lessonId) {
            const updated = forceUpdateAllLessonElements(lessonId);
            showNotification(`✅ ${updated} éléments mis à jour !`, 'success');
        }
    });
    
    document.body.appendChild(testBtn);
    console.log('✅ Bouton test AGRESSIF ajouté');
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
    console.log('🚀 DOM chargé - Initialisation test AGRESSIF');
    
    const lessonId = document.body.dataset.lessonId;
    
    if (lessonId) {
        createAggressiveTestButton();
    } else {
        console.log('❌ Pas de lessonId, pas de bouton test AGRESSIF');
    }
});

console.log('✅ lesson_progress_aggressive.js prêt');
