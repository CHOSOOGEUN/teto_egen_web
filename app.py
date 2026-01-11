from flask import Flask, render_template, request, send_from_directory
import google.generativeai as genai
import os
import base64
import io
from PIL import Image

app = Flask(__name__)

# 1. 환경변수 설정
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("⚠️ 경고: GOOGLE_API_KEY 환경변수가 설정되지 않았습니다!")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# ★ 추가된 부분: 구글 봇이 ads.txt를 찾을 때 보여주는 길
# ==========================================
@app.route('/ads.txt')
def ads_txt():
    return send_from_directory(app.root_path, 'ads.txt')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return "파일이 없습니다."
            
            file = request.files['file']
            if file.filename == '':
                return "파일을 선택해주세요."

            if file:
                image = Image.open(file.stream)
                
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_url = f"data:image/jpeg;base64,{img_str}"

                prompt = """
                이 사람의 얼굴을 분석해서 'TETO(테토)' 성향과 'EGEN(에겐)' 성향 중 어디에 가까운지 퍼센트로 알려줘.
                TETO는 남성 호르몬(테스토스테론)이 높은 관상으로 직선적이고 턱선이 굵고 눈썹뼈가 발달하고 눈매가 깊은 특징이 있어.
                EGEN은 여성 호르몬(에스트로겐)이 높은 관상으로 곡선적이고 피부가 부드럽고 눈이 크고 입술이 도톰한 특징이 있어.
                
                반드시 아래 JSON 형식으로만 답해줘. 다른 말은 하지 마.
                {
                    "teto_percent": 70,
                    "egen_percent": 30,
                    "type_name": "거친 야생의 늑대 테토",
                    "celebrity": "박보검",
                    "description": "당신의 얼굴은 전체적으로 선이 굵고...",
                    "parts_analysis": [
                        {"part": "눈", "teto": 80, "egen": 20, "desc": "눈매가 깊고..."},
                        {"part": "코", "teto": 60, "egen": 40, "desc": "코가 높고..."},
                        {"part": "턱선/얼굴형", "teto": 90, "egen": 10, "desc": "턱선이 날렵하고..."},
                        {"part": "분위기", "teto": 70, "egen": 30, "desc": "전체적으로 차가운..."}
                    ]
                }
                """
                
                import json
                response = model.generate_content([prompt, image])
                
                text = response.text.replace("```json", "").replace("```", "")
                result = json.loads(text)
                
                return render_template('result.html', result=result, image_url=image_url)

        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"

    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)