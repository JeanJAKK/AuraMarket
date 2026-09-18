#!/bin/bash
# Script sûr pour supprimer et recréer la base de données marketplace_db (propriétaire : odoo)

echo "=== Réinitialisation de la base de données marketplace_db ==="

# 1. Terminer toutes les connexions actives à la base (nécessaire avant DROP DATABASE)
echo "Terminaison des connexions actives à la base..."
sudo -u postgres psql -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'marketplace_db' AND pid <> pg_backend_pid();
" 2>/dev/null || echo "Aucune connexion active ou erreur (ignorée)."

# 2. Supprimer la base de données si elle existe (en tant qu'utilisateur odoo, puis postgres en fallback)
echo "Suppression de la base de données..."
dropdb marketplace_db -U odoo --if-exists 2>/dev/null || \
  echo "Échec en tant qu'utilisateur odoo, essai avec l'utilisateur postgres..." && \
  sudo -u postgres dropdb marketplace_db --if-exists

# 3. Créer une nouvelle base de données avec odoo comme propriétaire
echo "Création de la base de données avec propriétaire odoo..."
createdb marketplace_db -U odoo -O odoo 2>/dev/null || \
  echo "Échec en tant qu'utilisateur odoo, essai avec l'utilisateur postgres..." && \
  sudo -u postgres createdb -O odoo marketplace_db

echo "✅ Base de données marketplace_db recréée avec succès (propriétaire : odoo)."
echo "Vous pouvez maintenant relancer la commande Odoo :"
echo "  source venv/bin/activate"
echo "  python odoo/odoo-bin -d marketplace_db --addons-path=odoo/addons,odoo/odoo/addons,addons -u marketplace --db_host=localhost --db_port=5432 --db_user=odoo --db_password=odoo --dev=all"