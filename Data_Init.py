"""
Data_Init.py
Script to prepopulate database with initial data for student evaluation system.
Run this script to initialize the database with levels, skills, students, and evaluation.
"""

from Data_Models import Db, Level, Skill, StudntGrp, Studnt, Evaluat, Score
from App_Main import App


def DataInit_Create_All():
    """
    Initialize database with all required data.
    Creates tables and populates with Level Set #1, Skills Set #1, 
    Student Group #1, and Evaluation #1.
    """
    with App.app_context():
        # Create all database tables
        Db.create_all()
        
        # Check if data already exists to avoid duplicates
        if Level.query.first() is not None:
            print("Database already initialized. Skipping data creation.")
            return
        
        print("Initializing database with prepopulated data...")
        
        # Create Level Set #1 (LS_1)
        DataInit_Create_Levels()
        
        # Create Skills Set #1 (DNMADE3_18.3)
        DataInit_Create_Skills()
        
        # Create Student Group #1 (DNMADE3_INT_IP_A)
        DataInit_Create_Studnts()
        
        # Create Evaluation #1
        DataInit_Create_Evaluat()
        
        print("Database initialization completed successfully!")


def DataInit_Create_Levels():
    """
    Create Level Set #1 (LS_1) with 4 levels.
    Each level has percentage, description and color.
    """
    Levels_Data = [
        {'LevelSet_Id': 1, 'Percent': 20, 'Descrip': 'Maitrise insufisente', 'Color': 'Red'},
        {'LevelSet_Id': 1, 'Percent': 50, 'Descrip': 'maitrise Faible', 'Color': 'Yellow'},
        {'LevelSet_Id': 1, 'Percent': 75, 'Descrip': 'Maitrise sufisante', 'Color': 'Green'},
        {'LevelSet_Id': 1, 'Percent': 100, 'Descrip': 'Tres bonne maitrise', 'Color': 'Blue'}
    ]
    
    # Loop through levels data and create Level instances
    for Level_tmp in Levels_Data:
        New_Level = Level(
            LevelSet_Id=Level_tmp['LevelSet_Id'],
            Percent=Level_tmp['Percent'],
            Descrip=Level_tmp['Descrip'],
            Color=Level_tmp['Color']
        )
        Db.session.add(New_Level)
    
    Db.session.commit()
    print(f"Created {len(Levels_Data)} levels in Level Set #1")


def DataInit_Create_Skills():
    """
    Create Skills Set #1 (DNMADE3_18.3) with 3 skills.
    Each skill has code and description.
    """
    Skills_Data = [
        {
            'SkillSet_Id': 'DNMADE3_18.3',
            'Code': 'C1.1',
            'Descrip': 'Use digital reference tools...'
        },
        {
            'SkillSet_Id': 'DNMADE3_18.3',
            'Code': 'C4.4',
            'Descrip': 'Develop an argumentation...'
        },
        {
            'SkillSet_Id': 'DNMADE3_18.3',
            'Code': 'C6.2',
            'Descrip': 'Identify emerging workshop...'
        }
    ]
    
    # Loop through skills data and create Skill instances
    for Skill_tmp in Skills_Data:
        New_Skill = Skill(
            SkillSet_Id=Skill_tmp['SkillSet_Id'],
            Code=Skill_tmp['Code'],
            Descrip=Skill_tmp['Descrip']
        )
        Db.session.add(New_Skill)
    
    Db.session.commit()
    print(f"Created {len(Skills_Data)} skills in Skills Set #1")


def DataInit_Create_Studnts():
    """
    Create Student Group #1 (DNMADE3_INT_IP_A) with students 17-23.
    Each student has name and email (truc@email.com).
    """
    # Create student group first
    New_Group = StudntGrp(Name='DNMADE3_INT_IP_A')
    Db.session.add(New_Group)
    Db.session.commit()
    
    Group_Id = New_Group.Id
    
    # Create students 17 to 23
    Studnt_Count = 0
    for Studnt_Num in range(17, 24):  # 17 to 23 inclusive
        New_Studnt = Studnt(
            Name=f'Étudiant {Studnt_Num}',
            Email='truc@email.com',
            Group_Id=Group_Id
        )
        Db.session.add(New_Studnt)
        Studnt_Count += 1
    
    Db.session.commit()
    print(f"Created Student Group #1 with {Studnt_Count} students (Étudiant 17-23)")


def DataInit_Create_Evaluat():
    """
    Create Evaluation #1 with name and links to Group #1 and Skills Set #1.
    Also create empty score entries for all student/skill combinations.
    """
    # Get the group we just created
    Group_1 = StudntGrp.query.filter_by(Name='DNMADE3_INT_IP_A').first()
    
    # Create evaluation
    New_Evaluat = Evaluat(
        Name='Rhino Modeling Pince Alors _SwabDesign_ ',
        Group_Id=Group_1.Id,
        SkillSet_Id='DNMADE3_18.3'
    )
    Db.session.add(New_Evaluat)
    Db.session.commit()
    
    Evaluat_Id = New_Evaluat.Id
    
    # Get all students in this group
    All_Studnts = Studnt.query.filter_by(Group_Id=Group_1.Id).all()
    
    # Get all skills in this skill set
    All_Skills = Skill.query.filter_by(SkillSet_Id='DNMADE3_18.3').all()
    
    # Create score entries for each student/skill combination
    # Initial scores have no level assigned (Level_Id = None)
    Score_Count = 0
    for Studnt_tmp in All_Studnts:
        for Skill_tmp in All_Skills:
            New_Score = Score(
                Evaluat_Id=Evaluat_Id,
                Studnt_Id=Studnt_tmp.Id,
                Skill_Id=Skill_tmp.Id,
                Level_Id=None  # No level assigned initially
            )
            Db.session.add(New_Score)
            Score_Count += 1
    
    Db.session.commit()
    print(f"Created Evaluation #1 with {Score_Count} score entries")


if __name__ == '__main__':
    DataInit_Create_All()
