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

model = genai.GenerativeModel('gemini-flash-latest')

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
                image.thumbnail((800, 800))  # 사진 크기를 최대 800px로 줄임 (화질은 충분함)
                image = image.convert('RGB') # PNG 파일 등 호환성 문제 해결
                
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG", quality=80) # 용량도 80%로 살짝 압축
                
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_url = f"data:image/jpeg;base64,{img_str}"

                prompt = """
                이 사람의 얼굴과 분위기를 분석해서 다음 6가지 밴드 포지션 중 어디에 가장 잘 어울리는지 관상을 분석해줘.
                포지션: 보컬(Vocal), 리드기타(Lead Guitar), 리듬기타(Rhythm Guitar), 베이스(Bass), 드럼(Drum), 키보드(Keyboard)
                
                각 포지션의 전형적인 관상 및 분위기 특징:
                - 보컬: 시선을 끄는 화려함과 카리스마, 감수성이 풍부해 보이는 눈빛.
                - 리드기타: 날렵하고 예민한 인상, 테크니컬하고 독보적인 분위기.
                - 리듬기타: 안정감 있고 다정다감한 인상, 묵묵히 받쳐줄 것 같은 부드러움과 듬직함.
                - 베이스: 무심하고 나른한 인상, 차분하고 미스터리한 매력.
                - 드럼: 에너지가 넘치고 호쾌한 인상, 장난기 많고 활동적인 분위기.
                - 키보드: 지적이고 섬세한 인상, 깔끔하고 이지적인 분위기.
                
                각 포지션과의 싱크로율(얼마나 잘 어울리는지)을 0~100 사이의 점수(퍼센트)로 평가해줘. 가장 점수가 높은 포지션을 top_position으로 설정해.
                그리고 'celebrity' 항목에는 아이돌이 아닌, 국내외 실제 유명 밴드 멤버 중에서 가장 분위기가 비슷한 사람을 매칭해줘. (예: 잔나비 최정훈, 데이식스 영케이, 콜드플레이 크리스 마틴 등)
                
                반드시 아래 JSON 형식으로만 답해줘. 마크다운 기호 없이 순수 JSON 문자열만 출력해.
                {
                    "top_position": "베이스",
                    "scores": {
                        "vocal": 15,
                        "lead_guitar": 10,
                        "rhythm_guitar": 20,
                        "bass": 85,
                        "drum": 10,
                        "keyboard": 30
                    },
                    "type_name": "무심한 듯 매력적인 베이시스트",
                    "celebrity": "이정신(씨엔블루)",
                    "description": "당신의 얼굴은 전체적으로 묵묵하지만 단단한 인상을 줍니다...",
                    "parts_analysis": [
                        {"part": "눈", "position": "베이스", "desc": "깊고 차분한 눈매가 특유의 나른함을..."},
                        {"part": "코", "position": "드럼", "desc": "둥글고 친근한 코끝이..."},
                        {"part": "입매", "position": "보컬", "desc": "시원한 입꼬리가..."},
                        {"part": "분위기", "position": "베이스", "desc": "전체적으로 차분하고 미스터리한..."}
                    ]
                }
                """
                
                import json
                response = model.generate_content([prompt, image])
                
                text = response.text.strip().replace("```json", "").replace("```", "")
                result = json.loads(text)
                
                return render_template('result.html', result=result, image_url=image_url)

        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"

    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)