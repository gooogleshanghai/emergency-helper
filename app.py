from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import json
from openai import OpenAI
import time
import threading

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# Deepseek API 配置
client = OpenAI(
   api_key="sk-c0bb1adddd9d44fca046444bce0c03f0",  # 替换为你的 API 密钥
   base_url="https://api.deepseek.com",
)

system_prompt = """
请按以下结构全面分析紧急报警信息, 20秒内json返回，注意不要有多层对象结构。
1. 事件类型：（火灾/医疗急救/交通事故/犯罪事件/自然灾害/其他）
2. 位置信息：
3. 伤亡人数：
4. 其他信息：
5. 信息获取问题设计（按优先级排序）：
  需设计3个问题，作为接线员下一步提问的参考，照顾用户情绪，说话像人类
6. 当前报警人情绪，如何应对：
剩下的按需要返回，不用全部返回
1. 医疗机构：
  - 最近的一家医院/诊所（一行返回，一定要是真实的信息包括名字、地址、距离、急诊电话、具体通知科室。）
2、急救医疗指导（针对具体事件类型）
3、-最近的消防站/警察局（一行返回，一定要是真实的信息包括名字、地址、距离、急诊电话、推荐派遣人数。）
"""

response_cache = {}

def fetch_response(user_prompt_part):
   print(user_prompt_part)
   if user_prompt_part in response_cache:
       print("从缓存获取响应")
       return response_cache[user_prompt_part]

   messages = [{"role": "system", "content": system_prompt},
               {"role": "user", "content": user_prompt_part}]

   response_data = {"timeout": True}  # 默认超时

   def api_call():
       nonlocal response_data
       try:
           response = client.chat.completions.create(
               model="deepseek-chat",
               messages=messages,
               response_format={'type': 'json_object'},
               timeout=100000
           )
           response_data = json.loads(response.choices[0].message.content)
       except Exception as e:
           print(f"API调用出错: {e}")
           response_data = {"error": str(e)}  # 记录错误信息

   # 创建并启动线程
   thread = threading.Thread(target=api_call)
   thread.start()

   thread.join(timeout=1000000)

   response_cache[user_prompt_part] = response_data  # 缓存响应
   print(response_data)
   if response_data!= {"timeout": True}:
       return response_data

@app.route('/process_text', methods=['POST'])
def process_text():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        # 调用 Deepseek API
        response_data = fetch_response(text)
        print("返回的JSON数据：", json.dumps(response_data, indent=2, ensure_ascii=False))

        return jsonify(response_data)

    except Exception as e:
        print(f"Error processing text: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # 确保端口与前端一致
@app.route('/')
def process():
    return render_template('index.html')