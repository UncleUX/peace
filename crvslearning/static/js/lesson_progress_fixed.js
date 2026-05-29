/**
 * Version corrigée - Suivi de progression des leçons
 */

console.log('🚀 lesson_progress_fixed.js chargé');

class LessonProgressTracker {
    constructor(lessonId, videoElement) {
        console.log('🎯 CONSTRUCTEUR LessonProgressTracker');
        console.log('- lessonId:', lessonId);
        console.log('- videoElement:', videoElement);
        
        this.lessonId = lessonId;
        this.video = videoElement;
        this.autoCompleted = false;
        this.manuallyMarked = false;
        this.lastPosition = 0;
        this.watchTime = 0;
        this.startTime = Date.now();
        
        console.log('📋 Propriétés initialisées');
        
        this.init();
    }
    
    init() {
        console.log('🔧 Initialisation du suivi');
        
        // Vérifier la progression existante
        this.checkExistingProgress();
        
        // Ajouter les écouteurs d'événements
        this.setupVideoListeners();
        
        // Démarrer le suivi
        this.startTracking();
    }
    
    async checkExistingProgress() {
        try {
            const response = await fetch(`/courses/progress/lesson/${this.lessonId}/progress/`);
            const data = await response.json();
            
            if (data.success) {
                this.autoCompleted = data.auto_completed;
                this.manuallyMarked = data.manually_marked;
                this.lastPosition = data.watch_percentage * this.video.duration / 100;
                
                // Restaurer la position de la vidéo
                if (this.lastPosition > 0 && this.lastPosition < this.video.duration - 10) {
                    this.video.currentTime = this.lastPosition;
                }
                
                // Mettre à jour l'interface
                this.updateUI(data);
                
                // Si déjà complété, afficher le bouton "Marquer terminé" si nécessaire
                if (this.autoCompleted && !this.manuallyMarked) {
                    // PLUS NÉCESSAIRE - terminaison automatique
                    console.log('🚫 Auto-complété mais pas encore terminé manuellement - terminaison automatique');
                    await this.markAsTerminatedImmediately();
                }
            }
        } catch (error) {
            console.error('Erreur lors de la vérification de la progression:', error);
        }
    }
    
    setupVideoListeners() {
        console.log('🎧 Configuration des écouteurs vidéo');
        
        // Suivi du temps
        this.video.addEventListener('timeupdate', () => {
            this.onTimeUpdate();
        });
        
        // Sauvegarde de la position
        this.video.addEventListener('pause', () => {
            this.saveProgress();
        });
        
        // Fin de la vidéo
        this.video.addEventListener('ended', () => {
            this.onVideoEnded();
        });
        
        // Avant de quitter la page
        window.addEventListener('beforeunload', () => {
            this.saveProgress();
        });
    }
    
    onTimeUpdate() {
        const currentTime = this.video.currentTime;
        const duration = this.video.duration;
        
        if (duration > 0) {
            const watchPercentage = (currentTime / duration) * 100;
            
            // Mettre à jour la barre de progression
            this.updateProgressBar(watchPercentage);
            
            // 🎯 ÉMETTRE L'ÉVÉNEMENT DE PROGRESSION EN TEMPS RÉEL
            window.dispatchEvent(new CustomEvent('lessonProgressUpdated', {
                detail: {
                    watch_percentage: watchPercentage,
                    auto_completed: this.autoCompleted,
                    manually_marked: this.manuallyMarked,
                    fully_completed: this.manuallyMarked && this.autoCompleted
                }
            }));
            
            // Vérifier si on atteint 80%
            if (watchPercentage >= 80 && !this.autoCompleted) {
                this.markAutoCompleted();
            }
        }
    }
    
    onVideoEnded() {
        // Marquer comme 100% visionné
        this.saveProgress(100);
        
        // Si pas encore auto-complété, le faire maintenant
        if (!this.autoCompleted) {
            this.markAutoCompleted();
        }
    }
    
    async markAutoCompleted() {
        if (this.autoCompleted) return;
        
        console.log('🤖 Marquage automatique à 80% - TERMINAISON IMMÉDIATE');
        
        try {
            // 1. Marquer comme auto-complété
            const response = await fetch(`/courses/progress/lesson/${this.lessonId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    percentage: 80,
                    watch_time: Math.floor((Date.now() - this.startTime) / 1000),
                    last_position: this.video.currentTime
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.auto_completed) {
                this.autoCompleted = true;
                this.showNotification('Leçon complétée automatiquement !', 'success');
                
                console.log('✅ Auto-complétion réussie');
                
                // 🎯 ÉMETTRE L'ÉVÉNEMENT DE COMPLÉTION AUTOMATIQUE
                window.dispatchEvent(new CustomEvent('lessonAutoCompleted', {
                    detail: {
                        watch_percentage: 80,
                        auto_completed: true,
                        manually_marked: false,
                        fully_completed: false
                    }
                }));
                
                // 2. MARQUER IMMÉDIATEMENT COMME TERMINÉ (sans cliquer)
                await this.markAsTerminatedImmediately();
            }
        } catch (error) {
            console.error('Erreur lors du marquage auto:', error);
        }
    }
    
    async markAsTerminatedImmediately() {
        console.log('🎯 TERMINAISON IMMÉDIATE AVEC AJAX - SANS CLIQUER');
        
        try {
            console.log('📡 ENVOI REQUÊTE AJAX...');
            
            const response = await fetch(`/courses/progress/lesson/${this.lessonId}/mark-completed/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            console.log('📡 RÉPONSE AJAX REÇUE:', response.status);
            
            const data = await response.json();
            console.log('📝 DONNÉES AJAX:', data);
            
            if (data.success) {
                console.log('✅ AJAX SUCCÈS - MISE À JOUR DOM');
                
                this.manuallyMarked = true;
                
                // Mettre à jour l'interface locale
                this.updateUI({
                    fully_completed: true,
                    completion_percentage: 100
                });
                
                console.log('🔄 APPEL DE updatePlaylistImmediately...');
                
                // Utiliser la mise à jour AGGRESSIVE du DOM
                this.updatePlaylistImmediately();
                
                console.log('✅ AJAX + DOM TERMINÉ AVEC SUCCÈS !');
                this.showNotification('Leçon terminée automatiquement !', 'success');
            } else {
                console.log('❌ AJAX ÉCHEC:', data);
            }
        } catch (error) {
            console.error('❌ ERREUR AJAX:', error);
        }
    }
    
    async markManuallyCompleted() {
        if (this.manuallyMarked) return;
        
        console.log('🔥 Début marquage manuel leçon', this.lessonId);
        
        try {
            const response = await fetch(`/courses/progress/lesson/${this.lessonId}/mark-completed/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            console.log('📝 Réponse marquage manuel:', data);
            
            if (data.success) {
                this.manuallyMarked = true;
                this.hideMarkCompletedButton();
                this.showNotification('Leçon marquée comme terminée !', 'success');
                
                // Mettre à jour l'interface locale
                this.updateUI({
                    fully_completed: true,
                    completion_percentage: 100
                });
                
                console.log('🔄 MISE À JOUR IMMÉDIATE DE LA PLAYLIST...');
                
                // Mettre à jour DIRECTEMENT la playlist sans attendre
                this.updatePlaylistImmediately();
                
                console.log('✅ Playlist mise à jour immédiatement');
            }
        } catch (error) {
            console.error('❌ Erreur lors du marquage manuel:', error);
        }
    }
    
    updatePlaylistImmediately() {
        // Mettre à jour immédiatement la playlist pour cette leçon
        const lessonId = this.lessonId;
        
        console.log('🎯 MISE À JOUR INSTANTANÉE SANS REFRESH - leçon', lessonId);
        
        // DIAGNOSTIC COMPLET DU DOM
        console.log('🔍 DIAGNOSTIC DOM COMPLET');
        
        // 1. Lister tous les éléments avec data-lesson-id
        const allElements = document.querySelectorAll('[data-lesson-id]');
        console.log(`📋 Total éléments avec data-lesson-id: ${allElements.length}`);
        
        allElements.forEach((element, index) => {
            if (element.tagName !== 'BODY') {
                console.log(`Élément ${index}: ${element.tagName} - data-lesson-id="${element.dataset.lessonId}" - classes: "${element.className}"`);
                
                if (element.dataset.lessonId === lessonId.toString()) {
                    console.log(`🎯 CIBLE TROUVÉE: ${element.tagName}`);
                    
                    // Tenter de mettre à jour cet élément
                    this.updateSingleElement(element);
                }
            }
        });
        
        // 2. Diagnostic spécifique pour la playlist
        console.log('🔍 DIAGNOSTIC PLAYLIST SPÉCIFIQUE');
        
        // Essayer plusieurs sélecteurs possibles pour la playlist
        const possibleSelectors = [
            `.playlist-item[data-lesson-id="${lessonId}"]`,
            `[data-lesson-id="${lessonId}"]`,
            `.simple-playlist [data-lesson-id="${lessonId}"]`,
            `#simple-playlist [data-lesson-id="${lessonId}"]`
        ];
        
        let playlistItem = null;
        let selectorUsed = '';
        
        for (const selector of possibleSelectors) {
            playlistItem = document.querySelector(selector);
            if (playlistItem) {
                selectorUsed = selector;
                console.log(`✅ Élément playlist trouvé avec sélecteur: ${selector}`);
                break;
            }
        }
        
        console.log('📋 Item playlist trouvé:', playlistItem);
        console.log('📋 Sélecteur utilisé:', selectorUsed);
        
        if (playlistItem) {
            console.log('✅ MISE À JOUR PLAYITEM DIRECT');
            this.updateSingleElement(playlistItem);
        } else {
            console.log('❌ AucUN élément playlist trouvé avec tous les sélecteurs');
        }
        
        // 3. Diagnostic des formulaires
        console.log('🔍 DIAGNOSTIC FORMULAIRES');
        const forms = document.querySelectorAll(`form[data-lesson-id="${lessonId}"]`);
        console.log(`📋 Formulaires trouvés: ${forms.length}`);
        
        forms.forEach((form, index) => {
            console.log(`Formulaire ${index}: ${form.tagName} - classes: "${form.className}"`);
            this.updateSingleElement(form);
        });
        
        // 4. Forcer le reflow DOM
        this.forceDOMReflow();
    }
    
    updateSingleElement(element) {
        console.log(`🔄 MISE À JOUR ÉLÉMENT: ${element.tagName}`);
        
        // Mettre à jour les icônes play circle
        const playIcons = element.querySelectorAll('.bi-play-circle');
        console.log(`📋 Icônes play trouvées: ${playIcons.length}`);
        
        playIcons.forEach((icon, index) => {
            icon.classList.remove('bi-play-circle', 'text-primary');
            icon.classList.add('bi-check-circle-fill', 'text-success');
            console.log(`✅ Icône ${index} mise à jour`);
        });
        
        // Mettre à jour les statuts
        const statusElements = element.querySelectorAll('.lesson-status, .lesson-badge, .current-badge');
        console.log(`📋 Éléments de statut trouvés: ${statusElements.length}`);
        
        statusElements.forEach((status, index) => {
            status.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
            status.className = 'lesson-status badge badge-success';
            console.log(`✅ Statut ${index} mis à jour`);
        });
        
        // Mettre à jour les classes
        element.classList.add('completed');
        element.classList.remove('current');
        console.log('✅ Classes mises à jour');
        
        // Si c'est un formulaire, le remplacer
        if (element.tagName === 'FORM') {
            const statusDiv = document.createElement('div');
            statusDiv.className = 'text-success fw-bold';
            statusDiv.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
            element.parentNode.replaceChild(statusDiv, element);
            console.log('✅ Formulaire remplacé');
        }
        
        // Si c'est un bouton, le désactiver
        if (element.tagName === 'BUTTON') {
            element.disabled = true;
            element.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
            element.className = 'btn btn-success btn-sm disabled';
            console.log('✅ Bouton désactivé');
        }
    }
    
    forceDOMReflow() {
        console.log('🔄 FORÇAGE REFLOW DOM SANS REFRESH');
        
        // Forcer le reflow pour que les changements soient visibles
        document.body.offsetHeight;
        
        // Ajouter une animation subtile pour montrer la mise à jour
        const completedElements = document.querySelectorAll('.completed');
        completedElements.forEach(el => {
            el.style.transition = 'background-color 0.5s ease';
            el.style.backgroundColor = '#d4edda';
            
            setTimeout(() => {
                el.style.backgroundColor = '';
            }, 500);
        });
        
        console.log('✨ Animation de mise à jour appliquée - PAS DE REFRESH');
    }
    
    updateGlobalTerminatedButtons(lessonId) {
        console.log('🔄 MISE À JOUR DES BOUTONS "LEÇON TERMINÉE"');
        
        // Chercher tous les formulaires de marquage pour cette leçon
        const markForms = document.querySelectorAll(`form[data-lesson-id="${lessonId}"]`);
        console.log(`📋 Formulaires trouvés pour leçon ${lessonId}:`, markForms.length);
        
        markForms.forEach(form => {
            console.log('🔄 Transformation du formulaire en statut "Leçon terminée"');
            
            // Créer un élément de remplacement
            const statusDiv = document.createElement('div');
            statusDiv.className = 'text-success fw-bold';
            statusDiv.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
            
            // Remplacer le formulaire
            form.parentNode.replaceChild(statusDiv, form);
            console.log('✅ Formulaire remplacé par "Leçon terminée"');
        });
        
        // Chercher les boutons avec data-lesson-id
        const markButtons = document.querySelectorAll(`[data-lesson-id="${lessonId}"] .mark-completed-btn, button[data-lesson-id="${lessonId}"]`);
        console.log(`📋 Boutons trouvés pour leçon ${lessonId}:`, markButtons.length);
        
        markButtons.forEach(button => {
            button.disabled = true;
            button.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
            button.className = 'btn btn-success btn-sm disabled';
            console.log('✅ Bouton transformé en "Leçon terminée"');
        });
    }
    
    async saveProgress(percentage = null) {
        if (this.autoCompleted && this.manuallyMarked) return; // Déjà complété
        
        const currentPercentage = percentage !== null ? percentage : 
            (this.video.currentTime / this.video.duration) * 100;
        
        try {
            await fetch(`/courses/progress/lesson/${this.lessonId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    percentage: currentPercentage,
                    watch_time: Math.floor((Date.now() - this.startTime) / 1000),
                    last_position: this.video.currentTime
                })
            });
        } catch (error) {
            console.error('Erreur lors de la sauvegarde:', error);
        }
    }
    
    updateProgressBar(percentage) {
        const progressBar = document.getElementById('lesson-progress-bar');
        const progressText = document.getElementById('lesson-progress-text');
        
        if (progressBar) {
            progressBar.style.width = `${Math.min(percentage, 100)}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(percentage)}%`;
        }
    }
    
    updateUI(data) {
        this.updateProgressBar(data.watch_percentage || 0);
        
        // Mettre à jour le statut
        const statusElement = document.getElementById('lesson-status');
        if (statusElement) {
            if (data.fully_completed) {
                statusElement.innerHTML = '<span class="badge badge-success">Terminé</span>';
            } else if (data.auto_completed) {
                statusElement.innerHTML = '<span class="badge badge-warning">À valider</span>';
            } else {
                statusElement.innerHTML = '<span class="badge badge-info">En cours</span>';
            }
        }
    }
    
    showMarkCompletedButton() {
        // PLUS NÉCESSAIRE - la leçon se termine automatiquement à 80%
        console.log('🚫 Bouton "Marquer terminé" plus nécessaire - terminaison automatique');
        return;
    }
    
    hideMarkCompletedButton() {
        const button = document.getElementById('mark-lesson-completed-btn');
        if (button) {
            button.style.display = 'none';
        }
    }
    
    showNotification(message, type = 'info') {
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
            console.log(message);
        }
    }
    
    startTracking() {
        console.log('⏱️ Démarrage du suivi');
        
        // Démarrer le suivi toutes les 30 secondes
        this.trackingInterval = setInterval(() => {
            if (!this.video.paused) {
                this.saveProgress();
            }
        }, 30000);
    }
    
    stopTracking() {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
        }
    }
    
    getCSRFToken() {
        // Priorité à la variable globale depuis le template Django
        if (typeof window.csrfToken !== 'undefined' && window.csrfToken) {
            return window.csrfToken;
        }
        
        // Alternative: depuis le cookie
        return this.getCookie('csrftoken');
    }
    
    getCookie(name) {
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
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM chargé - Initialisation lesson_progress_fixed.js');
    
    const videoElement = document.getElementById('lesson-video');
    const lessonId = document.body.dataset.lessonId;
    const courseId = document.body.dataset.courseId;
    
    console.log('📋 Éléments trouvés:');
    console.log('- videoElement:', videoElement);
    console.log('- lessonId:', lessonId);
    console.log('- courseId:', courseId);
    console.log('- csrfToken:', window.csrfToken);
    
    if (videoElement && lessonId) {
        console.log('✅ Création du LessonProgressTracker');
        window.lessonTracker = new LessonProgressTracker(lessonId, videoElement);
    } else {
        console.log('❌ Éléments manquants pour l\'initialisation');
    }
});

console.log('✅ lesson_progress_fixed.js prêt');
