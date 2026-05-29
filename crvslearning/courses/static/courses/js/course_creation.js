// Variables globales
let moduleCount = 0;
const lessonCounters = {};
const videoCounters = {};

// Fonction pour mettre à jour les numéros des modules
function updateModuleNumbers() {
    $('.module-card').each(function(index) {
        const moduleIndex = index + 1;
        $(this).find('.module-number').text(moduleIndex);
        $(this).find('input[name$="-order"]').val(moduleIndex);
    });
}

// Fonction pour mettre à jour les numéros des leçons dans un module
function updateLessonNumbers(moduleIndex) {
    $(`[data-module-index="${moduleIndex}"] .lesson-card`).each(function(index) {
        const lessonIndex = index + 1;
        $(this).find('.lesson-number').text(lessonIndex);
        $(this).find('input[name$="-order"]').val(lessonIndex);
    });
}

// Fonction pour mettre à jour les numéros des vidéos dans une leçon
function updateVideoNumbers(moduleIndex, lessonIndex) {
    $(`[data-module-index="${moduleIndex}"] [data-lesson-index="${lessonIndex}"] .video-item`).each(function(index) {
        const videoIndex = index + 1;
        $(this).find('.video-number').text(videoIndex);
        $(this).find('input[name$="-order"]').val(videoIndex);
    });
}

// Initialisation au chargement du document
$(document).ready(function() {
    // Gestion de l'ajout d'un module
    $(document).on('click', '#addModuleBtn, #addAnotherModule', function() {
        const moduleIndex = moduleCount++;
        const moduleTemplate = $('#moduleTemplate').html()
            .replace(/MODULE_INDEX/g, moduleIndex);
        
        $('#modulesContainer').append(moduleTemplate);
        lessonCounters[moduleIndex] = 0;
        updateModuleNumbers();
        
        // Faire défiler jusqu'au module ajouté
        $('html, body').animate({
            scrollTop: $(`[data-module-index="${moduleIndex}"]`).offset().top - 20
        }, 500);
    });

    // Gestion de l'ajout d'une leçon
    $(document).on('click', '.add-lesson-btn', function() {
        const moduleIndex = $(this).closest('[data-module-index]').data('module-index');
        const lessonIndex = lessonCounters[moduleIndex]++;
        const lessonTemplate = $('#lessonTemplate').html()
            .replace(/MODULE_INDEX/g, moduleIndex)
            .replace(/LESSON_INDEX/g, lessonIndex);
        
        $(`#lessonsContainer-${moduleIndex}`).append(lessonTemplate);
        updateLessonNumbers(moduleIndex);
        
        // Initialiser le compteur de vidéos pour cette leçon
        videoCounters[`${moduleIndex}-${lessonIndex}`] = 0;
    });

    // Gestion de l'ajout d'une vidéo
    $(document).on('click', '.add-video-btn', function() {
        const moduleIndex = $(this).closest('[data-module-index]').data('module-index');
        const lessonIndex = $(this).closest('[data-lesson-index]').data('lesson-index');
        const videoIndex = videoCounters[`${moduleIndex}-${lessonIndex}`]++;
        
        const videoTemplate = $('#videoTemplate').html()
            .replace(/MODULE_INDEX/g, moduleIndex)
            .replace(/LESSON_INDEX/g, lessonIndex)
            .replace(/VIDEO_INDEX/g, videoIndex);
        
        $(`#videosContainer-${moduleIndex}-${lessonIndex}`).append(videoTemplate);
        updateVideoNumbers(moduleIndex, lessonIndex);
    });

    // Gestion de la suppression d'un module
    $(document).on('click', '.remove-module', function() {
        if (confirm('Êtes-vous sûr de vouloir supprimer ce module ? Toutes les leçons et vidéos associées seront également supprimées.')) {
            $(this).closest('.module-card').remove();
            updateModuleNumbers();
        }
    });

    // Gestion de la suppression d'une leçon
    $(document).on('click', '.remove-lesson', function() {
        if (confirm('Êtes-vous sûr de vouloir supprimer cette leçon ? Toutes les vidéos associées seront également supprimées.')) {
            const moduleIndex = $(this).closest('[data-module-index]').data('module-index');
            $(this).closest('.lesson-card').remove();
            updateLessonNumbers(moduleIndex);
        }
    });

    // Gestion de la suppression d'une vidéo
    $(document).on('click', '.remove-video', function() {
        if (confirm('Êtes-vous sûr de vouloir supprimer cette vidéo ?')) {
            const moduleIndex = $(this).closest('[data-module-index]').data('module-index');
            const lessonIndex = $(this).closest('[data-lesson-index]').data('lesson-index');
            $(this).closest('.video-item').remove();
            updateVideoNumbers(moduleIndex, lessonIndex);
        }
    });

    // Prévisualisation de l'image de la miniature
    $('#id_thumbnail').on('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#thumbnailPreview').html(`<img src="${e.target.result}" class="img-thumbnail thumbnail-preview" alt="Aperçu de la miniature">`);
            }
            reader.readAsDataURL(file);
        }
    });

    // Gestion de la soumission du formulaire
    $('#courseForm').on('submit', function(e) {
        e.preventDefault();
        
        // Désactiver le bouton de soumission
        const submitButton = $(this).find('button[type="submit"]');
        const originalButtonText = submitButton.html();
        submitButton.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enregistrement...');
        
        // Préparer les données du formulaire
        const formData = new FormData(this);
        
        // Ajouter les données des modules, leçons et vidéos
        const modulesData = [];
        $('.module-card').each(function(moduleIdx) {
            const moduleData = {
                title: $(this).find('input[name$="-title"]').val(),
                description: $(this).find('textarea[name$="-description"]').val(),
                order: moduleIdx + 1,
                lessons: []
            };
            
            $(this).find('.lesson-card').each(function(lessonIdx) {
                const lessonData = {
                    title: $(this).find('input[name$="-title"]').val(),
                    description: $(this).find('textarea[name$="-description"]').val(),
                    order: lessonIdx + 1,
                    videos: []
                };
                
                $(this).find('.video-item').each(function(videoIdx) {
                    const videoFile = $(this).find('input[type="file"]')[0].files[0];
                    const videoData = {
                        title: $(this).find('input[name$="-title"]').val(),
                        order: videoIdx + 1,
                        video_file: videoFile || null
                    };
                    lessonData.videos.push(videoData);
                });
                
                moduleData.lessons.push(lessonData);
            });
            
            modulesData.push(moduleData);
        });
        
        // Ajouter les données sérialisées au FormData
        formData.set('modules_data', JSON.stringify(modulesData));
        
        // Envoyer les données via AJAX
        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.redirect_url) {
                    window.location.href = response.redirect_url;
                } else {
                    // Afficher un message de succès
                    alert('Le cours a été créé avec succès !');
                    window.location.reload();
                }
            },
            error: function(xhr) {
                let errorMessage = 'Une erreur est survenue lors de la création du cours.';
                if (xhr.responseJSON && xhr.responseJSON.errors) {
                    errorMessage = 'Veuillez corriger les erreurs suivantes :\n' + 
                                 Object.values(xhr.responseJSON.errors).join('\n');
                }
                alert(errorMessage);
            },
            complete: function() {
                // Réactiver le bouton de soumission
                submitButton.prop('disabled', false).html(originalButtonText);
            }
        });
    });

    // Gestion de l'aperçu du cours
    $('#previewBtn').on('click', function() {
        // Récupérer les données du formulaire
        const formData = new FormData(document.getElementById('courseForm'));
        const courseData = {
            title: formData.get('title'),
            description: formData.get('description'),
            category: $('#id_category option:selected').text(),
            language: formData.get('language'),
            thumbnail: $('#id_thumbnail')[0].files[0] ? 
                      URL.createObjectURL($('#id_thumbnail')[0].files[0]) : 
                      '{% static "img/default-course.jpg" %}',
            modules: []
        };
        
        // Récupérer les données des modules
        $('.module-card').each(function() {
            const moduleData = {
                title: $(this).find('input[name$="-title"]').val(),
                description: $(this).find('textarea[name$="-description"]').val(),
                lessons: []
            };
            
            // Récupérer les données des leçons
            $(this).find('.lesson-card').each(function() {
                const lessonData = {
                    title: $(this).find('input[name$="-title"]').val(),
                    description: $(this).find('textarea[name$="-description"]').val(),
                    videos: []
                };
                
                // Récupérer les données des vidéos
                $(this).find('.video-item').each(function() {
                    const videoFile = $(this).find('input[type="file"]')[0];
                    const videoData = {
                        title: $(this).find('input[name$="-title"]').val(),
                        description: $(this).find('textarea[name$="-description"]').val(),
                        duration: $(this).find('input[name$="-duration"]').val()
                    };
                    lessonData.videos.push(videoData);
                });
                
                moduleData.lessons.push(lessonData);
            });
            
            courseData.modules.push(moduleData);
        });
        
        // Mettre à jour le contenu du modal de prévisualisation
        const previewModal = $('#previewModal');
        const previewContent = previewModal.find('.modal-body');
        
        // Construire le HTML de l'aperçu
        let previewHtml = `
            <div class="mb-4">
                <h3>${courseData.title}</h3>
                <p class="text-muted">${courseData.description}</p>
                <p><strong>Catégorie :</strong> ${courseData.category}</p>
                <p><strong>Langue :</strong> ${courseData.language}</p>
                <img src="${courseData.thumbnail}" class="img-fluid rounded mb-3" alt="Miniature du cours">
            </div>
            <hr>
            <h4>Modules (${courseData.modules.length})</h4>
        `;
        
        // Ajouter les modules
        courseData.modules.forEach((module, moduleIndex) => {
            previewHtml += `
                <div class="card mb-3">
                    <div class="card-header">
                        <h5 class="mb-0">Module ${moduleIndex + 1}: ${module.title || 'Sans titre'}</h5>
                    </div>
                    <div class="card-body">
                        <p>${module.description || 'Aucune description'}</p>
                        <h6>Leçons (${module.lessons.length})</h6>
            `;
            
            // Ajouter les leçons
            module.lessons.forEach((lesson, lessonIndex) => {
                previewHtml += `
                    <div class="card mb-2">
                        <div class="card-body p-3">
                            <h6 class="mb-1">Leçon ${lessonIndex + 1}: ${lesson.title || 'Sans titre'}</h6>
                            <p class="mb-1 small">${lesson.description || 'Aucune description'}</p>
                            <p class="mb-0 small"><strong>Vidéos (${lesson.videos.length})</strong></p>
                            <ul class="mb-0">
                `;
                
                // Ajouter les vidéos
                lesson.videos.forEach((video, videoIndex) => {
                    previewHtml += `
                        <li class="small">
                            ${video.title || 'Sans titre'} 
                            ${video.duration ? `(${video.duration} min)` : ''}
                        </li>
                    `;
                });
                
                previewHtml += `
                            </ul>
                        </div>
                    </div>
                `;
            });
            
            previewHtml += `
                    </div>
                </div>
            `;
        });
        
        // Mettre à jour le contenu du modal
        previewContent.html(previewHtml);
        
        // Afficher le modal
        previewModal.modal('show');
    });

    // Gestion des sections dépliables
    $(document).on('click', '.collapsible-header', function() {
        $(this).next('.collapsible-content').slideToggle();
        $(this).find('i').toggleClass('fa-chevron-down fa-chevron-up');
    });

    // Initialiser les sections dépliables comme ouvertes
    $('.collapsible-content').show();
});
