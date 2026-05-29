/**
 * Script de suivi de progression des leçons
 * Gère le suivi vidéo, la progression automatique et le marquage manuel
 */

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
        console.log('- this.lessonId:', this.lessonId);
        console.log('- this.video:', this.video);
        
        this.init();
    }
    
    init() {
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
                if (data.auto_completed && !data.manually_marked) {
                    this.showMarkCompletedButton();
                }
            }
        } catch (error) {
            console.error('Erreur lors de la vérification de la progression:', error);
        }
    }
    
    setupVideoListeners() {
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
        
        try {
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
                this.showMarkCompletedButton();
                
                // Mettre à jour la progression du cours
                await this.updateCourseProgress();
                
                // Si c'est aussi marqué manuellement, mettre à jour l'état global
                if (this.manuallyMarked) {
                    await this.updateGlobalState();
                }
            }
        } catch (error) {
            console.error('Erreur lors du marquage auto:', error);
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
        
        console.log('🎯 MISE À JOUR INSTANTANÉE playlist leçon', lessonId);
        
        // 1. Mettre à jour l'item dans la playlist
        const playlistItem = document.querySelector(`[data-lesson-id="${lessonId}"]`);
        if (playlistItem) {
            console.log('✅ Item playlist trouvé, mise à jour immédiate...');
            
            // Ajouter classe completed
            playlistItem.classList.add('completed');
            playlistItem.classList.remove('current');
            
            // Mettre à jour l'icône PRINCIPALE (play circle → check circle)
            const mainIcon = playlistItem.querySelector('.bi-play-circle');
            if (mainIcon) {
                mainIcon.classList.remove('bi-play-circle', 'text-primary');
                mainIcon.classList.add('bi-check-circle-fill', 'text-success');
                console.log('✅ ICÔNE PRINCIPALE mise à jour : bi-check-circle-fill text-success');
            }
            
            // Mettre à jour l'icône de statut
            const statusIcon = playlistItem.querySelector('.lesson-status .bi-check-circle-fill, .lesson-status .current-badge');
            if (statusIcon) {
                statusIcon.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
                console.log('✅ ICÔNE DE STATUT mise à jour');
            }
            
            // Mettre à jour le badge de statut
            const statusElement = playlistItem.querySelector('.lesson-status, .lesson-badge');
            if (statusElement) {
                statusElement.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
                statusElement.className = 'lesson-status badge badge-success';
                console.log('✅ BADGE DE STATUT mis à jour');
            }
            
            // Mettre à jour le numéro
            const numberElement = playlistItem.querySelector('.playlist-item-number');
            if (numberElement) {
                numberElement.classList.add('text-success');
                console.log('✅ NUMÉRO mis à jour');
            }
            
            console.log('🎉 PLAYLIST MISE À JOUR AVEC SUCCÈS - ICÔNE VERTE VISIBLE !');
            
        } else {
            console.log('❌ Item playlist non trouvé pour leçon', lessonId);
            console.log('🔍 Recherche de tous les items avec data-lesson-id...');
            const allItems = document.querySelectorAll('[data-lesson-id]');
            console.log('📋 Items trouvés:', allItems.length);
            allItems.forEach((item, index) => {
                console.log(`Item ${index}: data-lesson-id="${item.dataset.lessonId}"`);
            });
        }
        
        // 2. Mettre à jour les autres boutons "Marquer terminé" globaux
        const globalButtons = document.querySelectorAll(`[data-lesson-id="${lessonId}"] .mark-completed-btn, #mark-lesson-${lessonId}`);
        globalButtons.forEach(button => {
            if (button.tagName === 'BUTTON') {
                button.disabled = true;
                button.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
                button.className = 'btn btn-success btn-sm disabled';
            }
        });
        
        console.log('✅ MISE À JOUR TERMINÉE - LEÇON TERMINÉE AFFICHÉE !');
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
        let button = document.getElementById('mark-lesson-completed-btn');
        
        if (!button) {
            button = document.createElement('button');
            button.id = 'mark-lesson-completed-btn';
            button.className = 'btn btn-success btn-sm mt-2';
            button.innerHTML = '<i class="bi bi-check-circle"></i> Marquer comme terminé';
            
            // Ajouter un gestionnaire d'événements direct
            button.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🎯 Click sur bouton "Marquer terminé"');
                this.markManuallyCompleted();
            });
            
            const container = document.getElementById('lesson-progress-container');
            if (container) {
                container.appendChild(button);
                console.log('✅ Bouton "Marquer terminé" créé et ajouté');
            } else {
                console.log('❌ Container lesson-progress-container non trouvé');
            }
        } else {
            button.style.display = 'inline-block';
            console.log('✅ Bouton "Marquer terminé" affiché (existait déjà)');
        }
    }
    
    hideMarkCompletedButton() {
        const button = document.getElementById('mark-lesson-completed-btn');
        if (button) {
            button.style.display = 'none';
        }
    }
    
    showNotification(message, type = 'info') {
        // Utiliser SweetAlert si disponible, sinon une alerte simple
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
    
    async updateCourseProgress() {
        // Mettre à jour la progression du cours (optionnel)
        const courseId = document.body.dataset.courseId;
        if (courseId) {
            try {
                const response = await fetch(`/courses/progress/course/${courseId}/progress/`);
                const data = await response.json();
                
                if (data.success) {
                    this.updateCourseUI(data);
                }
            } catch (error) {
                console.error('Erreur lors de la mise à jour du cours:', error);
            }
        }
    }
    
    async updateGlobalState() {
        // Mettre à jour l'état global de la leçon dans toute l'interface
        const lessonId = this.lessonId;
        
        try {
            // 1. Rafraîchir les données de la playlist depuis le serveur
            await this.refreshPlaylistData();
            
            // 2. Mettre à jour la playlist si elle existe
            this.updatePlaylistState(lessonId);
            
            // 3. Mettre à jour les boutons "Marquer terminé" globaux
            this.updateGlobalButtons(lessonId);
            
            // 4. Mettre à jour les compteurs de progression
            this.updateProgressCounters();
            
            // 5. Déclencher un événement personnalisé pour d'autres composants
            this.dispatchLessonCompletedEvent(lessonId);
            
        } catch (error) {
            console.error('Erreur lors de la mise à jour de l\'état global:', error);
        }
    }
    
    async refreshPlaylistData() {
        // Rafraîchir les données de la playlist depuis le serveur
        const courseId = document.body.dataset.courseId;
        if (!courseId) {
            console.log('❌ Pas de courseId trouvé');
            return;
        }
        
        console.log('🔄 Rafraîchissement playlist pour cours', courseId);
        
        try {
            const response = await fetch(`/courses/progress/course/${courseId}/refresh-playlist/?current_lesson_id=${this.lessonId}`);
            const data = await response.json();
            
            console.log('📝 Données playlist reçues:', data);
            
            if (data.success && data.playlist_data) {
                // Mettre à jour les données de la playlist dans le DOM
                const playlistDataElement = document.getElementById('simple-playlist-data');
                if (playlistDataElement) {
                    console.log('🔄 Mise à jour données playlist DOM');
                    playlistDataElement.textContent = JSON.stringify(data.playlist_data);
                    
                    // Re-générer la playlist
                    if (window.renderSimplePlaylist) {
                        console.log('🎨 Re-génération playlist');
                        window.renderSimplePlaylist();
                    } else {
                        console.log('❌ Fonction renderSimplePlaylist non trouvée');
                    }
                } else {
                    console.log('❌ Élément simple-playlist-data non trouvé');
                }
            } else {
                console.log('❌ Pas de données playlist dans la réponse');
            }
        } catch (error) {
            console.error('❌ Erreur lors du rafraîchissement de la playlist:', error);
        }
    }
    
    updatePlaylistState(lessonId) {
        // Mettre à jour la playlist simple
        const playlistItems = document.querySelectorAll(`[data-lesson-id="${lessonId}"]`);
        
        playlistItems.forEach(item => {
            // Ajouter la classe "completed"
            item.classList.add('lesson-completed');
            
            // Mettre à jour l'icône
            const icon = item.querySelector('.lesson-icon, .bi');
            if (icon) {
                icon.classList.remove('bi-play-circle', 'bi-circle');
                icon.classList.add('bi-check-circle-fill', 'text-success');
            }
            
            // Mettre à jour le statut
            const status = item.querySelector('.lesson-status, .lesson-badge');
            if (status) {
                status.textContent = 'Terminé';
                status.className = 'lesson-status badge badge-success';
            }
        });
    }
    
    updateGlobalButtons(lessonId) {
        // Mettre à jour tous les boutons "Marquer terminé" pour cette leçon
        const markButtons = document.querySelectorAll(`[data-lesson-id="${lessonId}"] .mark-completed-btn, #mark-lesson-${lessonId}`);
        
        markButtons.forEach(button => {
            if (button.tagName === 'BUTTON') {
                button.disabled = true;
                button.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
                button.className = 'btn btn-success btn-sm disabled';
            } else if (button.tagName === 'FORM') {
                // Remplacer le formulaire par un statut
                const statusDiv = document.createElement('div');
                statusDiv.className = 'text-success';
                statusDiv.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Leçon terminée';
                button.parentNode.replaceChild(statusDiv, button);
            }
        });
    }
    
    updateProgressCounters() {
        // Mettre à jour les compteurs de progression dans l'interface
        const progressElements = document.querySelectorAll('[data-progress-counter]');
        
        progressElements.forEach(element => {
            const current = parseInt(element.textContent) || 0;
            element.textContent = current + 1;
        });
        
        // Mettre à jour les barres de progression globales
        const progressBars = document.querySelectorAll('.course-progress-bar');
        progressBars.forEach(bar => {
            const currentWidth = parseFloat(bar.style.width) || 0;
            const newWidth = Math.min(currentWidth + 5, 100); // Approximation
            bar.style.width = `${newWidth}%`;
        });
    }
    
    dispatchLessonCompletedEvent(lessonId) {
        // Déclencher un événement personnalisé
        const event = new CustomEvent('lessonCompleted', {
            detail: {
                lessonId: lessonId,
                timestamp: new Date().toISOString(),
                fullyCompleted: this.is_fully_completed
            }
        });
        
        document.dispatchEvent(event);
    }
    
    updateCourseUI(data) {
        // Mettre à jour l'interface du cours
        const courseProgress = document.getElementById('course-progress');
        if (courseProgress) {
            courseProgress.textContent = `${data.result.final_score.toFixed(1)}%`;
        }
    }
    
    startTracking() {
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
                // Does this cookie string begin with the name we want?
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
    console.log('🚀 DOM chargé - Initialisation lesson_progress.js');
    
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
    
    // Écouter les événements de complétion de leçon
    document.addEventListener('lessonCompleted', function(event) {
        console.log('Leçon complétée:', event.detail);
        
        // Rafraîchir la playlist si nécessaire
        const playlistEl = document.getElementById('simple-playlist');
        if (playlistEl && window.renderSimplePlaylist) {
            // Recharger les données de la playlist
            setTimeout(() => {
                renderSimplePlaylist();
            }, 500);
        }
    });
});

// Fonction globale pour le marquage manuel (pour les boutons existants)
function markLessonCompleted(lessonId) {
    if (window.lessonTracker) {
        window.lessonTracker.markManuallyCompleted();
    }
}
