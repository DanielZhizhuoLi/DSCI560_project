import os
import openai
import json


openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("请设置环境变量 OPENAI_API_KEY")

def read_csv_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(file_text):
    prompt = f"""请根据下面的文本内容提取出以下字段：
- Date Stimulated
- Stimulated Formation
- Top (Ft)
- Bottom (Ft)
- Stimulation Stages
- Volume
- Volume Units
- Type Treatment
- Acid %
- Lbs Proppant
- Maximum Treatment Pressure (PSI)
- Maximum Treatment Rate (BBLS/Min)
- Details

请将这些字段及其对应的值整理成标准 JSON 格式。请只输出 JSON，不要包含其他文字。

文本如下：
------------------
{file_text}
------------------
"""
    return prompt

def get_json_from_chatgpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个数据提取助手，请严格按照要求返回 JSON 格式的数据。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    reply = response.choices[0].message.content.strip()
    return reply

def process_all_csv(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]
    if not csv_files:
        print("没有找到 CSV 文件。")
        return
    for csv_file in csv_files:
        input_path = os.path.join(input_dir, csv_file)
        print(f"正在处理文件：{input_path}")
        file_text = read_csv_file(input_path)
        prompt = build_prompt(file_text)
        json_reply = get_json_from_chatgpt(prompt)
        try:
            parsed = json.loads(json_reply)
            output_filename = os.path.splitext(csv_file)[0] + ".json"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
            print(f"已保存为：{output_path}")
        except json.JSONDecodeError as e:
            print(f"解析 JSON 失败：{e}")
            print("原始回复：", json_reply)

def main():
    input_dir = "../data/csv"   # CSV 文件所在目录
    output_dir = "../data/json_output"   # JSON 输出目录
    process_all_csv(input_dir, output_dir)

if __name__ == "__main__":
    main()
