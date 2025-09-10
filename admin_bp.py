import os, zipfile, csv, uuid, shutil
from pathlib import Path
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app , abort
from flask_login import current_user
from werkzeug.utils import secure_filename
from config import Config
import string
import secrets

bp = Blueprint('admin', __name__, url_prefix='/admin')

# ---------- 工具 ----------
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.UPLOAD_ALLOWED_EXT

# ---------- 路由 ----------
@bp.route('/cards', methods=['GET', 'POST'])
def cards():

    if not current_user.is_authenticated or current_user.role != 'admin':
        abort(403)
    """
    GET : 展示新增表单
    POST: 处理表单 + 上传 zip + 落库 function.csv + 解压到 functions/{id}/
    """
    if request.method == 'POST':
        # 1. 取字段
        id_ = request.form.get('id', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        input_list = [x.strip() for x in request.form.get('input_list', '').split(',') if x.strip()]
        output_list = [x.strip() for x in request.form.get('output_list', '').split(',') if x.strip()]
        input_desc = [x.strip() for x in request.form.get('input_list_description', '').split(';') if x.strip()]
        output_desc = [x.strip() for x in request.form.get('output_list_description', '').split(';') if x.strip()]

        # 2. 简单校验
        if not id_ or not name or not input_list or not output_list:
            flash('ID/名称/输入/输出为必填')
            return redirect(request.url)
        if not all(x.isalnum() or x == '_' for x in id_):
            flash('ID 只能包含小写字母、数字、下划线')
            return redirect(request.url)

        # 3. 处理上传 zip
        zip_file = request.files.get('zip_file')
        if not zip_file or zip_file.filename == '':
            flash('必须上传 zip 压缩包（含 env/ 与 program/run.py）')
            return redirect(request.url)
        if not allowed_file(zip_file.filename):
            flash('仅允许 zip 格式')
            return redirect(request.url)

        # 4. 落盘临时 zip
        tmp_zip = Path(Config.UPLOAD_TMP_DIR) / f"{uuid.uuid4().hex}.zip"
        zip_file.save(tmp_zip)

        # 5. 解压并校验结构
        func_dir = Path(Config.FUNCTIONS_DIR) / id_
        if func_dir.exists():
            flash('ID 已存在')
            return redirect(request.url)
        func_dir.mkdir(parents=True)

        with zipfile.ZipFile(tmp_zip, 'r') as zf:
            # 提前检查
            namelist = zf.namelist()
            if not any('env/' in s for s in namelist) or 'program/run.py' not in namelist:
                flash('zip 内必须包含 env/ 目录与 program/run.py')
                return redirect(request.url)
            zf.extractall(func_dir)

        # 6. 追加写入 function.csv
        csv_file = Path(current_app.root_path) / 'function.csv'
        new_row = [
            id_, name,
            str(input_list).replace("'", '"'),
            str(output_list).replace("'", '"'),
            description,
            str(input_desc).replace("'", '"'),
            str(output_desc).replace("'", '"')
        ]
        with csv_file.open('a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(new_row)

        # 7. 清理临时文件
        tmp_zip.unlink(missing_ok=True)

        flash('服务卡片新增成功！')
        return redirect(url_for('admin.cards'))

    # GET：渲染表单
    return render_template('admin/card_form.html')



#生成邀请码
def random64() -> str:
    """生成 64 位 URL-safe 字符串"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))

#这里对用进行管理
from models import db,InvCode
# InvCode表只有一列为invcode，是64位字符串类型
@bp.route('/users', methods=['GET', 'POST'])
def users():
    # 仅管理员
    if not current_user.is_authenticated or current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        # 读取追加数量
        try:
            count = int(request.form.get('count', 0))
        except ValueError:
            count = 0
        if count <= 0 or count > 10000:          # 一次最多 1w 条，可调
            flash('请输入 1-10000 之间的整数')
            return render_template('admin/invcode.html')

        # 生成+写入
        new_codes = []
        for _ in range(count):
            code = random64()
            new_codes.append(InvCode(invcode=code))
        # 批量插入（忽略已存在）
        db.session.bulk_save_objects(new_codes, return_defaults=False)
        db.session.commit()

        # 把新增列表传给模板
        return render_template('admin/invcode.html',
                               created=[c.invcode + '\n' for c in new_codes])

    # GET：展示表单
    return render_template('admin/invcode.html')