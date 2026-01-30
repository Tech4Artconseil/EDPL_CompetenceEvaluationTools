"""
App_Main.py
Flask application with routes and logic for student competence evaluation.
Handles dashboard display, score updates, comments, and CSV export.
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
import re
from Data_Models import Db, Level, Skill, Studnt, Evaluat, Score, Comment, Note, EvaluatNote
from admin import admin_bp
import csv
import io
from datetime import datetime

# Initialize Flask application
App = Flask(__name__)
# Use the package's `instance` folder for the SQLite DB so Data_Init and the app agree
PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(PACKAGE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, 'evaluat.db')
# Use forward slashes in the URI to avoid Windows backslash issues
App.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH.replace('\\', '/')
App.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
App.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Initialize database with app
Db.init_app(App)

# Register admin blueprint
App.register_blueprint(admin_bp)
from import_csv import importer_bp
App.register_blueprint(importer_bp)


def norm_color(val: object) -> str:
    """Normalize a color value for CSS use. Returns a hex color like '#rrggbb' or the original string.

    Accepts values already in '#rrggbb' or 'rrggbb' or common color names (red, green...).
    """
    if not val:
        return ''
    s = str(val).strip()
    sl = s.lower()
    # common name map
    name_map = {
        'red': '#ff0000', 'green': '#00ff00', 'blue': '#0000ff', 'yellow': '#ffff00',
        'white': '#ffffff', 'black': '#000000', 'grey': '#808080', 'gray': '#808080'
    }
    if sl in name_map:
        return name_map[sl]
    # already with #
    if sl.startswith('#'):
        if re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', sl):
            if len(sl) == 4:  # expand #rgb to #rrggbb
                return '#' + sl[1]*2 + sl[2]*2 + sl[3]*2
            return sl
        return sl
    # hex without #
    if re.match(r'^[0-9a-f]{3}$', sl):
        return '#' + ''.join(ch*2 for ch in sl)
    if re.match(r'^[0-9a-f]{6}$', sl):
        return '#' + sl
    return s


@App.route('/')
def App_Main_Dashboard():
    """
    Main dashboard route - displays evaluation grid.
    Shows students (rows) vs skills (columns) with level selection.
    """
    # Allow selecting an evaluation via query param ?evaluat_id=ID
    evaluat_id = request.args.get('evaluat_id', type=int)
    Current_Evaluat = None
    if evaluat_id:
        Current_Evaluat = Evaluat.query.get(evaluat_id)

    # If none selected, pick the first evaluation
    if not Current_Evaluat:
        Current_Evaluat = Evaluat.query.first()

    if not Current_Evaluat:
        return "No evaluation found. Please run Data_Init.py first.", 404

    # Load all evaluations for the panels
    All_Evaluats = Evaluat.query.order_by(Evaluat.CreatedAt.desc()).all()
    
    # Get all students in the evaluation's group
    All_Studnts = Studnt.query.filter_by(Group_Id=Current_Evaluat.Group_Id).order_by(Studnt.Name).all()
    
    # Get all skills in the evaluation's skill set
    All_Skills = Skill.query.filter_by(SkillSet_Id=Current_Evaluat.SkillSet_Id).order_by(Skill.Code).all()
    
    # Get all levels for the level selector
    All_Levels = Level.query.filter_by(LevelSet_Id=1).order_by(Level.Percent).all()
    
    # Get all scores for this evaluation
    # Create a dictionary for quick lookup: (student_id, skill_id) -> score
    All_Scores = Score.query.filter_by(Evaluat_Id=Current_Evaluat.Id).all()
    Scores_Dict = {}
    for Score_tmp in All_Scores:
        Key = f"{Score_tmp.Studnt_Id}_{Score_tmp.Skill_Id}"
        Scores_Dict[Key] = Score_tmp
    
    # Get all comments for this evaluation
    All_Comments = Comment.query.filter_by(Evaluat_Id=Current_Evaluat.Id).all()
    Comments_Dict = {}
    for Comment_tmp in All_Comments:
        Key = f"{Comment_tmp.Studnt_Id}_{Comment_tmp.Skill_Id}"
        if Key not in Comments_Dict:
            Comments_Dict[Key] = []
        Comments_Dict[Key].append(Comment_tmp)

    # Build a mapping of student_id -> comments for comments that are NOT tied to a skill
    Student_Comments_Dict = {}
    for Comment_tmp in All_Comments:
        if Comment_tmp.Skill_Id is None:
            sid = Comment_tmp.Studnt_Id
            if sid not in Student_Comments_Dict:
                Student_Comments_Dict[sid] = []
            Student_Comments_Dict[sid].append(Comment_tmp)

    # Get all notes and build mapping student_id -> note_id for this evaluation
    All_Notes = Note.query.order_by(Note.Valeure.desc()).all()
    Student_Notes_Dict = {}
    All_Evaluat_Notes = EvaluatNote.query.filter_by(Evaluat_Id=Current_Evaluat.Id).all()
    for en in All_Evaluat_Notes:
        Student_Notes_Dict[en.Studnt_Id] = en.Note_Id
    
    return render_template(
        'Eval_Dash.html',
        Evaluat=Current_Evaluat,
        All_Evaluats=All_Evaluats,
        Studnts=All_Studnts,
        Skills=All_Skills,
        Levels=All_Levels,
        All_Notes=All_Notes,
        Scores_Dict=Scores_Dict,
        Comments_Dict=Comments_Dict,
        Student_Comments_Dict=Student_Comments_Dict,
        Student_Notes_Dict=Student_Notes_Dict,
        norm_color=norm_color
    )



@App.route('/api/evaluat/note/set', methods=['POST'])
def App_Main_Evaluat_Note_Set():
    """Assign or remove a Note for a student in an evaluation.
    JSON: {evaluat_id, studnt_id, note_id|null}
    """
    Data = request.get_json() or {}
    evaluat_id = Data.get('evaluat_id')
    studnt_id = Data.get('studnt_id')
    note_id = Data.get('note_id')  # can be null to remove

    if not evaluat_id or not studnt_id:
        return jsonify({'success': False, 'error': 'evaluat_id and studnt_id required'}), 400

    try:
        existing = EvaluatNote.query.filter_by(Evaluat_Id=evaluat_id, Studnt_Id=studnt_id).first()
        if not note_id:
            if existing:
                Db.session.delete(existing)
                Db.session.commit()
            return jsonify({'success': True})

        note = Note.query.get(int(note_id))
        if not note:
            return jsonify({'success': False, 'error': 'Note not found'}), 404

        if existing:
            existing.Note_Id = note.Id
        else:
            en = EvaluatNote(Evaluat_Id=evaluat_id, Studnt_Id=studnt_id, Note_Id=note.Id)
            Db.session.add(en)
        Db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        Db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@App.route('/api/score/update', methods=['POST'])
def App_Main_Score_Update():
    """
    API endpoint to update a student's score for a skill.
    Receives JSON with student_id, skill_id, and level_id.
    """
    Data = request.get_json()
    
    Studnt_Id = Data.get('studnt_id')
    Skill_Id = Data.get('skill_id')
    Level_Id = Data.get('level_id')
    Evaluat_Id = Data.get('evaluat_id')
    
    # Find the score entry
    Score_Entry = Score.query.filter_by(
        Evaluat_Id=Evaluat_Id,
        Studnt_Id=Studnt_Id,
        Skill_Id=Skill_Id
    ).first()
    
    if not Score_Entry:
        return jsonify({'success': False, 'error': 'Score entry not found'}), 404
    
    # Update the level
    Score_Entry.Level_Id = Level_Id if Level_Id else None
    Db.session.commit()
    
    return jsonify({'success': True})


@App.route('/api/notes/list', methods=['GET'])
def App_Main_Notes_List():
    """Return list of all notes as JSON."""
    All_Notes = Note.query.order_by(Note.Valeure.desc()).all()
    notes = [n.Note_To_Dict() for n in All_Notes]
    return jsonify({'success': True, 'notes': notes})


@App.route('/api/notes/add', methods=['POST'])
def App_Main_Notes_Add():
    """Create or update a Note. JSON body: {id?, valeure, descript}
    If id provided, update; otherwise create new.
    """
    Data = request.get_json() or {}
    nid = Data.get('id')
    valeure = Data.get('valeure')
    descript = Data.get('descript')

    if valeure is None:
        return jsonify({'success': False, 'error': 'Field "valeure" is required'}), 400

    try:
        if nid:
            note = Note.query.get(int(nid))
            if not note:
                return jsonify({'success': False, 'error': 'Note not found'}), 404
            note.Valeure = int(valeure)
            note.Descript = descript
        else:
            note = Note(Valeure=int(valeure), Descript=descript)
            Db.session.add(note)
        Db.session.commit()
        return jsonify({'success': True, 'note': note.Note_To_Dict()})
    except Exception as e:
        Db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@App.route('/api/notes/delete', methods=['POST'])
def App_Main_Notes_Delete():
    """Delete a note. JSON body: {id}
    """
    Data = request.get_json() or {}
    nid = Data.get('id')
    if not nid:
        return jsonify({'success': False, 'error': 'Field "id" is required'}), 400
    try:
        note = Note.query.get(int(nid))
        if not note:
            return jsonify({'success': False, 'error': 'Note not found'}), 404
        Db.session.delete(note)
        Db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        Db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@App.route('/api/comment/add', methods=['POST'])
def App_Main_Comment_Add():
    """
    API endpoint to add a comment for a student/skill combination.
    Receives JSON with student_id, skill_id, and comment text.
    """
    Data = request.get_json()
    
    Studnt_Id = Data.get('studnt_id')
    Skill_Id = Data.get('skill_id')
    Comment_Text = Data.get('comment_text')
    Evaluat_Id = Data.get('evaluat_id')
    
    if not Comment_Text or not Comment_Text.strip():
        return jsonify({'success': False, 'error': 'Comment text is required'}), 400
    
    # Create new comment
    try:
        New_Comment = Comment(
            Evaluat_Id=Evaluat_Id,
            Studnt_Id=Studnt_Id,
            Skill_Id=Skill_Id,
            Text=Comment_Text.strip()
        )
        Db.session.add(New_Comment)
        Db.session.commit()
    except Exception as e:
        # Rollback and return JSON error so client-side JSON.parse won't fail
        Db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({
        'success': True,
        'comment': New_Comment.Comment_To_Dict()
    })


@App.route('/api/comment/list', methods=['GET'])
def App_Main_Comment_List():
    """
    API endpoint to get comments for a student/skill combination.
    Query params: studnt_id, skill_id, evaluat_id
    """
    Studnt_Id = request.args.get('studnt_id', type=int)
    Skill_Id = request.args.get('skill_id', type=int)
    Evaluat_Id = request.args.get('evaluat_id', type=int)
    
    # Get all comments for this combination
    All_Comments = Comment.query.filter_by(
        Evaluat_Id=Evaluat_Id,
        Studnt_Id=Studnt_Id,
        Skill_Id=Skill_Id
    ).order_by(Comment.CreatedAt.desc()).all()
    
    Comments_List = [Comment_tmp.Comment_To_Dict() for Comment_tmp in All_Comments]
    
    return jsonify({'success': True, 'comments': Comments_List})


@App.route('/export/csv')
def App_Main_Export_CSV():
    """
    Export evaluation data to CSV file with semicolon separator.
    Creates a CSV with students as rows and skills as columns.
    """
    # Allow exporting a specific evaluation via query param ?evaluat_id=ID
    evaluat_id = request.args.get('evaluat_id', type=int)
    if evaluat_id:
        Current_Evaluat = Evaluat.query.get(evaluat_id)
    else:
        Current_Evaluat = Evaluat.query.first()

    if not Current_Evaluat:
        return "No evaluation found", 404
    
    # Get all students and skills
    All_Studnts = Studnt.query.filter_by(Group_Id=Current_Evaluat.Group_Id).order_by(Studnt.Name).all()
    All_Skills = Skill.query.filter_by(SkillSet_Id=Current_Evaluat.SkillSet_Id).order_by(Skill.Code).all()
    
    # Get all scores
    All_Scores = Score.query.filter_by(Evaluat_Id=Current_Evaluat.Id).all()
    Scores_Dict = {}
    for Score_tmp in All_Scores:
        Key = (Score_tmp.Studnt_Id, Score_tmp.Skill_Id)
        Scores_Dict[Key] = Score_tmp
    
    # Create CSV in memory
    Output = io.StringIO()
    Writer = csv.writer(Output, delimiter=';')
    
    # Write header row
    Header = ['Student', 'Email']
    for Skill_tmp in All_Skills:
        Header.append(f'{Skill_tmp.Code}')
    Writer.writerow(Header)
    
    # Write data rows - one row per student
    for Studnt_tmp in All_Studnts:
        Row = [Studnt_tmp.Name, Studnt_tmp.Email]
        
        # Add score for each skill
        for Skill_tmp in All_Skills:
            Key = (Studnt_tmp.Id, Skill_tmp.Id)
            Score_Entry = Scores_Dict.get(Key)
            
            if Score_Entry and Score_Entry.Level:
                # Write level percentage
                Row.append(f'{Score_Entry.Level.Percent}%')
            else:
                # No level assigned
                Row.append('')
        
        Writer.writerow(Row)
    
    # Prepare file for download
    Output.seek(0)
    Output_Bytes = io.BytesIO()
    Output_Bytes.write(Output.getvalue().encode('utf-8'))
    Output_Bytes.seek(0)
    
    # Generate filename with timestamp
    Filename = f'evaluat_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return send_file(
        Output_Bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=Filename
    )


if __name__ == '__main__':
    # Run the Flask development server
    App.run(debug=True, host='0.0.0.0', port=5000)
