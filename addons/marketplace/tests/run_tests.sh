#!/bin/bash
# Script pour lancer les tests du marketplace
# Usage: ./run_tests.sh [test_type]
# test_type: all | http | interactions | access | coverage

set -e

ODOO_HOME="/home/jakk/Bureau/repository/MarketHub/odoo"
DB_NAME="marketplace_db"
MODULE="marketplace"

cd "$ODOO_HOME"

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 Lancement des tests du Marketplace${NC}"
echo "================================================"

# Vérifier si la base existe
if ! python odoo-bin --list-db | grep -q "^$DB_NAME\$"; then
    echo -e "${RED}❌ Base de données '$DB_NAME' non trouvée${NC}"
    exit 1
fi

# Fonction pour lancer les tests
run_tests() {
    local test_type=$1
    local test_module=$2
    
    echo -e "${YELLOW}📝 Lancement de: $test_type${NC}"
    
    python odoo-bin -d "$DB_NAME" \
        -m "$MODULE" \
        --test-enable \
        --stop-after-init \
        --log-level=info
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $test_type réussis!${NC}"
    else
        echo -e "${RED}❌ $test_type échoués!${NC}"
        exit 1
    fi
}

case "${1:-all}" in
    all)
        echo -e "${YELLOW}🚀 Exécution de tous les tests...${NC}"
        run_tests "Tests HTTP" "marketplace.tests.test_http"
        run_tests "Tests Interactions" "marketplace.tests.test_interactions"
        run_tests "Tests Accès" "marketplace.tests.test_access_control"
        echo -e "${GREEN}✅ Tous les tests sont passés!${NC}"
        ;;
    http)
        echo -e "${YELLOW}🌐 Exécution des tests HTTP...${NC}"
        run_tests "Tests HTTP" "marketplace.tests.test_http"
        ;;
    interactions)
        echo -e "${YELLOW}💬 Exécution des tests d'interactions...${NC}"
        run_tests "Tests Interactions" "marketplace.tests.test_interactions"
        ;;
    access)
        echo -e "${YELLOW}🔐 Exécution des tests d'accès...${NC}"
        run_tests "Tests Accès" "marketplace.tests.test_access_control"
        ;;
    coverage)
        echo -e "${YELLOW}📊 Exécution avec couverture de code...${NC}"
        python odoo-bin -d "$DB_NAME" \
            -m "$MODULE" \
            --test-enable \
            --stop-after-init \
            --log-level=debug
        ;;
    help)
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Types de tests disponibles:"
        echo "  all         - Tous les tests"
        echo "  http        - Tests HTTP"
        echo "  interactions - Tests d'interactions"
        echo "  access      - Tests d'accès"
        echo "  coverage    - Avec analyse de couverture"
        echo "  help        - Affiche cette aide"
        ;;
    *)
        echo -e "${RED}❌ Type de test inconnu: $1${NC}"
        echo "Utilisez: $0 help"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo -e "${GREEN}✨ Tests terminés!${NC}"
