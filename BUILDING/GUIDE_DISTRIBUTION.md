# GUIDE DE DISTRIBUTION ET D'INSTALLATION
## EDPL Competence Evaluation Tool

---

## POUR L'ADMINISTRATEUR : Compiler et préparer le package

> Cette section est destinée à la personne qui prépare le package à distribuer.
> Elle n'est **pas nécessaire** pour les utilisateurs finaux.

### Prérequis de compilation

- Python 3.8+ installé avec le venv du projet
- Le projet source complet

### Gestion des versions de build

La version est automatiquement calculée à chaque build :
- **`BUILDING/VERSION.txt`** : version majeure, éditable manuellement (ex. `1.0`, `1.1`, `2.0`)
- **`BUILDING/build_counter.txt`** : compteur auto-incrémenté (ne pas éditer)
- **Version générée** : `v1.0-b003_20260304` (version + numéro + date)
- **`BUILDING/build_log.txt`** : historique de tous les builds avec date et résultat

Pour changer la version majeure (ex. passage à la `1.1`) : éditer `BUILDING/VERSION.txt` et écrire `1.1`.

### Compilation sur Windows

1. Ouvrir le dossier `BUILDING/`
2. Double-cliquer sur `build_windows.bat`
3. Le dossier de distribution est créé dans `BUILDING\dist\EDPL_EvaluationTool\`

### Compilation sur macOS

```bash
cd EDPL_CompetenceEvaluationTools/BUILDING/
chmod +x build_mac.sh
./build_mac.sh
```

Le dossier de distribution est créé dans `BUILDING/dist/EDPL_EvaluationTool/`.

### Préparer le ZIP à distribuer

Le dossier `BUILDING/dist/EDPL_EvaluationTool/` contient tout le nécessaire.

**Structure du dossier distribué :**
```
EDPL_EvaluationTool/
├── EDPL_EvaluationTool.exe   ← exécutable principal (Windows)
│   ou EDPL_EvaluationTool   ← exécutable principal (macOS/Linux)
├── VERSION.txt               ← version du build (informationnel)
├── GUIDE_DISTRIBUTION.md     ← ce guide
├── _internal/                ← bibliothèques Python (ne pas supprimer)
├── instance/                 ← BASE DE DONNÉES (créée au premier lancement)
│   └── evaluat.db            ← données à sauvegarder / transférer
└── static/
    └── uploads/
        └── trombi/           ← photos étudiants (à sauvegarder / transférer)
```

**Nommer le ZIP avec la version** (bonne pratique) :
- `EDPL_EvaluationTool_v1.0-b003_Windows.zip`
- `EDPL_EvaluationTool_v1.0-b003_macOS.zip`

**Créer le ZIP :**
- Windows : clic droit sur le dossier `EDPL_EvaluationTool` → "Compresser en fichier ZIP"
- macOS : clic droit → "Compresser"

**Important :** Le build Windows ne fonctionne que sur Windows, le build macOS que sur Mac.
Il faut donc compiler séparément sur chaque plateforme.

---

## POUR L'UTILISATEUR FINAL : Installation et démarrage

### Étape 1 — Récupérer le fichier

Téléchargez ou recevez le fichier ZIP `EDPL_EvaluationTool.zip` et décompressez-le.

Choisissez un emplacement stable sur votre ordinateur (par exemple `Documents`).
**Évitez de déplacer le dossier une fois l'application utilisée** (les données resteraient à l'ancien emplacement).

```
📁 Documents/
└── 📁 EDPL_EvaluationTool/     ← dossier à conserver ici
    ├── EDPL_EvaluationTool.exe
    ├── _internal/
    └── ...
```

---

### Étape 2 — Lancer l'application

#### Sur Windows

1. Ouvrir le dossier `EDPL_EvaluationTool/`
2. Double-cliquer sur **`EDPL_EvaluationTool.exe`**

> **Si Windows affiche un avertissement "Application inconnue"** :
> - Cliquer sur **"Informations complémentaires"**
> - Puis **"Exécuter quand même"**
>
> (Ce message apparaît car l'application n'est pas signée numériquement. Elle est sans danger.)

3. Une fenêtre noire (terminal) s'ouvre — **ne pas la fermer**, elle fait tourner le serveur
4. Votre navigateur s'ouvre automatiquement sur **http://localhost:5000**

#### Sur macOS

1. Ouvrir le dossier `EDPL_EvaluationTool/`
2. Faire un **clic droit** sur `EDPL_EvaluationTool` → **"Ouvrir"**

> **Si macOS affiche "impossible d'ouvrir car développeur non identifié"** :
> - Aller dans **Préférences Système → Sécurité et confidentialité**
> - Cliquer sur **"Ouvrir quand même"**
>
> (Ce message apparaît car l'application n'est pas signée Apple. Elle est sans danger.)

3. Un terminal s'ouvre — **ne pas le fermer**
4. Votre navigateur s'ouvre automatiquement sur **http://localhost:5000**

---

### Étape 3 — Utiliser l'application

L'application fonctionne dans votre navigateur web habituel.
L'adresse est toujours : **http://localhost:5000**

Si le navigateur ne s'ouvre pas automatiquement, ouvrez manuellement votre navigateur
et saisissez l'adresse `http://localhost:5000`.

---

### Étape 4 — Arrêter l'application

Fermez la fenêtre noire (terminal) pour arrêter le serveur.
Vos données sont automatiquement sauvegardées dans la base SQLite.

---

## TRANSFERT DE DONNÉES ENTRE POSTES

Pour copier vos données d'un ordinateur à un autre **sans perte** :

### Ce qu'il faut copier

| Élément | Chemin | Contenu |
|---|---|---|
| Base de données | `EDPL_EvaluationTool/instance/evaluat.db` | Toutes les évaluations, étudiants, scores, commentaires |
| Photos étudiants | `EDPL_EvaluationTool/static/uploads/trombi/` | Images des étudiants |

### Procédure de transfert

**Sur le poste SOURCE (l'ancien ordinateur) :**
1. Fermer l'application
2. Copier le fichier `instance/evaluat.db`
3. Copier tout le dossier `static/uploads/trombi/`

**Sur le poste DESTINATION (le nouvel ordinateur) :**
1. Installer l'application (décompresser le ZIP)
2. **Avant** le premier lancement, coller le fichier `evaluat.db` dans le dossier `instance/`
3. Coller les photos dans `static/uploads/trombi/`
4. Lancer l'application — toutes les données sont restaurées

> **Conseil :** Sauvegardez régulièrement le fichier `evaluat.db`
> (simple copie sur clé USB ou cloud). Il contient l'intégralité de vos données.

---

## RÉSOLUTION DE PROBLÈMES

### Le navigateur ne s'ouvre pas automatiquement
→ Ouvrir manuellement Chrome, Firefox ou Edge et aller sur `http://localhost:5000`

### Le port 5000 est déjà utilisé
→ Une autre application utilise le port 5000. Fermer le terminal, attendre quelques secondes, relancer.
→ Ou fermer l'autre application qui utilise ce port.

### L'application ne démarre pas (Windows)
→ Vérifier que le dossier `EDPL_EvaluationTool/` n'est pas dans un dossier protégé (ex. `C:\Windows\`, `C:\Program Files\`). Déplacer dans `Documents`.

### Erreur "database is locked"
→ L'application est déjà lancée (une autre fenêtre est ouverte). Fermer toutes les instances.

### Perte de données accidentelle
→ Des sauvegardes automatiques sont créées dans `instance/` avec l'extension `.bak.<timestamp>`.
→ Copier l'une d'elles en `evaluat.db` pour restaurer.

---

## INFORMATIONS TECHNIQUES

| Élément | Détail |
|---|---|
| Type | Application web locale (serveur Flask embarqué) |
| Base de données | SQLite (fichier `evaluat.db`) |
| Port réseau | 5000 (local uniquement, pas accessible depuis Internet) |
| Aucun accès Internet requis | L'application fonctionne entièrement hors-ligne |
| Données | Stockées localement, jamais envoyées à l'extérieur |
