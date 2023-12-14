import os

from flask import Flask, render_template, request, jsonify

from utils import auto_get_solc_version, run_command

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'  # 配置上传文件目录


# 加载主界面
@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    data = {
        'msg': "用户名或密码错误！",
        'success': False
    }
    if request.method == 'POST':
        if request.form.get('username') == "admin" \
                and request.form.get('password') == "admin":
            data['msg'] = '登录成功！'
            data['success'] = True

    return jsonify(data)


@app.route('/success-page')
def jump_to_index_page():
    return render_template('check.html')


@app.route('/upload_file_path', methods=['POST', 'GET'])
def upload_file():
    try:
        global current_filename
        # 检查是否有文件被上传
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        current_filename = file.filename
        file_content = file.read()
        file_path = os.getcwd() + "/upload/" + file.filename
        with open(file_path, 'wb') as uploaded_file:
            uploaded_file.write(file_content)
        response_data = {
            'fileContent': file_content.decode('utf-8'),
            'versionNumber': auto_get_solc_version(file_path)
        }

        return response_data

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/detect_bugs', methods=['GET'])
def detection_bugs():
    global current_filename

    print("file_path:" + current_filename)
    detection_file_path = "/home/long/longhe/match_3/mytool/web/upload/" + current_filename
    cmd = "python3 /home/long/longhe/match_3/mytool/mytool.py -s {}".format(detection_file_path)
    # 切换版本号
    # change_solc_version(version)
    result = run_command(cmd)

    return jsonify({'result': result})


def find_files(folder_path, extension):
    result_files = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(extension):
                result_files.append(os.path.join(root, file))

    return result_files


@app.route('/batch_detection', methods=['GET'])
def batch_detection():
    data = {
        'msg': "批量检测失败",
        'success': False
    }

    dir_path = "/home/long/longhe/match_3/contracts"
    target_extension = ".sol"

    f = open("/home/long/longhe/match_3/contracts/res.txt", 'a')

    found_files = find_files(dir_path, target_extension)

    if found_files:
        for file_path in found_files:
            cmd = "python3 /home/long/longhe/match_3/mytool/mytool.py -s {}".format(file_path)
            f.write(run_command(cmd))
            f.write("\n=================================================")
        data = {
            'msg': "批量检测完成！",
            'success': True
        }
    else:
        print(f"No files with extension {target_extension} found.")
    f.close()

    return data


if __name__ == '__main__':
    app.run(debug=True)
