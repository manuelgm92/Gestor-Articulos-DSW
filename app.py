
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
import psycopg2, os, bcrypt, psycopg2.errors
from dotenv import load_dotenv
from wtforms import Form, StringField, PasswordField 
from wtforms.validators import InputRequired, Regexp, Length, EqualTo
from datetime import timedelta
from functools import wraps

load_dotenv()

def login_required(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if "usuario" not in session:
            flash("Debe iniciar sesión para acceder.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorada

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=1)

def conectar():
    conexion = psycopg2.connect(
        host=os.getenv("host"), #'173.212.252.164',
        port=os.getenv("port"), #5432,
        dbname=os.getenv("database"), #"bd_profesor",
        user=os.getenv("user"), #"profesor",
        password=os.getenv("password") #"12345678"
    )

    return conexion


# ----------------------------------
# Página inicial
# ----------------------------------

@app.route("/")
def inicio():
    return redirect(url_for("login"))


# ----------------------------------
# Login
# ----------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")
        
        formulario_login = FormularioLogin(request.form)
        
        if not formulario_login.validate():
            for campo, errores in formulario_login.errors.items():
                for error in errores:
                    flash(error)
            return redirect(url_for("login"))
                
        conexion = conectar()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("""
                                SELECT password FROM usuarios WHERE nombre_usuario = %s
                                """, (usuario,))
                result = cursor.fetchone()
                
        finally:
            conexion.close()
        
        if result is None:
            flash("Usuario o contraseña incorrectos")
            return redirect(url_for("login"))
        
        password_hash_db = result[0]
        
        password_bytes = password.encode("utf-8")
        hash_bd_bytes = password_hash_db.encode("utf-8")
        
        if bcrypt.checkpw(password_bytes, hash_bd_bytes):
            session.clear()
            session.permanent = True
            session["usuario"] = usuario
            flash("Ha iniciado sesión correctamente.")
        else:
            flash("Usuario o contraseña incorrectos")
            return redirect(url_for("login"))
        return redirect(url_for("listar_articulos"))

    return render_template("login.html")


# ----------------------------------
# Registro de usuarios
# ----------------------------------

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":
        
        formulario_registro = FormularioRegistro(request.form)

        if not formulario_registro.validate():
            for campo, errores in formulario_registro.errors.items():
               for error in errores:
                   flash(error) 
            return redirect(url_for("registro"))
        
        usuario = request.form.get("usuario")
        password = request.form.get("password")
        
        #Convertir password a bytes
        password_bytes = password.encode("utf-8")
        #general salt y aplicar hash
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        #decodificar
        password_decode = password_hash.decode("utf-8")

        params = (usuario, password_decode)
        conexion = conectar()

        try:
            with conexion.cursor() as cursor:
                cursor.execute("""
                               INSERT INTO usuarios 
                               (nombre_usuario, password)
                               VALUES (%s, %s)
                               """,
                               params
                )
                
                conexion.commit()
        
        except psycopg2.errors.UniqueViolation:
            conexion.rollback()
            flash("Ese nombre de usuario ya existe.")
            return redirect(url_for("registro"))
        
        except Exception as e:
            print("Error: ", e)
            conexion.rollback()
            raise
                
        finally:
            conexion.close()

        flash("Usuario registrado correctamente.")
        return redirect(url_for("login"))

    return render_template("registro.html")

# ----------------------------------
# Listado de artículos
# ----------------------------------

@app.route("/articulos")
@login_required
def listar_articulos():

    conexion = conectar()

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id_articulo,
                       nombre_comercial,
                       descripcion,
                       precio_unitario,
                       stock
                FROM articulos
                ORDER BY id_articulo
            """)

            articulos = cursor.fetchall()


    finally:
        conexion.close()

    return render_template("articulos.html", articulos=articulos
    )


# ----------------------------------
# Insertar artículo
# ----------------------------------

@app.route("/articulos/nuevo", methods=["GET", "POST"])
@login_required
def insertar_articulo():

    if request.method == "POST":

        nombre = request.form.get("nombre_comercial")
        descripcion = request.form.get("descripcion")
        precio = request.form.get("precio_unitario")
        stock = request.form.get("stock")

        
        conexion = conectar()

        try:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO articulos
                    (nombre_comercial, descripcion,
                     precio_unitario, stock)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, descripcion, precio, stock))

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        finally:
            conexion.close()

        return redirect(url_for("listar_articulos"))

    return render_template(
        "formulario_articulo.html",
        articulo=None
    )


# ----------------------------------
# Editar artículo
# ----------------------------------

@app.route("/articulos/editar/<int:id_articulo>",methods=["GET", "POST"])
@login_required
def editar_articulo(id_articulo):

    conexion = conectar()

    try:
        with conexion.cursor() as cursor:

            if request.method == "POST":

                nombre = request.form.get("nombre_comercial")
                descripcion = request.form.get("descripcion")
                precio = request.form.get("precio_unitario")
                stock = request.form.get("stock")

                
                cursor.execute("""
                    UPDATE articulos
                    SET nombre_comercial = %s,
                        descripcion = %s,
                        precio_unitario = %s,
                        stock = %s
                    WHERE id_articulo = %s
                """, (
                    nombre, descripcion,
                    precio, stock, id_articulo
                ))

                conexion.commit()

                return redirect(
                    url_for("listar_articulos")
                )

            cursor.execute("""
                SELECT *
                FROM articulos
                WHERE id_articulo = %s
            """, (id_articulo,))

            articulo = cursor.fetchone()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()

    if articulo is None:
        return "Artículo no encontrado"

    return render_template("formulario_articulo.html", articulo=articulo)


# ----------------------------------
# Eliminar artículo
# ----------------------------------

@app.route("/articulos/eliminar/<int:id_articulo>", methods=["POST"])
@login_required
def eliminar_articulo(id_articulo):

    conexion = conectar()

    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                DELETE FROM articulos
                WHERE id_articulo = %s
            """, (id_articulo,))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()

    return redirect(url_for("listar_articulos"))


# ----------------------------------
# Cerrar sesión
# ----------------------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("login"))


class FormularioRegistro(Form):
    usuario = StringField("usuario", validators=[
        InputRequired(message="El usuario es obligatorio"),
        Regexp(r'^[A-Za-z0-9_]{3,20}$', message="Solo se permiten letras, números y guiones bajos")
    ])
    password = PasswordField("password", validators=[
        InputRequired(message="La contraseña es obligatoria"),
        Length(min=8, message="La contraseña debe contener al menos 8 caracteres.")
    ])
    confirma_password = PasswordField("confirma_password", validators=[
        EqualTo("password", message="Las contraseñas no coinciden.")
    ])

class FormularioLogin(Form):
    usuario = StringField("usuario", validators=[
        InputRequired(message="El usuario es obligatorio"),
        Regexp(r'^[a-zA-Z0-9_]{3,20}$', message="Solo se permiten letras, números y guiones bajos")
    ])
    password=PasswordField("password", validators=[
        InputRequired(message="La contraseña es obligatoria")
    ])
    
    
if __name__ == "__main__":
    app.run(debug=True)
