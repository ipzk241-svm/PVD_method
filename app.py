import io
import math
from flask import Flask, request, jsonify, send_file, render_template
from PIL import Image

app = Flask(__name__)

INTERVALS = [(0, 7, 3), (8, 15, 3), (16, 31, 4), (32, 63, 5), (64, 127, 6), (128, 255, 7)]

def get_interval_info(d):
    for l, u, bits in INTERVALS:
        if l <= d <= u: return l, u, bits
    return 0, 7, 3

def text_to_bits(text):
    text += '\0' 
    return ''.join(f"{ord(c):08b}" for c in text)

def embed_pixel_pair(p1, p2, remaining_bits):
    d = abs(p2 - p1)
    l_k, u_k, n = get_interval_info(d)
    
    bits_to_embed = remaining_bits[:n].ljust(n, '0')
    b = int(bits_to_embed, 2)
    
    d_new = l_k + b
    m = d_new - d
    
    delta_p1, delta_p2 = math.floor(abs(m) / 2), math.ceil(abs(m) / 2)
    
    if m > 0:
        h1, h2 = (p1 - delta_p1, p2 + delta_p2) if p2 >= p1 else (p1 + delta_p1, p2 - delta_p2)
    elif m < 0:
        h1, h2 = (p1 + delta_p1, p2 - delta_p2) if p2 >= p1 else (p1 - delta_p1, p2 + delta_p2)
    else:
        h1, h2 = p1, p2
        
    if h1 < 0:
        p1_new, p2_new = 0, h2 + abs(h1)
    elif h1 > 255:
        p1_new, p2_new = 255, h2 - (h1 - 255)
    elif h2 < 0:
        p1_new, p2_new = h1 + abs(h2), 0
    elif h2 > 255:
        p1_new, p2_new = h1 - (h2 - 255), 255
    else:
        p1_new, p2_new = h1, h2
        
    p1_new, p2_new = max(0, min(255, p1_new)), max(0, min(255, p2_new))
    
    return {
        "p1_new": p1_new, "p2_new": p2_new,
        "d": d, "l_k": l_k, "u_k": u_k, "n": n,
        "b": b, "d_new": d_new
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calc', methods=['POST'])
def api_calc():
    data = request.json
    try:
        p1, p2, char = int(data['p1']), int(data['p2']), data['char'][:1]
        bin_char = f"{ord(char):08b}"
        
        res = embed_pixel_pair(p1, p2, bin_char)
        
        p1_new, p2_new = res["p1_new"], res["p2_new"]
        
        extracted_d = abs(p2_new - p1_new)
        ext_l_k, _, ext_n = get_interval_info(extracted_d)
        extracted_bits = f"{(extracted_d - ext_l_k):0{ext_n}b}"

        res_text = (
            f"Символ: '{char}' -> ASCII: {ord(char)} -> Бінарно: {bin_char}\n"
            f"1. Початкова різниця (d): |{p2} - {p1}| = {res['d']}\n"
            f"2. Інтервал: [{res['l_k']}, {res['u_k']}], бітів (n): {res['n']}\n"
            f"3. Нова різниця: {res['l_k']} + {res['b']} = {res['d_new']}\n"
            f"4. НОВІ ПІКСЕЛІ: P1 = {p1_new}, P2 = {p2_new}\n"
            f"Вилучені біти (перевірка): {extracted_bits}"
        )
        return jsonify({"result": res_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/hide', methods=['POST'])
def api_hide():
    file = request.files.get('image')
    msg = request.form.get('message')
    if not file or not msg: return jsonify({"error": "Missing data"}), 400
    
    try:
        img = Image.open(file).convert('L')
        pixels = img.load()
        width, height = img.size
        msg_bits = text_to_bits(msg)
        bit_idx, total_bits = 0, len(msg_bits)
        
        for y in range(height):
            for x in range(0, width - 1, 2):
                if bit_idx >= total_bits: break
                
                res = embed_pixel_pair(pixels[x, y], pixels[x+1, y], msg_bits[bit_idx:])
                
                pixels[x, y] = res["p1_new"]
                pixels[x+1, y] = res["p2_new"]
                bit_idx += res["n"]
                
            if bit_idx >= total_bits: break
            
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='stego.png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract', methods=['POST'])
def api_extract():
    file = request.files.get('image')
    if not file: return jsonify({"error": "Missing image"}), 400
    
    try:
        img = Image.open(file).convert('L')
        pixels = img.load()
        width, height = img.size
        extracted_bits = ""
        
        for y in range(height):
            for x in range(0, width - 1, 2):
                p1, p2 = pixels[x, y], pixels[x+1, y]
                l_k, _, n = get_interval_info(abs(p2 - p1))
                extracted_bits += f"{(abs(p2 - p1) - l_k):0{n}b}"
                
                if len(extracted_bits) >= 8 and len(extracted_bits) % 8 == 0:
                    chars = [chr(int(extracted_bits[i:i+8], 2)) for i in range(0, len(extracted_bits)-7, 8)]
                    if '\0' in chars:
                        return jsonify({"message": "".join(chars).split('\0')[0]})
        return jsonify({"message": "Повідомлення не знайдено."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)