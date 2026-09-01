# 📊 PowerBI Data Extractor - Contourner les Restrictions d'Export

Application spécialisée pour extraire les données des tableaux, matrices et graphiques **Microsoft Power BI**, même lorsque le bouton *"Exporter vers Excel"* ou le partage est verrouillé par les règles de sécurité de l'organisation.

---

## 🎯 Les 2 Méthodes Disponibles

### 📸 Méthode 1 : Vision IA Multimodale (La plus universelle)
* **Idéale pour :** Rapports internes sécurisés avec authentification d'entreprise (SSO, 2FA, Microsoft Authenticator), graphiques et matrices complexes.
* **Fonctionnement :** 
  1. Ouvrez votre rapport Power BI dans votre navigateur normal.
  2. Faites une capture d'écran de votre tableau (`Touche Windows + Shift + S` ou outil Capture).
  3. Collez directement (`Ctrl + V`) ou glissez la capture dans l'application.
  4. L'IA **Gemini Vision** analyse l'image et reconstitue le tableau complet cellule par cellule.

### 🌐 Méthode 2 : Interception Réseau Automatisée (Playwright)
* **Idéale pour :** Rapports partagés via un lien web (`https://app.powerbi.com/view?r=...` ou intégrations iframe).
* **Fonctionnement :** 
  1. Collez l'URL Power BI dans l'application.
  2. Le navigateur invisible intercepte les requêtes réseau internes `querydata` et extrait les données tabulaires brutes du modèle sémantique DAX.

---

## 💾 Formats d'Export

* 📊 **Excel (.xlsx)** : Classeur professionnel formaté avec en-têtes Power BI Blue, bordures et colonnes ajustées.
* 📄 **CSV (.csv)** : Encodé en UTF-8-sig pour un affichage propre des caractères français et nombres sous Microsoft Excel.
* 📋 **JSON** : Copie brute pour développeurs et intégrations API.

---

## 🚀 Démarrage Rapide

```bash
cd "C:\Users\Mr Elkrouchni\.gemini\antigravity\scratch\powerbi-scraper"
python app.py --port 8600
```
Puis rendez-vous sur : **[http://localhost:8600](http://localhost:8600)**
