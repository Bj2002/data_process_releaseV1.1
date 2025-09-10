from pathlib import Path
import os
import csv
import ast
import subprocess
import uuid
from flask import send_file , Flask, request, redirect, url_for, render_template, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import platform
import secrets
from config import Config
from models import db,User

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# 关于注册
from auth_bp import bp as auth_bp
app.register_blueprint(auth_bp)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    if not os.path.exists('instance'):
        os.makedirs('instance')
    db.create_all()

# 和adminpage有关
from admin_bp import bp as admin_bp
app.register_blueprint(admin_bp)

@app.route('/contact')
def contact () :
    return render_template('contact.html')

@app.route('/user_guide')
def user_guide () :
    return render_template('user_guide.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('用户名或密码错误')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已登出')
    return redirect(url_for('index'))


root_path = os.path.dirname(os.path.abspath(__file__))
tmp_upload_dir = os.path.join (os.path.dirname(os.path.abspath(__file__)), 'tmp_uploads')
Path(tmp_upload_dir).mkdir(exist_ok=True)
function_list_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'function.csv')

@app.route('/')
@login_required
def index():
    #return f'欢迎回来，{current_user.username}！<br><a href="{url_for("logout")}">退出</a>'
    return render_template('index.html',username = current_user.username)

@app.route('/menu')
def menu():

    functions = [] 
    try:
        with open(function_list_path, newline='', encoding='utf-8') as csvfile:
            
            reader = csv.DictReader(csvfile)
            for row in reader:
                
                # 转换字符串列表为实际列表
                row['input_list'] = eval(row['input_list'])
                row['output_list'] = eval(row['output_list'])
                functions.append(row)
    except FileNotFoundError:
        app.logger.error("function.csv file not found")
    return render_template('menu.html', functions=functions)




@app.route('/function/<function_id>', methods=['GET', 'POST'])
def function_detail(function_id):
    FUNCTION_MAP = {}
    with open(function_list_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            FUNCTION_MAP[row['ID']] = {
            'name': row['name'],
            'input_list': eval(row['input_list']),
            'output_list': eval(row['output_list']),
            'description': row['description'],
            'input_descs': eval(row['input_list_description']),
            'output_descs': eval(row['output_list_description'])
            }
    if function_id not in FUNCTION_MAP:
        return "Function not found", 404
    
    func_info = FUNCTION_MAP[function_id]
    
    if request.method == 'GET':
        return render_template('function_page.html', 
                               func_id=function_id,
                               func_info=func_info)
    
    elif request.method == 'POST':
        try:
            # 为每个请求创建唯一的临时子目录
            request_id = uuid.uuid4().hex
            temp_dir = os.path.join(tmp_upload_dir , request_id)
            os.makedirs(temp_dir, exist_ok=True)
            
            input_paths = []
            # 保存上传的文件到临时目录
            for i, desc in enumerate(func_info['input_descs']):
                file = request.files.get(f'input_{i}')
                if not file:
                    return f"Missing input: {desc}", 400
                
                # 生成安全文件名
                filename = f'input_{i}_{file.filename}'
                save_path = os.path.join(temp_dir, filename)
                file.save(save_path)
                input_paths.append(save_path)
            
            # 准备输出文件路径
            output_paths = []
            for i in range(len(func_info['output_list'])):
                # 生成输出文件路径
                filename = f'output_{i}.bin'  # 适当扩展名可以后期改进
                output_path = os.path.join(temp_dir, filename)
                output_paths.append(output_path)
            
            # 构建命令并执行（使用跨平台兼容的os.path.join）
            python_exec=''
            if platform.system() == 'Windows':
                python_exec = os.path.join(root_path, 'functions', function_id, 'env', 'python.exe')
            else :
                python_exec = os.path.join(root_path , 'functions' , function_id , 'env' , 'bin' , 'python3')
            
            script_path = os.path.join(root_path , 'functions', function_id, 'program', 'run.py')
            
            # 创建跨平台命令列表

            cmd_args = [python_exec, script_path, *input_paths, *output_paths]

            # 执行命令
            print('run command' , cmd_args)
            result = subprocess.run(cmd_args, capture_output=True, text=True)
            
            if result.returncode != 0:
                # 保留临时目录用于调试
                return f"Error: {result.stderr}\nDebugging data saved in {temp_dir}", 500
            
            # 如果只有一个输出文件，直接返回
            if len(output_paths) == 1:
                return send_file(output_paths[0], as_attachment=True)
            
            # 多个输出文件则打包为ZIP
            zip_filename = os.path.join(temp_dir, 'outputs.zip')
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for output_path in output_paths:
                    zipf.write(output_path, os.path.basename(output_path))
            
            # 清理临时目录（可选）
            shutil.rmtree(temp_dir)
            
            return send_file(zip_filename, as_attachment=True, download_name='outputs.zip')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Internal Error: {str(e)}", 500


#创建目录
if __name__ == '__main__':
    app.run(debug=True)
    