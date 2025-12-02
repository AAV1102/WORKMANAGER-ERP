from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from modules.db_utils import get_db_connection

asset_profile_bp = Blueprint(
    "asset_profile", __name__, template_folder="../templates"
)


@asset_profile_bp.route("/asset/individual/<int:item_id>")
def profile_individual(item_id):
    """
    Muestra la página de perfil con todos los detalles de un equipo individual.
    """
    conn = get_db_connection()
    try:
        # Seleccionamos todas las columnas para obtener el perfil completo
        equipo = conn.execute(
            "SELECT * FROM equipos_individuales WHERE id = ?", (item_id,)
        ).fetchone()
    finally:
        conn.close()

    if equipo is None:
        # Si no se encuentra el equipo, muestra un error 404
        abort(404, description=f"Equipo con ID {item_id} no encontrado.")

    return render_template(
        "asset_profile/profile_individual.html",
        equipo=equipo,
        titulo=f"Perfil del Activo: {equipo['marca']} {equipo['modelo']} (ID: {equipo['id']})",
    )


@asset_profile_bp.route("/asset/individual/<int:item_id>/edit", methods=["GET", "POST"])
def edit_individual(item_id):
    """
    Muestra un formulario para editar un equipo y procesa la actualización.
    """
    conn = get_db_connection()
    equipo = conn.execute(
        "SELECT * FROM equipos_individuales WHERE id = ?", (item_id,)
    ).fetchone()

    if equipo is None:
        conn.close()
        abort(404, description=f"Equipo con ID {item_id} no encontrado.")

    if request.method == "POST":
        # Obtener todos los campos del formulario
        serial = request.form.get("serial", "").strip()
        marca = request.form.get("marca", "").strip()

        # --- Validación de campos obligatorios ---
        if not serial or not marca:
            flash("Los campos 'Serial' y 'Marca' son obligatorios.", "danger")
            # Volver a renderizar el formulario con los datos que el usuario ya había ingresado
            return render_template(
                "asset_profile/edit_individual.html",
                equipo=request.form,
                titulo=f"Editando Activo (ID: {item_id})",
            )

        updated_fields = {key: request.form.get(key) for key in equipo.keys()}

        # Construir la consulta de actualización dinámicamente
        set_clause = ", ".join([f"{key} = ?" for key in updated_fields.keys() if key != 'id'])
        values = list(updated_fields.values())
        # Mover el ID al final para el WHERE
        values.remove(updated_fields['id'])
        values.append(item_id)

        query = f"UPDATE equipos_individuales SET {set_clause} WHERE id = ?"

        # --- Lógica de Notificación ---
        estado_anterior = equipo['estado']
        estado_nuevo = updated_fields.get('estado')
        if estado_anterior != estado_nuevo:
            try:
                # Asumimos que el admin (user_id=1) recibe las notificaciones
                admin_user_id = 1 
                mensaje = f"El estado del equipo #{item_id} ({updated_fields.get('marca')} {updated_fields.get('modelo')}) cambió de '{estado_anterior}' a '{estado_nuevo}'."
                url_notificacion = url_for('asset_profile.profile_individual', item_id=item_id, _external=True)
                conn.execute("INSERT INTO notificaciones (user_id, message, url) VALUES (?, ?, ?)", (admin_user_id, mensaje, url_notificacion))
            except Exception as e:
                # Si la notificación falla, no detenemos la actualización del equipo
                print(f"ADVERTENCIA: No se pudo crear la notificación. Error: {e}")

        try:
            conn.execute(query, tuple(values))
            conn.commit()
            flash("Equipo actualizado correctamente.", "success")
            return redirect(url_for("asset_profile.profile_individual", item_id=item_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error al actualizar el equipo: {e}", "danger")
        finally:
            conn.close()

    # Para el método GET, simplemente cerramos la conexión después de obtener los datos
    conn.close()
    return render_template(
        "asset_profile/edit_individual.html",
        equipo=equipo,
        titulo=f"Editando Activo: {equipo['marca']} {equipo['modelo']} (ID: {equipo['id']})",
    )