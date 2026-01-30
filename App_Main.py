"""
App_Main.py
Flask application with routes and logic for student competence evaluation.
Handles dashboard display, score updates, comments, and CSV export.
"""

from flask import Flask, render_template, request, jsonify, send_file
from Data_Models import Db, Level, Skill, Studnt, Evaluat, Score, Comment
import csv
import io
from datetime import datetime

# Initialize Flask application
App = Flask(__name__)
App.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evaluat.db'
App.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
App.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Initialize database with app
Db.init_app(App)


@App.route('/')
def App_Main_Dashboard():
    """
    Main dashboard route - displays evaluation grid.
    Shows students (rows) vs skills (columns) with level selection.
    """
    # Get the first evaluation (we only have one initially)
    Current_Evaluat = Evaluat.query.first()
    
    if not Current_Evaluat:
        return "No evaluation found. Please run Data_Init.py first.", 404
    
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
        Key = (Score_tmp.Studnt_Id, Score_tmp.Skill_Id)
        Scores_Dict[Key] = Score_tmp
    
    # Get all comments for this evaluation
    All_Comments = Comment.query.filter_by(Evaluat_Id=Current_Evaluat.Id).all()
    Comments_Dict = {}
    for Comment_tmp in All_Comments:
        Key = (Comment_tmp.Studnt_Id, Comment_tmp.Skill_Id)
        if Key not in Comments_Dict:
            Comments_Dict[Key] = []
        Comments_Dict[Key].append(Comment_tmp)
    
    return render_template(
        'Eval_Dash.html',
        Evaluat=Current_Evaluat,
        Studnts=All_Studnts,
        Skills=All_Skills,
        Levels=All_Levels,
        Scores_Dict=Scores_Dict,
        Comments_Dict=Comments_Dict
    )


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
    New_Comment = Comment(
        Evaluat_Id=Evaluat_Id,
        Studnt_Id=Studnt_Id,
        Skill_Id=Skill_Id,
        Text=Comment_Text.strip()
    )
    Db.session.add(New_Comment)
    Db.session.commit()
    
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
    # Get the first evaluation
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
