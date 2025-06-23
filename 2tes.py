from flask import Flask, render_template, Response
import requests
import csv
import io

app = Flask(__name__)

API_URL = "https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/457/th/1,2/key/79452e4c302f8921ad36cd2bf55f0630/"

COLUMNS = [
    "status",
    "data-availability",
    "last_update",
    "subject",
    "var",
    "turvar",
    "labelvervar",
    "vervar",
    "tahun",
    "turtahun",
    "datacontent",
    "related"
]

@app.route('/')
def index():
    response = requests.get(API_URL)
    data = response.json()
    # Jika struktur data berupa dict di dalam 'data', ubah menjadi list
    rows = data.get('data', [])
    if isinstance(rows, dict):
        rows = [rows]
    return render_template('index.html', columns=COLUMNS, rows=rows, data=data)

@app.route('/download-csv')
def download_csv():
    response = requests.get(API_URL)
    data = response.json()
    rows = data.get('data', [])
    if isinstance(rows, dict):
        rows = [rows]
    if not rows:
        return "Tidak ada data untuk di-export."
    proxy = io.StringIO()
    writer = csv.DictWriter(proxy, fieldnames=COLUMNS)
    writer.writeheader()
    for row in rows:
        # Pastikan hanya field di COLUMNS yang diambil (handle jika field tidak ada)
        filtered_row = {col: row.get(col, "") for col in COLUMNS}
        writer.writerow(filtered_row)
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    mem.seek(0)
    proxy.close()
    return Response(
        mem,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=data_bps.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)
