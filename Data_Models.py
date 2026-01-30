"""
Data_Models.py
SQLAlchemy database models for student competence evaluation system.
Follows strict naming conventions with truncated words and uppercase variables.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

Db = SQLAlchemy()


class Level(Db.Model):
    """Level model - represents evaluation levels with percentage and color"""
    __tablename__ = 'levels'
    
    Id = Db.Column(Db.Integer, primary_key=True)
    LevelSet_Id = Db.Column(Db.Integer, nullable=False)
    Percent = Db.Column(Db.Integer, nullable=False)  # 20, 50, 75, 100
    Descrip = Db.Column(Db.String(100), nullable=False)  # Description truncated
    Color = Db.Column(Db.String(20), nullable=False)  # Red, Yellow, Green, Blue
    
    def Level_To_Dict(self):
        """Convert Level instance to dictionary"""
        return {
            'Id': self.Id,
            'LevelSet_Id': self.LevelSet_Id,
            'Percent': self.Percent,
            'Descrip': self.Descrip,
            'Color': self.Color
        }


class Skill(Db.Model):
    """Skill model - represents competences to evaluate"""
    __tablename__ = 'skills'
    
    Id = Db.Column(Db.Integer, primary_key=True)
    SkillSet_Id = Db.Column(Db.String(50), nullable=False)  # e.g., DNMADE3_18.3
    Code = Db.Column(Db.String(20), nullable=False)  # e.g., C1.1
    Descrip = Db.Column(Db.String(200), nullable=False)  # Description truncated
    
    def Skill_To_Dict(self):
        """Convert Skill instance to dictionary"""
        return {
            'Id': self.Id,
            'SkillSet_Id': self.SkillSet_Id,
            'Code': self.Code,
            'Descrip': self.Descrip
        }


class StudntGrp(Db.Model):
    """Student Group model - represents groups of students"""
    __tablename__ = 'studnt_grps'
    
    Id = Db.Column(Db.Integer, primary_key=True)
    Name = Db.Column(Db.String(100), nullable=False)  # e.g., DNMADE3_INT_IP_A
    
    def StudntGrp_To_Dict(self):
        """Convert StudntGrp instance to dictionary"""
        return {
            'Id': self.Id,
            'Name': self.Name
        }


class Studnt(Db.Model):
    """Student model - represents individual students"""
    __tablename__ = 'studnts'
    
    Id = Db.Column(Db.Integer, primary_key=True)
    Name = Db.Column(Db.String(100), nullable=False)  # e.g., Étudiant 17
    Email = Db.Column(Db.String(100), nullable=False)
    Group_Id = Db.Column(Db.Integer, Db.ForeignKey('studnt_grps.Id'), nullable=False)
    
    # Relationship to group
    Group = Db.relationship('StudntGrp', backref='studnts')
    
    def Studnt_To_Dict(self):
        """Convert Studnt instance to dictionary"""
        return {
            'Id': self.Id,
            'Name': self.Name,
            'Email': self.Email,
            'Group_Id': self.Group_Id
        }


class Evaluat(Db.Model):
    """Evaluation model - represents an evaluation session"""
    __tablename__ = 'evaluats'
    
    Id = Db.Column(Db.Integer, primary_key=True)
    Name = Db.Column(Db.String(200), nullable=False)
    Group_Id = Db.Column(Db.Integer, Db.ForeignKey('studnt_grps.Id'), nullable=False)
    SkillSet_Id = Db.Column(Db.String(50), nullable=False)
    CreatedAt = Db.Column(Db.DateTime, default=datetime.utcnow)
    
    # Relationships
    Group = Db.relationship('StudntGrp', backref='evaluats')
    
    def Evaluat_To_Dict(self):
        """Convert Evaluat instance to dictionary"""
        return {
            'Id': self.Id,
            'Name': self.Name,
            'Group_Id': self.Group_Id,
            'SkillSet_Id': self.SkillSet_Id,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None
        }


class Score(Db.Model):
    """Score model - represents student scores for skills"""
    __tablename__ = 'scores'
    
    Id = Db.Column(Db.Integer, primary_key=True)
    Evaluat_Id = Db.Column(Db.Integer, Db.ForeignKey('evaluats.Id'), nullable=False)
    Studnt_Id = Db.Column(Db.Integer, Db.ForeignKey('studnts.Id'), nullable=False)
    Skill_Id = Db.Column(Db.Integer, Db.ForeignKey('skills.Id'), nullable=False)
    Level_Id = Db.Column(Db.Integer, Db.ForeignKey('levels.Id'), nullable=True)
    
    # Relationships
    Evaluat = Db.relationship('Evaluat', backref='scores')
    Studnt = Db.relationship('Studnt', backref='scores')
    Skill = Db.relationship('Skill', backref='scores')
    Level = Db.relationship('Level', backref='scores')
    
    def Score_To_Dict(self):
        """Convert Score instance to dictionary"""
        return {
            'Id': self.Id,
            'Evaluat_Id': self.Evaluat_Id,
            'Studnt_Id': self.Studnt_Id,
            'Skill_Id': self.Skill_Id,
            'Level_Id': self.Level_Id
        }


class Comment(Db.Model):
    """Comment model - represents comments on student/skill combinations"""
    __tablename__ = 'comments'
    
    Id = Db.Column(Db.Integer, primary_key=True)
    Evaluat_Id = Db.Column(Db.Integer, Db.ForeignKey('evaluats.Id'), nullable=False)
    Studnt_Id = Db.Column(Db.Integer, Db.ForeignKey('studnts.Id'), nullable=False)
    Skill_Id = Db.Column(Db.Integer, Db.ForeignKey('skills.Id'), nullable=False)
    Text = Db.Column(Db.Text, nullable=False)
    CreatedAt = Db.Column(Db.DateTime, default=datetime.utcnow)
    
    # Relationships
    Evaluat = Db.relationship('Evaluat', backref='comments')
    Studnt = Db.relationship('Studnt', backref='comments')
    Skill = Db.relationship('Skill', backref='comments')
    
    def Comment_To_Dict(self):
        """Convert Comment instance to dictionary"""
        return {
            'Id': self.Id,
            'Evaluat_Id': self.Evaluat_Id,
            'Studnt_Id': self.Studnt_Id,
            'Skill_Id': self.Skill_Id,
            'Text': self.Text,
            'CreatedAt': self.CreatedAt.isoformat() if self.CreatedAt else None
        }
