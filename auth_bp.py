# auth_bp.py
from flask import Blueprint, request, redirect, url_for, flash, render_template
from models import db, User, InvCode

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        invcode = request.form['invcode']

        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('auth.auth'))

        inv_code_entry = InvCode.query.filter_by(invcode=invcode).first()
        if not inv_code_entry:
            flash('错误的邀请码')
            return redirect(url_for('auth.auth'))

        # 创建用户
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)

        # 注册成功后删除邀请码
        db.session.delete(inv_code_entry)
        db.session.commit()

        flash('注册成功，请登录')
        return redirect(url_for('login')) 

    return render_template('auth.html')