# Student Competence Evaluation Tool

A Flask-based web application for evaluating students based on competencies and skill levels. This tool helps workflow consultants assess student performance across multiple skills using a color-coded grid system.

## Features

- **Interactive Grid View**: Students (rows) vs Skills (columns) grid layout
- **Level Selection**: Four-level evaluation system with color coding:
  - 🔴 Red (20%) - Maitrise insufisente
  - 🟡 Yellow (50%) - maitrise Faible
  - 🟢 Green (75%) - Maitrise sufisante
  - 🔵 Blue (100%) - Tres bonne maitrise
- **Comment System**: Add and view comments for each student/skill combination
- **CSV Export**: Export evaluation results with semicolon separator
- **Real-time Updates**: AJAX-based score updates without page refresh

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Tech4Artconseil/EDPL_CompetenceEvaluationTools.git
cd EDPL_CompetenceEvaluationTools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python Data_Init.py
```

This will create:
- Level Set #1 with 4 evaluation levels
- Skills Set #1 (DNMADE3_18.3) with 3 skills
- Student Group #1 (DNMADE3_INT_IP_A) with 7 students (Étudiant 17-23)
- Evaluation #1: "Rhino Modeling Pince Alors _SwabDesign_"

## Running the Application

Start the Flask development server:
```bash
python App_Main.py
```

The application will be available at: `http://localhost:5000`

## Usage

### Evaluating Students

1. Open the dashboard in your web browser
2. For each student/skill combination:
   - Select a level from the dropdown menu
   - The cell will automatically color-code based on the level
   - Changes are saved automatically to the database

### Adding Comments

1. Click the 💬 button in any cell
2. A modal will open showing existing comments
3. Type your comment in the text area
4. Click "Add Comment" to save
5. The comment count will appear next to the 💬 button

### Exporting Data

Click the "Export CSV" button to download evaluation results as a CSV file with semicolon separators.

## Project Structure

```
EDPL_CompetenceEvaluationTools/
├── App_Main.py              # Flask application with routes and logic
├── Data_Models.py           # SQLAlchemy database models
├── Data_Init.py            # Database initialization script
├── requirements.txt         # Python dependencies
├── templates/
│   └── Eval_Dash.html      # Main dashboard template
├── static/
│   └── css/
│       └── Main_Style.css  # Application styling
└── instance/
    └── evaluat.db          # SQLite database (created on first run)
```

## Database Schema

The application uses SQLite with the following models:

- **Level**: Evaluation levels with percentages and colors
- **Skill**: Competencies to be evaluated
- **StudntGrp**: Student groups
- **Studnt**: Individual students
- **Evaluat**: Evaluation sessions
- **Score**: Student scores for each skill
- **Comment**: Comments on student/skill combinations

## Naming Conventions

The code follows strict naming conventions:
- Words > 10 characters are truncated (e.g., 'Evaluation' → 'Evaluat')
- Variables start with uppercase (e.g., `StudntList`)
- Functions include parent class name with underscores (e.g., `Studnt_Update_Score`)
- Loop variables are suffixed with `_tmp` (e.g., `for Stud_tmp in Stud_List:`)

## Technology Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLite with SQLAlchemy 2.0.23
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with responsive design

## Development

To modify the prepopulated data, edit the `Data_Init.py` file and re-run it:

```bash
python Data_Init.py
```

Note: The script will skip initialization if data already exists. Delete `instance/evaluat.db` to reset the database.

## Screenshots

### Dashboard with Color-Coded Levels
![Dashboard](https://github.com/user-attachments/assets/283ff1f6-6b6e-4717-a765-4b64ea9b6caf)

### Comment System
![Comments](https://github.com/user-attachments/assets/fd9ee888-73f3-49d0-9132-451b32594bdf)

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE  - see the LICENSE file for details.

## Support

For issues or questions, please open an issue on the GitHub repository.
