from flask import Blueprint, render_template, request, redirect, url_for, flash
from Data_Models import Db, Level, Skill, StudntGrp, Studnt, Evaluat, Score, Comment, Note
import re

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def norm_color(val: object) -> str:
    if not val:
        return ''
    s = str(val).strip()
    sl = s.lower()
    name_map = {
        'red': '#ff0000', 'green': '#00ff00', 'blue': '#0000ff', 'yellow': '#ffff00',
        'white': '#ffffff', 'black': '#000000', 'grey': '#808080', 'gray': '#808080'
    }
    if sl in name_map:
        return name_map[sl]
    if sl.startswith('#'):
        if re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', sl):
            if len(sl) == 4:
                return '#' + sl[1]*2 + sl[2]*2 + sl[3]*2
            return sl
        return sl
    if re.match(r'^[0-9a-f]{3}$', sl):
        return '#' + ''.join(ch*2 for ch in sl)
    if re.match(r'^[0-9a-f]{6}$', sl):
        return '#' + sl
    return s

# Map simple resource names to model classes
MODEL_MAP = {
    'skills': Skill,
    'studnt_grps': StudntGrp,
    'studnts': Studnt,
    'evaluats': Evaluat,
    'levels': Level,
    'notes': Note,
}


def get_columns(model):
    return [c.name for c in model.__table__.columns]


REF_MODELS = {
    'Studnt': Studnt,
    'Group': StudntGrp,
    'Skill': Skill,
    'Evaluat': Evaluat,
    'Level': Level,
    'Note': Note,
}


@admin_bp.route('/')
def admin_index():
    return render_template('admin_index.html', resources=list(MODEL_MAP.keys()), norm_color=norm_color)


@admin_bp.route('/<resource>')
def list_resource(resource):
    model = MODEL_MAP.get(resource)
    if not model:
        return "Unknown resource", 404
    cols = get_columns(model)
    items = model.query.all()
    rows = []
    for it in items:
        row = {c: getattr(it, c) for c in cols}
        rows.append(row)
    return render_template('admin_list.html', resource=resource, columns=cols, rows=rows, norm_color=norm_color)


@admin_bp.route('/<resource>/create', methods=['GET', 'POST'])
def create_resource(resource):
    model = MODEL_MAP.get(resource)
    if not model:
        return "Unknown resource", 404
    cols = [c for c in get_columns(model) if c not in ('Id', 'CreatedAt')]
    # prepare choices for foreign-key like fields (ending with _Id)
    choices = {}
    fk_int_fields = set()
    for c in cols:
        if c.endswith('_Id'):
            ref = c[:-3]  # remove trailing _Id
            # Special case: SkillSet_Id is a string field referencing Skill.SkillSet_Id values
            if ref == 'SkillSet':
                opts = []
                rows = Db.session.query(Skill.SkillSet_Id).distinct().all()
                for r in rows:
                    if r and r[0] is not None:
                        opts.append((r[0], r[0]))
                if opts:
                    choices[c] = opts
                continue

            ref_model = REF_MODELS.get(ref)
            if ref_model:
                opts = []
                for o in ref_model.query.all():
                    label = getattr(o, 'Name', None) or getattr(o, 'Code', None) or str(getattr(o, 'Id'))
                    opts.append((str(o.Id), label))
                choices[c] = opts
                fk_int_fields.add(c)
    if request.method == 'POST':
        data = {}
        for c in cols:
            # Special handling for checkbox fields (boolean)
            if c == 'Show_Optional_Column':
                # checkbox sends value when checked, nothing when unchecked
                val = True if request.form.get(c) else False
            else:
                val = request.form.get(c)
            # convert integer foreign keys to int when applicable
            if c in fk_int_fields and val:
                try:
                    data[c] = int(val)
                except ValueError:
                    data[c] = None
            else:
                data[c] = val if val != '' else None
        new = model(**{k: data[k] for k in data})
        Db.session.add(new)
        Db.session.commit()

        # If a new student is created, ensure Score entries exist for existing evaluations
        if resource == 'studnts':
            # find evaluations for this student's group
            evals = Evaluat.query.filter_by(Group_Id=new.Group_Id).all()
            for ev in evals:
                skills = Skill.query.filter_by(SkillSet_Id=ev.SkillSet_Id).all()
                for sk in skills:
                    existing = Score.query.filter_by(Evaluat_Id=ev.Id, Studnt_Id=new.Id, Skill_Id=sk.Id).first()
                    if not existing:
                        s = Score(Evaluat_Id=ev.Id, Studnt_Id=new.Id, Skill_Id=sk.Id, Level_Id=None)
                        Db.session.add(s)
            Db.session.commit()

        # If a new evaluation is created, create Score entries for students in the group
        if resource == 'evaluats':
            ev = new
            # get students in the evaluation group
            students = Studnt.query.filter_by(Group_Id=ev.Group_Id).all()
            skills = Skill.query.filter_by(SkillSet_Id=ev.SkillSet_Id).all()
            for st in students:
                for sk in skills:
                    existing = Score.query.filter_by(Evaluat_Id=ev.Id, Studnt_Id=st.Id, Skill_Id=sk.Id).first()
                    if not existing:
                        s = Score(Evaluat_Id=ev.Id, Studnt_Id=st.Id, Skill_Id=sk.Id, Level_Id=None)
                        Db.session.add(s)
            Db.session.commit()

        # If a new skill is created, ensure Score entries for evaluations with same skillset
        if resource == 'skills':
            sk = new
            evals = Evaluat.query.filter_by(SkillSet_Id=sk.SkillSet_Id).all()
            for ev in evals:
                students = Studnt.query.filter_by(Group_Id=ev.Group_Id).all()
                for st in students:
                    existing = Score.query.filter_by(Evaluat_Id=ev.Id, Studnt_Id=st.Id, Skill_Id=sk.Id).first()
                    if not existing:
                        s = Score(Evaluat_Id=ev.Id, Studnt_Id=st.Id, Skill_Id=sk.Id, Level_Id=None)
                        Db.session.add(s)
            Db.session.commit()

        flash(f'{resource} created', 'success')
        return redirect(url_for('admin.list_resource', resource=resource))
    return render_template('admin_form.html', resource=resource, columns=cols, item=None, choices=choices, attr=getattr, norm_color=norm_color)


@admin_bp.route('/<resource>/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_resource(resource, item_id):
    model = MODEL_MAP.get(resource)
    if not model:
        return "Unknown resource", 404
    item = model.query.get_or_404(item_id)
    cols = [c for c in get_columns(model) if c not in ('Id', 'CreatedAt')]
    # prepare choices for foreign-key like fields
    choices = {}
    fk_int_fields = set()
    for c in cols:
        if c.endswith('_Id'):
            ref = c[:-3]
            if ref == 'SkillSet':
                opts = []
                rows = Db.session.query(Skill.SkillSet_Id).distinct().all()
                for r in rows:
                    if r and r[0] is not None:
                        opts.append((r[0], r[0]))
                if opts:
                    choices[c] = opts
                continue

            ref_model = REF_MODELS.get(ref)
            if ref_model:
                opts = []
                for o in ref_model.query.all():
                    label = getattr(o, 'Name', None) or getattr(o, 'Code', None) or str(getattr(o, 'Id'))
                    opts.append((str(o.Id), label))
                choices[c] = opts
                fk_int_fields.add(c)
    if request.method == 'POST':
        old_group = getattr(item, 'Group_Id', None)
        for c in cols:
            if hasattr(item, c):
                # handle checkbox for boolean fields
                if c == 'Show_Optional_Column':
                    val = True if request.form.get(c) else False
                else:
                    val = request.form.get(c)
                # convert ints for FK fields
                if c in fk_int_fields and val:
                    try:
                        setattr(item, c, int(val))
                    except ValueError:
                        setattr(item, c, None)
                else:
                    # For boolean checkbox, val is already True/False
                    if isinstance(val, bool):
                        setattr(item, c, val)
                    else:
                        setattr(item, c, val if val != '' else None)
        Db.session.commit()

        # If editing a student, ensure Score entries for new group/evaluations exist
        if resource == 'studnts':
            stud = item
            evals = Evaluat.query.filter_by(Group_Id=stud.Group_Id).all()
            for ev in evals:
                skills = Skill.query.filter_by(SkillSet_Id=ev.SkillSet_Id).all()
                for sk in skills:
                    existing = Score.query.filter_by(Evaluat_Id=ev.Id, Studnt_Id=stud.Id, Skill_Id=sk.Id).first()
                    if not existing:
                        s = Score(Evaluat_Id=ev.Id, Studnt_Id=stud.Id, Skill_Id=sk.Id, Level_Id=None)
                        Db.session.add(s)
            Db.session.commit()

        # If editing an evaluation, sync Score entries: add missing and remove obsolete
        if resource == 'evaluats':
            ev = item
            # create missing scores for students in the group
            students = Studnt.query.filter_by(Group_Id=ev.Group_Id).all()
            skills = Skill.query.filter_by(SkillSet_Id=ev.SkillSet_Id).all()
            for st in students:
                for sk in skills:
                    existing = Score.query.filter_by(Evaluat_Id=ev.Id, Studnt_Id=st.Id, Skill_Id=sk.Id).first()
                    if not existing:
                        s = Score(Evaluat_Id=ev.Id, Studnt_Id=st.Id, Skill_Id=sk.Id, Level_Id=None)
                        Db.session.add(s)
            # remove scores that no longer belong (students not in group or skills not in skillset)
            all_scores = Score.query.filter_by(Evaluat_Id=ev.Id).all()
            valid_pairs = {(st.Id, sk.Id) for st in students for sk in skills}
            for sc in all_scores:
                if (sc.Studnt_Id, sc.Skill_Id) not in valid_pairs:
                    # also delete related comments
                    Comment.query.filter_by(Evaluat_Id=ev.Id, Studnt_Id=sc.Studnt_Id, Skill_Id=sc.Skill_Id).delete()
                    Db.session.delete(sc)
            Db.session.commit()

        # If the user clicked 'Appliquer', stay on the edit page after saving
        action = request.form.get('action')
        flash(f'{resource} updated', 'success')
        if action == 'apply':
            # refresh the item from the session to show updated values
            Db.session.refresh(item)
            return render_template('admin_form.html', resource=resource, columns=cols, item=item, choices=choices, attr=getattr, norm_color=norm_color)
        return redirect(url_for('admin.list_resource', resource=resource))
    return render_template('admin_form.html', resource=resource, columns=cols, item=item, choices=choices, attr=getattr, norm_color=norm_color)


@admin_bp.route('/<resource>/delete/<int:item_id>', methods=['POST'])
def delete_resource(resource, item_id):
    model = MODEL_MAP.get(resource)
    if not model:
        return "Unknown resource", 404
    item = model.query.get_or_404(item_id)
    # Compute counts to report in confirmation flash
    deleted_info = {}
    if resource == 'studnts':
        n_scores = Score.query.filter_by(Studnt_Id=item.Id).count()
        n_comments = Comment.query.filter_by(Studnt_Id=item.Id).count()
        Score.query.filter_by(Studnt_Id=item.Id).delete()
        Comment.query.filter_by(Studnt_Id=item.Id).delete()
        deleted_info = {'students': 1, 'scores': n_scores, 'comments': n_comments}
    elif resource == 'evaluats':
        n_scores = Score.query.filter_by(Evaluat_Id=item.Id).count()
        n_comments = Comment.query.filter_by(Evaluat_Id=item.Id).count()
        Score.query.filter_by(Evaluat_Id=item.Id).delete()
        Comment.query.filter_by(Evaluat_Id=item.Id).delete()
        deleted_info = {'evaluats': 1, 'scores': n_scores, 'comments': n_comments}
    elif resource == 'skills':
        n_scores = Score.query.filter_by(Skill_Id=item.Id).count()
        n_comments = Comment.query.filter_by(Skill_Id=item.Id).count()
        Score.query.filter_by(Skill_Id=item.Id).delete()
        Comment.query.filter_by(Skill_Id=item.Id).delete()
        deleted_info = {'skills': 1, 'scores': n_scores, 'comments': n_comments}
    elif resource == 'studnt_grps':
        students = Studnt.query.filter_by(Group_Id=item.Id).all()
        evals = Evaluat.query.filter_by(Group_Id=item.Id).all()
        n_students = len(students)
        n_evals = len(evals)
        n_scores = 0
        n_comments = 0
        for st in students:
            cs = Score.query.filter_by(Studnt_Id=st.Id).count()
            cc = Comment.query.filter_by(Studnt_Id=st.Id).count()
            n_scores += cs
            n_comments += cc
            Score.query.filter_by(Studnt_Id=st.Id).delete()
            Comment.query.filter_by(Studnt_Id=st.Id).delete()
            Db.session.delete(st)
        for ev in evals:
            es = Score.query.filter_by(Evaluat_Id=ev.Id).count()
            ec = Comment.query.filter_by(Evaluat_Id=ev.Id).count()
            n_scores += es
            n_comments += ec
            Score.query.filter_by(Evaluat_Id=ev.Id).delete()
            Comment.query.filter_by(Evaluat_Id=ev.Id).delete()
            Db.session.delete(ev)
        deleted_info = {'groups': 1, 'students': n_students, 'evaluats': n_evals, 'scores': n_scores, 'comments': n_comments}

    # Delete the main item
    Db.session.delete(item)
    Db.session.commit()

    # Build a readable summary message
    parts = []
    for k, v in deleted_info.items():
        parts.append(f"{v} {k}")
    summary = ', '.join(parts) if parts else f"1 {resource}"
    flash(f'Deletion completed: {summary}', 'success')
    return redirect(url_for('admin.list_resource', resource=resource))
