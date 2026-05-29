"""
Configuration de l'assignation automatique des parcours d'apprentissage
"""

# Structures éligibles pour l'auto-assignation
# Les utilisateurs de ces structures auront un template assigné automatiquement
AUTO_ASSIGN_STRUCTURES = [
    'commune',      # Agents communaux
    'minsante',      # Personnel de santé
    'bunec',         # Inspecteurs BUNEC
    # Ajoutez d'autres structures ici si nécessaire
    # 'universite',   # Étudiants universitaires
    # 'ong',          # ONG
    # 'consultant',   # Consultants
]

# Priorité d'assignation par niveau (du plus prioritaire au moins prioritaire)
ASSIGNMENT_PRIORITY = [
    'beginner',      # Priorité 1 : parcours débutant
    'intermediate',   # Priorité 2 : parcours intermédiaire  
    'advanced',       # Priorité 3 : parcours avancé
]

# Messages personnalisés par structure
ASSIGNMENT_MESSAGES = {
    'commune': {
        'success': '🏛️ Parcours communal assigné automatiquement !',
        'welcome': 'Bienvenue dans votre parcours de formation d\'agent communal',
    },
    'minsante': {
        'success': '🏥 Parcours santé assigné automatiquement !',
        'welcome': 'Bienvenue dans votre parcours de formation du personnel de santé',
    },
    'bunec': {
        'success': '🏛️ Parcours BUNEC assigné automatiquement !',
        'welcome': 'Bienvenue dans votre parcours de formation d\'inspecteur BUNEC',
    },
    'default': {
        'success': '🎯 Parcours assigné automatiquement !',
        'welcome': 'Bienvenue dans votre parcours d\'apprentissage',
    }
}

def is_auto_assign_enabled(structure):
    """Vérifie si l'auto-assignation est activée pour cette structure"""
    return structure in AUTO_ASSIGN_STRUCTURES

def get_assignment_message(structure, message_type='success'):
    """Récupère le message personnalisé pour une structure"""
    structure_messages = ASSIGNMENT_MESSAGES.get(structure, ASSIGNMENT_MESSAGES['default'])
    return structure_messages.get(message_type, ASSIGNMENT_MESSAGES['default'][message_type])

def get_priority_templates(templates):
    """Retourne les templates ordonnés par priorité"""
    prioritized_templates = []
    
    for level in ASSIGNMENT_PRIORITY:
        level_templates = templates.filter(level=level)
        prioritized_templates.extend(level_templates)
    
    return prioritized_templates
