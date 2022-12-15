from flask import Flask, jsonify, request
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import psycopg2
from datetime import timedelta
import mysql.connector
import requests
from requests.auth import HTTPBasicAuth


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'my-secret-key'
jwt = JWTManager(app)

# Set the database connection parameters
host = "satao.db.elephantsql.com"
database = "efrlebyq"
user = "efrlebyq"
password = "JfYLOPzBtdMXs_rd_l6ZdG2p3qUVICgR"

# Connect to the database
mydb = psycopg2.connect(host=host, database=database, user=user, password=password)

# mydb = mysql.connector.connect(
#     host = "localhost",
#     user = "root",
#     database = "car_sales",
#     )

# mydb_cursor = mydb.cursor()

#Authentication
#Register
@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if not username or not password:
            return ({"error": "Username and Password are required"}), 400
        
        if username == password:
            return ({"error": "Username and Password must be different"}), 400
        
        if len(username) < 4:
            return ({"error": "Username must be at least 4 characters"}), 400

        if len(password) < 6:
            return ({"error": "Password must be at least 8 characters"}), 400

        mydb_cursor = mydb.cursor()
        mydb_cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = mydb_cursor.fetchone()
        if user is not None:
            return ({"error": "Username already exists"}), 400

        hashed_password = generate_password_hash(password).decode('utf-8')

        mydb_cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        mydb.commit()
        return ({"message": "User created successfully"}), 200
    
    except Exception as e:
        return(e)

    finally:
        mydb_cursor.close()


#Login
@app.route('/login', methods=['POST'])
def login_user():
    try:
        mydb_cursor = mydb.cursor()
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return ({"message": "Please insert username and password!"}), 401
        
        user = mydb_cursor.execute("SELECT * FROM users WHERE username=%s", (auth.username,))
        user = mydb_cursor.fetchone()

        if user is not None:
            if check_password_hash(user[1], auth.password):
                access_token = create_access_token(identity=user[0], expires_delta=timedelta(minutes=30) )
                return jsonify(access_token=access_token), 200
        
        return ({"message": "Invalid username or password!"}), 401  
    except Exception as e:
        return(e)
    finally:
        mydb_cursor.close()

#CURD Operations
#Read
@app.route("/get_car_sales", methods=["GET"])
@jwt_required()
def read():
    try:
        mydb_cursor = mydb.cursor()
        mydb_cursor.execute("SELECT * FROM car_sales")
        data = mydb_cursor.fetchall()
        return jsonify(data), 200
    except Exception as e:
        return(e)
    finally:
        mydb_cursor.close()

@app.route("/add_car_sales", methods=["POST"])
@jwt_required()
def create():
    try:
        mydb_cursor = mydb.cursor()
        data = request.get_json()
        mydb_cursor.execute("INSERT INTO car_sales (manufacturer, model, sales_in_thousands, vehicle_type, price_in_thousands, engine_size, horsepower, wheelbase, width, length, fuel_capacity, fuel_efficiency) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (data['manufacturer'], data['model'], data['sales_in_thousands'], data['vehicle_type'], data['price_in_thousands'], data['engine_size'], data['horsepower'], data['wheelbase'], data['width'], data['length'], data['fuel_capacity'], data['fuel_efficiency']))
        mydb.commit()
        return jsonify({'car_sales': data}),200
    except Exception as e:
        return(e)
    finally:
        mydb_cursor.close()

#Update
@app.route("/update_car_sales", methods=["PUT"])
@jwt_required()
def update():
    try:
        mydb_cursor = mydb.cursor()
        data=request.get_json()
        mydb_cursor.execute("UPDATE car_sales SET manufacturer=%s, model=%s, sales_in_thousands=%s, vehicle_type=%s, price_in_thousands=%s, engine_size=%s, horsepower=%s, wheelbase=%s, width=%s, length=%s, fuel_capacity=%s, fuel_efficiency=%s WHERE model=%s", 
        (data['manufacturer'], data['model'], data['sales_in_thousands'], data['vehicle_type'], data['price_in_thousands'], data['engine_size'], data['horsepower'], data['wheelbase'], data['width'], data['length'], data['fuel_capacity'], data['fuel_efficiency'], data['changemodel']))
        mydb.commit()
        return jsonify({'car_sales': data}),200
    except Exception as e:
        return(e)
    finally:
        mydb_cursor.close()


#Delete
@app.route("/delete_car_sales", methods=["DELETE"])
@jwt_required()
def delete():
    try:
        mydb_cursor = mydb.cursor()
        data=request.get_json()
        mydb_cursor.execute("SELECT * FROM car_sales WHERE model=%s", (data['model'],))
        if mydb_cursor.fetchone() is None:
            return jsonify({"message": "Car not found"})
        mydb_cursor.execute("DELETE FROM car_sales WHERE model=%s", (data['model'],))
        mydb.commit()
        return jsonify({"message": "Car deleted successfully"})
    except Exception as e:
        return(e)
    finally:
        mydb_cursor.close()
    



#Core Services

#Access Calvin API
def get_bearer_token():
    response = requests.post('https://calvinfinancialconsult.azurewebsites.net/login',auth=HTTPBasicAuth('rayclementj', 'Test123'))
    jsonresponse = response.json()
    bearertoken = str(jsonresponse['access_token'])
    return bearertoken

def get_structure(url, id):
    link = url
    headers = {"Authorization": f'Bearer {get_bearer_token()}'}
    response = requests.get(link, headers=headers, json=id)
    jsonresponse = response.json()
    return jsonresponse


#Get Buying Power
@app.route("/buying_power", methods=["GET"])
@jwt_required()
def get_buying_power():
    try:
        # return buying_power()
        data=request.get_json()
        id = data['id']
        model = data['model']
        tenor = data['tenor']
        percent = data['percent']
        
        url = 'https://calvinfinancialconsult.azurewebsites.net/additional_spending'
        request_body = {
            'ID' : id
            }
        jsonresponse = get_structure(url, request_body)
        additionalspending = jsonresponse['total_pengeluaran_tambahan']
        harga_per_seribu = get_car_price_by_model(model)
        harga = harga_per_seribu[0] * 1000
        simulasi_kredit = get_kredit_per_bulan(model, tenor, int(percent))

        message = ''
        if additionalspending > simulasi_kredit:
            message={'message': 'You can buy this car with the given tenor :D', 'harga_mobil': harga, 'kredit_per_bulan': simulasi_kredit}
        else:
            new_tenor = 1
            while additionalspending < simulasi_kredit:
                new_tenor += 1
                simulasi_kredit = get_kredit_per_bulan(model, new_tenor, int(percent))
            message={'message': 'Sorry, you cannot buy this car with the given tenor :( try to increase the tenor', 'recommended_tenor_years': new_tenor}
        return jsonify(message)
    except Exception as e:
        return(e)

@app.route("/simulasi_kredit", methods=["GET"])
def get_simulasi_kredit():
    try:
        data=request.get_json()
        model = data['model']
        tenor = data['tenor']
        bunga = data['bunga']
        kredit_per_bulan = get_kredit_per_bulan(model, tenor, int(bunga))
        jumlah_bulan = int(tenor) * 12
        return jsonify(kredit_per_bulan=kredit_per_bulan, jumlah_bulan = jumlah_bulan)
    except Exception as e:
        return(e)
    
def get_kredit_per_bulan(model, tenor, bunga):
    harga_per_seribu = get_car_price_by_model(model)
    harga = harga_per_seribu[0] * 1000
    kredit_per_bulan = harga / (12 * int(tenor)) + (bunga/12)*harga/100
    return kredit_per_bulan

def get_fuel_eff(model):
    mydb_cursor = mydb.cursor()
    mydb_cursor.execute("SELECT fuel_efficiency FROM car_sales WHERE model=%s", (model,))
    data = mydb_cursor.fetchone()
    mydb_cursor.close()
    return data

def get_car_price_by_model(model):
    mydb_cursor = mydb.cursor()
    mydb_cursor.execute("SELECT price_in_thousands FROM car_sales WHERE model=%s", (model,))
    data = mydb_cursor.fetchone()
    mydb_cursor.close()
    return data

def get_car_detail_by_spending(spending):
    mydb_cursor = mydb.cursor()
    mydb_cursor.execute("SELECT concat (manufacturer,' ', model) as nama_kendaraan, price_in_thousands * 1000 as harga FROM car_sales WHERE price_in_thousands*1000<=%s order by price_in_thousands", (spending,))
    data = mydb_cursor.fetchall()
    mydb_cursor.close()
    return data

def get_car_detail_by_fuel_eff(number):
    mydb_cursor = mydb.cursor()
    mydb_cursor.execute("SELECT concat (manufacturer,' ', model) as nama_kendaraan, price_in_thousands * 1000 as harga, fuel_efficiency FROM car_sales WHERE fuel_efficiency<=%s order by price_in_thousands", (number,))
    data = mydb_cursor.fetchall()
    mydb_cursor.close()
    return data

def get_car_manuf(model):
    mydb_cursor = mydb.cursor()
    mydb_cursor.execute("SELECT manufacturer FROM car_sales WHERE model=%s", (model,))
    data = mydb_cursor.fetchone()
    mydb_cursor.close()
    return data

def get_car_full_name(model):
    mydb_cursor = mydb.cursor()
    mydb_cursor.execute("SELECT concat (manufacturer,' ', model) FROM car_sales WHERE model=%s", (model,))
    data = mydb_cursor.fetchone()
    mydb_cursor.close()
    return data

#Get Car Spending Detail by Model
@app.route("/perkiraan_biaya", methods=["GET"])
@jwt_required()
def perkiraan_biaya():
    data = request.get_json()
    model = data['model']
    nama_kendaraan = get_car_full_name(model)
    harga_per_seribu = get_car_price_by_model(model)
    harga = harga_per_seribu[0] * 1000
    efBBM = get_fuel_eff(model)
    biaya_bbm_per_taun = (1 / efBBM[0]) * 1 * 20000
    return jsonify(nama_kendaraan = nama_kendaraan[0], harga=harga, biaya_bbm_per_taun=biaya_bbm_per_taun),200

#Get Car List by Spending
@app.route("/list_rekomendasi_mobil", methods=["GET"])
@jwt_required()
def rekomendasi_mobil():
    data = request.get_json()
    batas_harga = data['batas_harga']
    mobils = get_car_detail_by_spending(batas_harga)
    
    list_mobil = []
    for mobil in mobils:
        mobil_data = {}
        mobil_data['nama_kendaraan'] = mobil[0]
        mobil_data['harga_kendaraan'] = mobil[1]
        list_mobil.append(mobil_data)

    return jsonify(list_mobil),200

#Get Car List by Fuel Efficiency
@app.route("/list_rekomendasi_mobil_efisiensi_bbm", methods=["GET"])
@jwt_required()
def rekomendasi_mobil_efisiensi_bbm():
    data = request.get_json()
    min_efisiensi = data['min_efisiensi']
    mobils = get_car_detail_by_fuel_eff(min_efisiensi)
    
    list_mobil = []
    for mobil in mobils:
        mobil_data = {}
        mobil_data['nama_kendaraan'] = mobil[0]
        mobil_data['harga_kendaraan'] = mobil[1]
        mobil_data['efisiensi_bbm'] = mobil[2]
        list_mobil.append(mobil_data)

    return jsonify(list_mobil),200

if  __name__ == '__main__':  
    app.run(debug=True, host="0.0.0.0", port=5002)