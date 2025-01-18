from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import piexif
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Лимит 16 MB

def copy_exif_and_quality(source_image_path, target_image_path):
    """
    Копирует EXIF-данные и параметры качества из исходного изображения в целевое.
    :param source_image_path: Путь к исходному изображению.
    :param target_image_path: Путь к целевому изображению.
    """
    try:
        # Открываем исходное изображение
        source_image = Image.open(source_image_path)

        # Получаем EXIF-данные
        exif_data = piexif.load(source_image.info.get("exif", b""))

        # Открываем целевое изображение
        target_image = Image.open(target_image_path)

        # Сохраняем целевое изображение с EXIF-данными и качеством исходного
        target_image.save(target_image_path, exif=piexif.dump(exif_data), quality=100)
    except Exception as e:
        raise Exception(f"Ошибка при копировании EXIF-данных: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    download_link = None

    if request.method == 'POST':
        if 'source_image' not in request.files or 'target_image' not in request.files:
            message = "Ошибка: файлы не загружены."
            return render_template('index.html', message=message, download_link=download_link)

        source_image = request.files['source_image']
        target_image = request.files['target_image']

        if source_image.filename == '' or target_image.filename == '':
            message = "Ошибка: файлы не выбраны."
            return render_template('index.html', message=message, download_link=download_link)

        # Очистка имен файлов
        source_filename = secure_filename(source_image.filename)
        target_filename = secure_filename(target_image.filename)

        source_path = os.path.join(app.config['UPLOAD_FOLDER'], source_filename)
        target_path = os.path.join(app.config['UPLOAD_FOLDER'], target_filename)

        try:
            # Сохраняем загруженные файлы
            source_image.save(source_path)
            target_image.save(target_path)

            # Копируем EXIF-данные и параметры качества
            copy_exif_and_quality(source_path, target_path)

            message = "Успешно!"
            download_link = target_filename
        except Exception as e:
            message = f"Ошибка: {str(e)}"
            if os.path.exists(source_path):
                os.remove(source_path)
            if os.path.exists(target_path):
                os.remove(target_path)

    return render_template('index.html', message=message, download_link=download_link)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    # Удаляем файл после отправки
    response.call_on_close(lambda: os.remove(file_path))
    return response

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000)