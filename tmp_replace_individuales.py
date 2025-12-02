from pathlib import Path
path = Path('templates/inventarios.html')
text = path.read_text()
start_marker = "            <!-- Equipos Individuales Tab -->"
end_marker = "            <!-- Equipos Asignados Tab -->"
start = text.find(start_marker)
end = text.find(end_marker)
if start == -1 or end == -1:
    raise SystemExit('individuales markers not found')
block = """            <!-- Equipos Individuales Tab -->
            <div class=\"tab-pane fade\" id=\"individuales\" role=\"tabpanel\">
                <div class=\"card mb-3\">
                    <div class=\"card-body\">
                        <h6><i class=\"fas fa-search\"></i> B&uacute;squeda en Equipos Individuales</h6>
                        <div class=\"row g-3\">
                            <div class=\"col-md-3\">
                                <input type=\"text\" class=\"form-control\" id=\"individualSearchId\" placeholder=\"Buscar por ID\">
                            </div>
                            <div class=\"col-md-3\">
                                <input type=\"text\" class=\"form-control\" id=\"individualSearchCodigo\" placeholder=\"C&oacute;digo Individual\">
                            </div>
                            <div class=\"col-md-3\">
                                <input type=\"text\" class=\"form-control\" id=\"individualSearchAnterior\" placeholder=\"Usuario anterior\">
                            </div>
                            <div class=\"col-md-3\">
                                <input type=\"text\" class=\"form-control\" id=\"individualSearchActual\" placeholder=\"Usuario actual\">
                            </div>
                        </div>
                        <div class=\"row g-3 mt-2\">
                            <div class=\"col-md-3\">
                                <select id=\"individualTipoFilter\" class=\"form-select\">
                                    <option value=\"\">Todos los tipos</option>
                                    <option value=\"cpu\">CPU</option>
                                    <option value=\"portatil\">Port&aacute;til</option>
                                    <option value=\"monitor\">Monitor</option>
                                    <option value=\"impresora\">Impresora</option>
                                    <option value=\"switch\">Switch</option>
                                    <option value=\"router\">Router</option>
                                </select>
                            </div>
                            <div class=\"col-md-3\">
                                <select id=\"individualEstadoFilter\" class=\"form-select\">
                                    <option value=\"\">Todos los estados</option>
                                    <option value=\"disponible\">Disponible</option>
                                    <option value=\"asignado\">Asignado</option>
                                    <option value=\"mantenimiento\">Mantenimiento</option>
                                    <option value=\"baja\">Dado de baja</option>
                                </select>
                            </div>
                            <div class=\"col-md-6 text-end\">
                                <button class=\"btn btn-primary me-2\" onclick=\"buscarEquipos()\"><i class=\"fas fa-search\"></i> Buscar</button>
                                <button class=\"btn btn-secondary\" onclick=\"limpiarFiltros()\"><i class=\"fas fa-times\"></i> Limpiar</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class=\"mb-3\">
                    <a href=\"{{ url_for('inventarios.new_inventario_individual') }}\" class=\"btn btn-primary btn-custom\"><i class=\"fas fa-plus\"></i> Nuevo Equipo Individual</a>
                    <button class=\"btn btn-success btn-custom\" onclick=\"exportToExcel('individuales')\"><i class=\"fas fa-file-excel\"></i> Exportar Excel</button>
                    <button class=\"btn btn-danger btn-custom\" onclick=\"exportToPDF('individuales')\"><i class=\"fas fa-file-pdf\"></i> Exportar PDF</button>
                    <button class=\"btn btn-info btn-custom\" onclick=\"importData('individuales')\"><i class=\"fas fa-upload\"></i> Importar Datos</button>
                    <button class=\"btn btn-warning btn-custom\" onclick=\"generateBarcode()\"><i class=\"fas fa-barcode\"></i> Generar C&oacute;digo de Barras</button>
                    <button class=\"btn btn-secondary\" onclick=\"generateLifeSheet()\"><i class=\"fas fa-file-alt\"></i> Generar Hoja de Vida</button>
                    <button class=\"btn btn-danger btn-custom\" onclick=\"darDeBaja()\"><i class=\"fas fa-times-circle\"></i> Dar de Baja</button>
                    <button class=\"btn btn-warning btn-custom\" onclick=\"reasignarEquipo()\"><i class=\"fas fa-exchange-alt\"></i> Reasignar</button>
                    <button class=\"btn btn-dark\" onclick=\"seleccionarTodosIndividuales()\"><i class=\"fas fa-check-square\"></i> Seleccionar Todos</button>
                    <button class=\"btn btn-secondary\" onclick=\"seleccionarIndividual()\"><i class=\"fas fa-check\"></i> Seleccionar Individual</button>
                    <button class=\"btn btn-primary btn-custom\" onclick=\"seleccionarVarios()\"><i class=\"fas fa-check-double\"></i> Seleccionar Varios</button>
                </div>

                <div class=\"table-responsive\">
                    <table class=\"table table-striped\" id=\"individualesTable\">
                        <thead>
                            <tr>
                                <th><input type=\"checkbox\" id=\"selectAllIndividuales\" onclick=\"seleccionarTodosIndividuales()\"></th>
                                <th>ID</th>
                                <th>C&oacute;digo Individual</th>
                                <th>Usuario anterior</th>
                                <th>Usuario actual</th>
                                <th>Caracter&iacute;sticas</th>
                                <th>Componentes y monitores</th>
                                <th>Tecnolog&iacute;a</th>
                                <th>Estado</th>
                                <th>Observaciones</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody id=\"individualesTableBody\">
                            {% for item in equipos_individuales %}
                            <tr data-id=\"{{ item[0] }}\" data-codigo=\"{{ item[1] or '' }}\" data-serial=\"{{ item[6] or '' }}\" data-usuario-actual=\"{{ item[18] or '' }}\" data-usuario-anterior=\"{{ item[8] or '' }}\" data-tecnologia=\"{{ item[5] or '' }}\" data-estado=\"{{ item[17] or '' }}\">
                                <td><input type=\"checkbox\" class=\"individualesCheckbox\" value=\"{{ item[0] }}\"></td>
                                <td>{{ item[0] }}</td>
                                <td>
                                    <strong>{{ item[1] }}</strong><br>
                                    <small class=\"text-muted\">Serial: {{ item[6] if item[6] else 'N/D' }}</small>
                                </td>
                                <td>{{ item[8] if item[8] else 'Sin registro' }}</td>
                                <td>{{ item[18] if item[18] else 'No asignado' }}</td>
                                <td>
                                    <div><strong>{{ item[10] if item[10] else 'Marca N/D' }}</strong> {{ item[7] if item[7] else '' }}</div>
                                    <div>Procesador: {{ item[11] if item[11] else 'N/A' }}</div>
                                    <div>RAM: {{ item[12] if item[12] else 'N/A' }} / {{ item[13] if item[13] else 'N/A' }}</div>
                                    <div>Disco: {{ item[14] if item[14] else 'N/A' }} {{ item[15] if item[15] else '' }}</div>
                                </td>
                                <td>
                                    <div>Monitor: {{ item[22] if item[22] else 'N/A' }} {{ item[23] if item[23] else '' }}</div>
                                    <div>Serial: {{ item[24] if item[24] else 'N/A' }}</div>
                                    <div>Placa: {{ item[25] if item[25] else 'N/A' }}</div>
                                </td>
                                <td>{{ item[5] if item[5] else 'N/A' }}</td>
                                <td><span class=\"badge {{ 'bg-success' if item[17] == 'disponible' else 'bg-primary' if item[17] == 'asignado' else 'bg-warning' }}\">{{ item[17] }}</span></td>
                                <td>{{ item[28] if item[28] else 'Sin observaciones' }}</td>
                                <td>
                                    <button class=\"btn btn-sm btn-info\" onclick=\"viewDetails('individual', {{ item[0] }})\"><i class=\"fas fa-eye\"></i> Ver</button>
                                    <button class=\"btn btn-sm btn-success\" onclick=\"assignEquipment('individual', {{ item[0] }})\"><i class=\"fas fa-user-plus\"></i> Asignar</button>
                                    <button class=\"btn btn-sm btn-warning\" onclick=\"viewLifeSheet('individual', {{ item[0] }})\"><i class=\"fas fa-history\"></i> Hoja Vida</button>
                                    <a href=\"{{ url_for('inventarios.edit_inventario', tipo='individual', inventario_id=item[0]) }}\" class=\"btn btn-sm btn-secondary\"><i class=\"fas fa-edit\"></i> Editar</a>
                                    <form action=\"{{ url_for('inventarios.delete_inventario', inventario_id=item[0]) }}\" method=\"post\" style=\"display:inline;\">
                                        <button type=\"submit\" class=\"btn btn-sm btn-danger\" onclick=\"return confirm('Estas seguro?')\"><i class=\"fas fa-trash\"></i> Eliminar</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Equipos Asignados Tab -->
"""

updated = text[:start] + block + text[end:]
path.write_text(updated)
