function switchTab(tabId) {
    document.getElementById('tab-calc').classList.add('hidden');
    document.getElementById('tab-image').classList.add('hidden');
    document.getElementById('btn-calc').classList.remove('active');
    document.getElementById('btn-image').classList.remove('active');

    document.getElementById('tab-' + tabId).classList.remove('hidden');
    document.getElementById('btn-' + tabId).classList.add('active');
}

async function calcPVD() {
    document.getElementById('calc-result').innerText = "Обчислення...";
    const payload = {
        p1: document.getElementById('p1').value,
        p2: document.getElementById('p2').value,
        char: document.getElementById('char').value
    };
    try {
        const res = await fetch('/api/calc', {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        document.getElementById('calc-result').innerText = data.result || data.error;
    } catch (e) {
        document.getElementById('calc-result').innerText = "Помилка з'єднання з сервером.";
    }
}

async function hideData() {
    const file = document.getElementById('imageFile').files[0];
    const msg = document.getElementById('secretMsg').value;
    if (!file || !msg) return alert("[ПОМИЛКА] Оберіть файл та введіть повідомлення!");

    const formData = new FormData();
    formData.append('image', file);
    formData.append('message', msg);

    const res = await fetch('/api/hide', { method: 'POST', body: formData });
    if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "stego_payload.png";
        a.click();
    } else {
        const data = await res.json();
        alert("[ПОМИЛКА] " + data.error);
    }
}

async function extractData() {
    const file = document.getElementById('imageFile').files[0];
    if (!file) return alert("[ПОМИЛКА] Оберіть файл!");

    const formData = new FormData();
    formData.append('image', file);

    const res = await fetch('/api/extract', { method: 'POST', body: formData });
    const data = await res.json();
    if (res.ok) {
        document.getElementById('secretMsg').value = data.message;
    } else {
        alert("[ПОМИЛКА] " + data.error);
    }
}