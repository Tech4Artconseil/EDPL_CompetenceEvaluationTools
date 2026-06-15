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
├── instance/
│   └── evaluat.db            ← BDD pré-remplie avec données de démo
└── _internal/static/
    └── uploads/
        └── trombi/           ← photos étudiants embarquées par PyInstaller
            ├── DUPONT_Alice.png
            ├── MARTIN_Thomas.png
            ├── BERNARD_Lea.png
            ├── MOREAU_Julien.jpg
            └── PETIT_Emma.jpg
```

> **Note :** Les photos trombi (démo **et** photos importées après déploiement) sont stockées dans
> `_internal/static/uploads/trombi/`. L'application sauvegarde les nouvelles photos importées dans ce
> même dossier (chemin calculé par rapport au code embarqué, pas à côté de l'exécutable).
> Il n'y a **pas** de dossier `static/` à côté de l'exécutable.

### BDD seed et données de démo

Le script `BUILDING/create_seed_db.py` génère automatiquement la base de données de démo
à chaque build. Il est appelé par `build_windows.bat` à l'étape `[6/6] Finalisation`.

**Contenu de la BDD seed :**

| Table | Données incluses |
|---|---|
| `saisons` | 1 saison : **"Test"** |
| `skill_sets` | 2 référentiels : **DNMADE3_18.3** (9 compétences) et **CUSTM_Eval_Set_1** (4 compétences) |
| `levels` | 4 niveaux : MI (rouge), MF (orange), MS (vert), TBM (vert foncé) |
| `notes` | Échelle 0–20 (21 valeurs) |
| `studnt_grps` | 1 groupe : **Groupe_Demo** |
| `studnts` | 5 étudiants fictifs avec photos trombi associées |
| `evaluats` | 1 évaluation : **Demo_Evaluation** (grille pré-remplie) |
| `scores` | 45 scores de démo (5 étudiants × 9 compétences) |

**Étudiants de démo et leurs photos :**

| Nom | Email | Photo |
|---|---|---|
| DUPONT Alice | alice.dupont@demo.local | `DUPONT_Alice.png` |
| MARTIN Thomas | thomas.martin@demo.local | `MARTIN_Thomas.png` |
| BERNARD Léa | lea.bernard@demo.local | `BERNARD_Lea.png` |
| MOREAU Julien | julien.moreau@demo.local | `MOREAU_Julien.jpg` |
| PETIT Emma | emma.petit@demo.local | `PETIT_Emma.jpg` |

Pour modifier les données de démo (ajouter des étudiants, changer les compétences…),
éditer directement `BUILDING/create_seed_db.py` puis relancer le build.

> **Comportement si une BDD existe déjà :** au démarrage, `Db.create_all()` crée uniquement les
> tables manquantes — aucune donnée existante n'est écrasée. La seed n'est copiée qu'à l'issue
> du build ; une installation déjà utilisée conserve ses propres données.

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
| Photos importées | `EDPL_EvaluationTool/_internal/static/uploads/trombi/` | Photos ajoutées **après** le déploiement initial |

> Les photos de démo (DUPONT_Alice, MARTIN_Thomas, etc.) sont également dans
> `_internal/static/uploads/trombi/` ; elles sont fournies avec le package et n'ont pas besoin
> d'être copiées manuellement.

### Procédure de transfert

**Sur le poste SOURCE (l'ancien ordinateur) :**
1. Fermer l'application
2. Copier le fichier `instance/evaluat.db`
3. Copier tout le dossier `_internal/static/uploads/trombi/`

**Sur le poste DESTINATION (le nouvel ordinateur) :**
1. Installer l'application (décompresser le ZIP)
2. **Avant** le premier lancement, coller le fichier `evaluat.db` dans le dossier `instance/`
3. Coller les photos dans `_internal/static/uploads/trombi/`
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
| BDD seed | Générée par `BUILDING/create_seed_db.py` à chaque build |
| Initialisation tables | `Db.create_all()` au démarrage — tables manquantes créées automatiquement |
| Photos de démo | Embarquées dans le bundle PyInstaller (`_internal/static/uploads/trombi/`) |
| Photos utilisateur | Stockées dans `_internal/static/uploads/trombi/` (à l'intérieur du bundle) |
| Référentiels inclus | `DNMADE3_18.3` (9 compétences) · `CUSTM_Eval_Set_1` (4 compétences) |
